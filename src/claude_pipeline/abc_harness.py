"""ABC harness driver.

Spawns each of three variants (A/B/C) against a list of issues at varying
tiers, captures metrics, and persists scores to SQLite.

Topology per issue:

    issue N
      ├── worktree A ── variant A: claude-pipeline run (v0.3 LangGraph)
      ├── worktree B ── variant B: claude --print + pipeline-0.3 skill
      └── worktree C ── variant C: claude --print + naive prompt

The three variants run **in parallel** per issue (ThreadPoolExecutor with
3 workers). Across issues, the harness is **sequential** — running multiple
issues simultaneously would have 9 Claude sessions live, blowing the
per-account concurrency budget and the VPS-side LLM load.

Worktree layout:

    {db_path_parent}/abc/{round}/issue-{N}/
        A/worktree/    + A/run.log
        B/worktree/    + B/run.log
        C/worktree/    + C/run.log

The harness does NOT delete worktrees after the run — the operator needs
to inspect them to verify the scorecard. Disk cleanup is a separate cron
job (not in scope).

Three rules:

1. The harness only **spawns** Claude. It does NOT itself read the model.
   Every Claude invocation goes through `claude.run_claude` so timeouts,
   env hygiene, and structured-JSON parsing are uniform.
2. Variant A is invoked via the pipeline's own CLI (subprocess), not by
   importing the graph in-process. This guarantees variant A runs the
   v0.3 pipeline as a user would invoke it — same subprocess boundary,
   same checkpoint DB layout, same exit codes.
3. Per-variant timeouts are hard. Default 1800s (30 min). A hung variant
   does not pin the harness — it gets killed, its row records the
   timeout in failure_categories, and the harness moves on.
"""

from __future__ import annotations

import concurrent.futures as cf
import datetime as _dt
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from claude_pipeline.abc_db import RunRow, init_db, insert_run
from claude_pipeline.abc_scoring import score_variant_run

log = logging.getLogger(__name__)


# Default timeout per variant invocation (wall clock). The operator can
# raise this for tier-3 work but every variant MUST be bounded — a hung
# subprocess does not get to pin the harness forever.
DEFAULT_VARIANT_TIMEOUT_S: int = 1800

# Variants this harness knows how to run.
VARIANTS: tuple[str, ...] = ("A", "B", "C")

# Pinned branch for variant A.  The v0.3 pipeline is on this branch.
# Variant A is "the v0.3 graph", so we explicitly check it out before
# invoking claude-pipeline. The harness itself lives on v0.4-abc-harness
# but variant A must be v0.3.
VARIANT_A_PIPELINE_BRANCH: str = "v0.3-context-and-reviewers"

# The pipeline-0.3 skill path. Variant B references it; the path is
# embedded into the prompt so the agent can read the skill body.
PIPELINE_03_SKILL_PATH: Path = (
    Path.home() / ".claude" / "skills" / "pipeline-0.3" / "SKILL.md"
)


# --------------------------------------------------------------------------- #
# Config types
# --------------------------------------------------------------------------- #


@dataclass
class IssueSpec:
    """One issue line in the round YAML."""

    number: int
    tier: int
    notes: str = ""


@dataclass
class RoundConfig:
    """Parsed YAML round config."""

    round_name: str
    repo: str
    issues: list[IssueSpec]
    variants: list[str]
    gate_folder: Path
    db_path: Path
    runs_root: Path  # parent dir for the per-issue worktrees
    variant_timeout_s: int = DEFAULT_VARIANT_TIMEOUT_S


def load_round_config(yaml_path: Path, round_name: str | None = None) -> RoundConfig:
    """Load and validate a round YAML file.

    The yaml's basename (minus .yaml/.yml) is the default round name; pass
    ``round_name`` to override (useful for re-running a config under a
    different label).
    """
    import yaml  # local import — PyYAML is an explicit dep of this module

    with open(yaml_path) as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(f"round config must be a YAML mapping, got: {type(raw)}")

    repo = raw.get("repo")
    if not repo:
        raise ValueError("round config missing 'repo'")

    issues_raw = raw.get("issues") or []
    if not issues_raw:
        raise ValueError("round config has no 'issues'")
    issues: list[IssueSpec] = []
    for entry in issues_raw:
        if not isinstance(entry, dict):
            raise ValueError(f"issue entry must be a mapping, got: {entry!r}")
        if "number" not in entry or "tier" not in entry:
            raise ValueError(f"issue entry missing 'number' or 'tier': {entry!r}")
        issues.append(
            IssueSpec(
                number=int(entry["number"]),
                tier=int(entry["tier"]),
                notes=str(entry.get("notes") or ""),
            )
        )

    variants = [v.upper() for v in (raw.get("variants") or list(VARIANTS))]
    for v in variants:
        if v not in VARIANTS:
            raise ValueError(f"unknown variant {v!r}; expected one of {VARIANTS}")

    gate_folder = Path(raw.get("gate_folder") or "")
    if not gate_folder.exists():
        raise ValueError(f"gate_folder does not exist: {gate_folder}")

    db_path = Path(raw.get("db_path") or "")
    if not db_path:
        raise ValueError("round config missing 'db_path'")

    # runs_root defaults to {db_path.parent}/abc/{round}/
    name = round_name or Path(yaml_path).stem
    runs_root = db_path.parent / "abc" / name

    variant_timeout = int(raw.get("variant_timeout_s") or DEFAULT_VARIANT_TIMEOUT_S)

    return RoundConfig(
        round_name=name,
        repo=repo,
        issues=issues,
        variants=variants,
        gate_folder=gate_folder,
        db_path=db_path,
        runs_root=runs_root,
        variant_timeout_s=variant_timeout,
    )


# --------------------------------------------------------------------------- #
# Issue fetching
# --------------------------------------------------------------------------- #


def fetch_issue_body(repo: str, issue_number: int) -> tuple[str, str]:
    """Fetch issue title + body via `gh`. Returns (title, body)."""
    proc = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", repo,
         "--json", "title,body,number,state"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue view failed: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    return (str(data.get("title") or ""), str(data.get("body") or ""))


# --------------------------------------------------------------------------- #
# Per-variant worktree setup
# --------------------------------------------------------------------------- #


def _make_worktree(repo: str, dest: Path, base_branch: str = "main") -> Path:
    """Clone the repo into ``dest`` (depth 50). Returns the worktree path.

    Idempotent: if ``dest`` already contains a git checkout, leaves it alone.
    """
    if (dest / ".git").exists():
        log.info("_make_worktree: reusing existing checkout at %s", dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{repo}.git"
    log.info("_make_worktree: cloning %s -> %s", url, dest)
    proc = subprocess.run(
        ["git", "clone", "--depth", "50", "--branch", base_branch, url, str(dest)],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed for {repo}: {proc.stderr.strip()}")
    return dest


def _checkout_branch(worktree: Path, branch: str) -> None:
    """Best-effort checkout of ``branch`` in ``worktree``. Tries remote ref."""
    # Fetch first so the branch is known.
    subprocess.run(
        ["git", "fetch", "origin", branch],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    proc = subprocess.run(
        ["git", "checkout", branch],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        # Try origin/<branch>
        subprocess.run(
            ["git", "checkout", "-b", branch, f"origin/{branch}"],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )


# --------------------------------------------------------------------------- #
# Variant runners
# --------------------------------------------------------------------------- #


@dataclass
class VariantResult:
    """What a variant runner returns to the harness loop."""

    variant: str
    issue_number: int
    tier: int
    started_at: str
    duration_s: float
    cost_usd: float | None
    log_path: Path
    worktree: Path
    crashed: bool = False
    crash_reason: str = ""
    extra: dict = field(default_factory=dict)


def _run_subprocess_to_log(
    args: list[str],
    *,
    cwd: Path,
    log_path: Path,
    timeout_s: int,
    env_extra: dict[str, str] | None = None,
    stdin_text: str | None = None,
) -> tuple[int, float, str]:
    """Run a subprocess streaming stdout+stderr to ``log_path``.

    Returns (returncode, duration_s, crash_reason). On timeout, returns
    (-1, duration, 'timeout after Ns'). The process is hard-killed on
    timeout (Popen.kill + wait). The combined stream is the harness's
    "raw log" for that variant.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.pop("ANTHROPIC_BASE_URL", None)  # mirror claude.run_claude hygiene
    if env_extra:
        env.update(env_extra)

    start = time.monotonic()
    with open(log_path, "w") as logfh:
        logfh.write(f"# command: {' '.join(args)}\n")
        logfh.write(f"# cwd: {cwd}\n")
        logfh.write(f"# timeout_s: {timeout_s}\n")
        logfh.write(f"# started: {_dt.datetime.utcnow().isoformat()}Z\n")
        logfh.write("# ---\n")
        logfh.flush()

        try:
            proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE if stdin_text else None,
                stdout=logfh,
                stderr=subprocess.STDOUT,
                cwd=str(cwd),
                env=env,
                text=True,
            )
        except FileNotFoundError as e:
            duration = time.monotonic() - start
            logfh.write(f"\n# FileNotFoundError: {e}\n")
            return (-2, duration, f"binary not found: {e}")

        if stdin_text and proc.stdin:
            try:
                proc.stdin.write(stdin_text)
                proc.stdin.close()
            except BrokenPipeError:
                pass

        try:
            rc = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            duration = time.monotonic() - start
            logfh.write(f"\n# TIMEOUT after {timeout_s}s — killed\n")
            return (-1, duration, f"timeout after {timeout_s}s")

    duration = time.monotonic() - start
    return (rc, duration, "")


def run_variant_a(
    cfg: RoundConfig,
    issue: IssueSpec,
    issue_root: Path,
) -> VariantResult:
    """Variant A: invoke claude-pipeline run on the v0.3 branch.

    Implementation note: claude-pipeline already creates its own worktree
    inside its runs/ dir. We don't need to pre-clone — we just call the
    CLI from a directory that has access to the same env. We DO need to
    make sure claude-pipeline runs against v0.3, so we set
    CLAUDE_PIPELINE_BRANCH (informational, the CLI itself takes --base).
    """
    started = _dt.datetime.utcnow().isoformat() + "Z"
    log_path = issue_root / "A" / "run.log"
    # claude-pipeline creates its own worktree under its runs/; we record
    # the issue_root/A/worktree as a placeholder symlink-target so the
    # scorer has something to inspect even if it's empty.
    placeholder_wt = issue_root / "A" / "worktree"
    placeholder_wt.mkdir(parents=True, exist_ok=True)

    args = [
        "claude-pipeline",
        "run",
        cfg.repo,
        str(issue.number),
        "--base",
        "main",
    ]
    # Variant A's "pipeline branch pin" is enforced by the operator's
    # checkout of this repo before running; we record it for the log.
    env_extra = {
        "CLAUDE_PIPELINE_VARIANT": "A",
        "CLAUDE_PIPELINE_TARGET_BRANCH": VARIANT_A_PIPELINE_BRANCH,
    }

    rc, duration, crash_reason = _run_subprocess_to_log(
        args,
        cwd=placeholder_wt,
        log_path=log_path,
        timeout_s=cfg.variant_timeout_s,
        env_extra=env_extra,
    )

    crashed = rc != 0
    if crashed and not crash_reason:
        crash_reason = f"exit {rc}"

    return VariantResult(
        variant="A",
        issue_number=issue.number,
        tier=issue.tier,
        started_at=started,
        duration_s=duration,
        cost_usd=None,  # variant A's cost lives across many claude --print calls; scorer can sum if needed
        log_path=log_path,
        worktree=placeholder_wt,
        crashed=crashed,
        crash_reason=crash_reason,
    )


def _variant_bc_prompt_b(repo: str, issue_number: int, issue_title: str, issue_body: str) -> str:
    """Variant B prompt: invoke the pipeline-0.3 skill on the issue."""
    return (
        f"You are running variant B of an A/B/C test. Use the pipeline-0.3 skill "
        f"at `{PIPELINE_03_SKILL_PATH}`. Read it, follow it phase-by-phase. "
        f"Do not skip phases. Do not collapse phases. Do not invent shortcuts.\n\n"
        f"REPO: {repo}\n"
        f"ISSUE: #{issue_number} — {issue_title}\n\n"
        f"ISSUE BODY:\n{issue_body}\n\n"
        f"End by passing the gate folder bar: walk "
        f"`/Users/syedhaider/Projects/claude-pipeline/gate/00_START.md` until "
        f"`12_PASS_HANDOFF`, then commit + push + open PR.\n"
    )


def _variant_bc_prompt_c(repo: str, issue_number: int, issue_title: str, issue_body: str) -> str:
    """Variant C prompt: naive single-call with only the gate-folder rule."""
    return (
        f"Solve this GitHub issue and open a PR. You MUST read "
        f"`/Users/syedhaider/Projects/claude-pipeline/gate/00_START.md` and pass "
        f"every gate before declaring done.\n\n"
        f"REPO: {repo}\n"
        f"ISSUE: #{issue_number} — {issue_title}\n\n"
        f"ISSUE BODY:\n{issue_body}\n"
    )


def _run_single_session_variant(
    cfg: RoundConfig,
    issue: IssueSpec,
    issue_root: Path,
    variant_letter: str,
    issue_title: str,
    issue_body: str,
) -> VariantResult:
    """Common path for variants B and C: clone, then invoke `claude --print`.

    The only difference between B and C is the prompt. Each runs as a
    single Claude session against the cloned worktree.
    """
    started = _dt.datetime.utcnow().isoformat() + "Z"
    log_path = issue_root / variant_letter / "run.log"
    worktree = issue_root / variant_letter / "worktree"

    try:
        _make_worktree(cfg.repo, worktree, base_branch="main")
        # Each variant gets its own feature branch so PRs don't collide.
        branch = f"abc/{cfg.round_name}/issue-{issue.number}-{variant_letter}"
        subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception as e:
        return VariantResult(
            variant=variant_letter,
            issue_number=issue.number,
            tier=issue.tier,
            started_at=started,
            duration_s=0.0,
            cost_usd=None,
            log_path=log_path,
            worktree=worktree,
            crashed=True,
            crash_reason=f"worktree setup failed: {e}",
        )

    if variant_letter == "B":
        prompt = _variant_bc_prompt_b(cfg.repo, issue.number, issue_title, issue_body)
    elif variant_letter == "C":
        prompt = _variant_bc_prompt_c(cfg.repo, issue.number, issue_title, issue_body)
    else:
        raise ValueError(f"unsupported variant for single-session runner: {variant_letter}")

    # Variants B and C run via `claude --print --output-format json`.  We
    # invoke the CLI ourselves (not run_claude) so we can stream the full
    # invocation into the variant's run.log for the scorer.
    args = [
        "claude",
        "--print",
        "--permission-mode", "bypassPermissions",
        "--output-format", "json",
        "--add-dir", str(cfg.gate_folder),
        "--add-dir", str(PIPELINE_03_SKILL_PATH.parent),
        "--add-dir",
        str(Path(__file__).resolve().parent.parent.parent / "prompts" / "metabuilder"),
    ]
    env_extra = {f"CLAUDE_PIPELINE_VARIANT": variant_letter}

    rc, duration, crash_reason = _run_subprocess_to_log(
        args,
        cwd=worktree,
        log_path=log_path,
        timeout_s=cfg.variant_timeout_s,
        env_extra=env_extra,
        stdin_text=prompt,
    )

    # Try to pull cost from the JSON envelope (the variant log contains
    # the full `claude --print --output-format json` stdout).
    cost: float | None = None
    try:
        txt = log_path.read_text(encoding="utf-8", errors="replace")
        # Find the first `{` after the header marker and try to parse.
        marker = "# ---\n"
        if marker in txt:
            body = txt.split(marker, 1)[1].strip()
            # claude --print json output is a single object on stdout
            for line in body.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        env = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(env, dict) and "total_cost_usd" in env:
                        cost = float(env["total_cost_usd"])
                        break
    except OSError:
        pass

    crashed = rc != 0
    if crashed and not crash_reason:
        crash_reason = f"exit {rc}"

    return VariantResult(
        variant=variant_letter,
        issue_number=issue.number,
        tier=issue.tier,
        started_at=started,
        duration_s=duration,
        cost_usd=cost,
        log_path=log_path,
        worktree=worktree,
        crashed=crashed,
        crash_reason=crash_reason,
    )


def run_variant_b(cfg: RoundConfig, issue: IssueSpec, issue_root: Path,
                  issue_title: str, issue_body: str) -> VariantResult:
    return _run_single_session_variant(cfg, issue, issue_root, "B", issue_title, issue_body)


def run_variant_c(cfg: RoundConfig, issue: IssueSpec, issue_root: Path,
                  issue_title: str, issue_body: str) -> VariantResult:
    return _run_single_session_variant(cfg, issue, issue_root, "C", issue_title, issue_body)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def _dispatch_variant(
    cfg: RoundConfig,
    variant_letter: str,
    issue: IssueSpec,
    issue_root: Path,
    issue_title: str,
    issue_body: str,
) -> VariantResult:
    """Dispatch to the right runner based on variant letter."""
    try:
        if variant_letter == "A":
            return run_variant_a(cfg, issue, issue_root)
        if variant_letter == "B":
            return run_variant_b(cfg, issue, issue_root, issue_title, issue_body)
        if variant_letter == "C":
            return run_variant_c(cfg, issue, issue_root, issue_title, issue_body)
        raise ValueError(f"unknown variant: {variant_letter}")
    except Exception as e:
        log.exception(
            "_dispatch_variant: variant=%s issue=%d crashed", variant_letter, issue.number
        )
        return VariantResult(
            variant=variant_letter,
            issue_number=issue.number,
            tier=issue.tier,
            started_at=_dt.datetime.utcnow().isoformat() + "Z",
            duration_s=0.0,
            cost_usd=None,
            log_path=issue_root / variant_letter / "run.log",
            worktree=issue_root / variant_letter / "worktree",
            crashed=True,
            crash_reason=f"dispatch exception: {e}",
        )


def _variant_result_to_row(
    result: VariantResult,
    cfg: RoundConfig,
) -> RunRow:
    """Compose a VariantResult + on-disk scoring into a RunRow.

    Pulls metrics from the worktree + log via abc_scoring.score_variant_run.
    Adds the crash_reason as an extra failure category if the variant
    crashed (without overwriting any categories the log already showed).
    """
    metrics = score_variant_run(result.worktree, result.log_path)

    if result.crashed:
        # Prepend a synthetic category if the variant crashed at the
        # subprocess level (vs internal failure).
        crash_cat = "harness-crash"
        existing = metrics.get("failure_categories") or ""
        if crash_cat not in existing.split(","):
            metrics["failure_categories"] = (
                f"{crash_cat},{existing}" if existing else crash_cat
            )

    return RunRow(
        round=cfg.round_name,
        ts=result.started_at,
        repo=cfg.repo,
        issue_number=result.issue_number,
        tier=result.tier,
        variant=result.variant,
        pr_url=metrics["pr_url"],
        pr_number=metrics["pr_number"],
        cost_usd=result.cost_usd,
        duration_s=result.duration_s,
        gate_verdict=metrics["gate_verdict"],
        test_pass_count=metrics["test_pass_count"],
        test_total_count=metrics["test_total_count"],
        diff_additions=metrics["diff_additions"],
        diff_deletions=metrics["diff_deletions"],
        diff_files=metrics["diff_files"],
        exported_func_count=metrics["exported_func_count"],
        failure_categories=metrics["failure_categories"],
        raw_log_path=str(result.log_path),
    )


def run_round(cfg: RoundConfig) -> list[int]:
    """Execute a full round. Returns list of inserted run_ids.

    For each issue: spawn A/B/C in parallel (3 threads). When all three
    finish, persist all three rows in order A, B, C. Then move on to the
    next issue. This keeps total parallelism capped at 3.
    """
    init_db(cfg.db_path)

    inserted_ids: list[int] = []
    for issue in cfg.issues:
        log.info(
            "run_round: issue=%d tier=%d notes=%r", issue.number, issue.tier, issue.notes
        )
        issue_root = cfg.runs_root / f"issue-{issue.number}"
        issue_root.mkdir(parents=True, exist_ok=True)

        # Fetch the issue body once and share it with B / C.
        try:
            title, body = fetch_issue_body(cfg.repo, issue.number)
        except Exception as e:
            log.error(
                "run_round: gh fetch failed for issue %d: %s — recording empty body",
                issue.number, e,
            )
            title, body = ("(fetch failed)", "")

        with cf.ThreadPoolExecutor(max_workers=len(cfg.variants)) as ex:
            futures = {
                ex.submit(
                    _dispatch_variant, cfg, v, issue, issue_root, title, body
                ): v
                for v in cfg.variants
            }
            results: dict[str, VariantResult] = {}
            for fut in cf.as_completed(futures):
                v = futures[fut]
                results[v] = fut.result()

        # Persist in canonical A/B/C order for stable scorecard layout.
        for v in ("A", "B", "C"):
            if v not in results:
                continue
            row = _variant_result_to_row(results[v], cfg)
            rid = insert_run(cfg.db_path, row)
            inserted_ids.append(rid)

    return inserted_ids


# --------------------------------------------------------------------------- #
# Scorecard rendering
# --------------------------------------------------------------------------- #


def _grid_for_metric(
    rows: list[dict],
    tiers: list[int],
    variants: list[str],
    *,
    selector,
    formatter,
):
    """Build a tier x variant grid from rows.

    selector(row) -> numeric value to aggregate (or None to skip).
    formatter(values: list[float|int]) -> str cell.

    Returns dict[tier][variant] = formatted cell.
    """
    grid: dict[int, dict[str, str]] = {}
    for tier in tiers:
        grid[tier] = {}
        for v in variants:
            vals = []
            for r in rows:
                if r["tier"] != tier or r["variant"] != v:
                    continue
                val = selector(r)
                if val is not None:
                    vals.append(val)
            grid[tier][v] = formatter(vals)
    return grid


def _fmt_pass_rate(rows: list[dict], tiers: list[int], variants: list[str]) -> dict:
    def sel(r):
        return r  # whole row
    def fmt(group):
        total = len(group)
        passes = sum(1 for r in group if (r.get("gate_verdict") or "") == "PASS")
        return f"{passes}/{total}" if total else "-/-"
    # Build manually since we need access to whole group, not single value
    grid: dict[int, dict[str, str]] = {}
    for tier in tiers:
        grid[tier] = {}
        for v in variants:
            group = [r for r in rows if r["tier"] == tier and r["variant"] == v]
            grid[tier][v] = fmt(group)
    return grid


def _fmt_avg_cost(rows: list[dict], tiers: list[int], variants: list[str]) -> dict:
    def sel(r):
        return r.get("cost_usd")
    def fmt(vals: list[float]) -> str:
        if not vals:
            return "  -   "
        return f"${sum(vals)/len(vals):>5.2f}"
    return _grid_for_metric(rows, tiers, variants, selector=sel, formatter=fmt)


def _fmt_avg_duration_min(rows: list[dict], tiers: list[int], variants: list[str]) -> dict:
    def sel(r):
        d = r.get("duration_s")
        return (d / 60.0) if d is not None else None
    def fmt(vals: list[float]) -> str:
        if not vals:
            return "  -  "
        return f"{sum(vals)/len(vals):>5.1f}"
    return _grid_for_metric(rows, tiers, variants, selector=sel, formatter=fmt)


def _failure_category_tally(rows: list[dict]) -> list[tuple[str, int]]:
    """Sum failure_categories across all rows. Returns descending counts."""
    counts: dict[str, int] = {}
    for r in rows:
        raw = r.get("failure_categories") or ""
        for tok in raw.split(","):
            tok = tok.strip()
            if not tok:
                continue
            counts[tok] = counts.get(tok, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _format_scorecard_text(
    round_name: str,
    rows: list[dict],
) -> str:
    """Render the scorecard as a fixed-width text block."""
    if not rows:
        return f"No runs found for round {round_name!r}.\n"
    # Pull dimensions from data
    tiers = sorted({r["tier"] for r in rows})
    variants = sorted({r["variant"] for r in rows})
    issue_count = len({r["issue_number"] for r in rows})

    # Header
    ts_first = rows[0]["ts"][:10] if rows else "?"
    lines: list[str] = []
    lines.append(
        f"== Round {round_name} ({ts_first}, {issue_count} issues, "
        f"{len(variants)} variants) =="
    )
    lines.append("")

    # Per-tier pass rates
    lines.append("Per-tier pass rates (gate_verdict == PASS):")
    header = "                  " + "".join(f"   {v:^5}" for v in variants)
    lines.append(header)
    pr_grid = _fmt_pass_rate(rows, tiers, variants)
    for tier in tiers:
        cells = "".join(f"   {pr_grid[tier][v]:^5}" for v in variants)
        lines.append(f"  tier {tier}        {cells}")
    lines.append("")

    # Average cost
    lines.append("Average cost (USD):")
    lines.append(header)
    cost_grid = _fmt_avg_cost(rows, tiers, variants)
    for tier in tiers:
        cells = "".join(f"   {cost_grid[tier][v]:^5}" for v in variants)
        lines.append(f"  tier {tier}        {cells}")
    lines.append("")

    # Average duration
    lines.append("Average duration (min):")
    lines.append(header)
    dur_grid = _fmt_avg_duration_min(rows, tiers, variants)
    for tier in tiers:
        cells = "".join(f"   {dur_grid[tier][v]:^5}" for v in variants)
        lines.append(f"  tier {tier}        {cells}")
    lines.append("")

    # Failure-category tally
    lines.append("Failure-category counts across all variants:")
    tally = _failure_category_tally(rows)
    if not tally:
        lines.append("  (none recorded)")
    else:
        for tok, n in tally:
            lines.append(f"  {tok}: {n}")
    lines.append("")

    return "\n".join(lines) + "\n"


def _format_scorecard_markdown(round_name: str, rows: list[dict]) -> str:
    """Render the scorecard as a markdown file for the runs/abc-scores/ dir."""
    if not rows:
        return f"# Round {round_name}\n\n_No runs._\n"
    tiers = sorted({r["tier"] for r in rows})
    variants = sorted({r["variant"] for r in rows})
    issue_count = len({r["issue_number"] for r in rows})
    ts_first = rows[0]["ts"][:10] if rows else "?"

    out: list[str] = []
    out.append(f"# ABC Scorecard — Round {round_name}")
    out.append("")
    out.append(f"- Date: {ts_first}")
    out.append(f"- Issues: {issue_count}")
    out.append(f"- Variants: {', '.join(variants)}")
    out.append("")

    def _md_table(title: str, grid: dict) -> list[str]:
        rows_md = [f"## {title}", "", "| tier | " + " | ".join(variants) + " |"]
        rows_md.append("|---|" + "---|" * len(variants))
        for tier in tiers:
            cells = " | ".join(grid[tier][v].strip() for v in variants)
            rows_md.append(f"| {tier} | {cells} |")
        rows_md.append("")
        return rows_md

    out.extend(_md_table("Pass rates (gate_verdict == PASS)",
                         _fmt_pass_rate(rows, tiers, variants)))
    out.extend(_md_table("Average cost (USD)",
                         _fmt_avg_cost(rows, tiers, variants)))
    out.extend(_md_table("Average duration (min)",
                         _fmt_avg_duration_min(rows, tiers, variants)))

    out.append("## Failure categories (all variants)")
    out.append("")
    tally = _failure_category_tally(rows)
    if not tally:
        out.append("_(none recorded)_")
    else:
        out.append("| category | count |")
        out.append("|---|---|")
        for tok, n in tally:
            out.append(f"| {tok} | {n} |")
    out.append("")

    out.append("## Per-row details")
    out.append("")
    out.append("| issue | tier | variant | gate | pass/total | cost | dur(s) | files | +adds | -dels | def | failures | PR |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        out.append(
            "| {issue} | {tier} | {variant} | {gate} | {tp}/{tt} | "
            "{cost} | {dur} | {df} | {a} | {d} | {ef} | {fc} | {pr} |".format(
                issue=r["issue_number"],
                tier=r["tier"],
                variant=r["variant"],
                gate=r.get("gate_verdict") or "-",
                tp=r.get("test_pass_count") if r.get("test_pass_count") is not None else "-",
                tt=r.get("test_total_count") if r.get("test_total_count") is not None else "-",
                cost=(f"${r['cost_usd']:.2f}" if r.get("cost_usd") is not None else "-"),
                dur=(f"{r['duration_s']:.0f}" if r.get("duration_s") is not None else "-"),
                df=r.get("diff_files") if r.get("diff_files") is not None else "-",
                a=r.get("diff_additions") if r.get("diff_additions") is not None else "-",
                d=r.get("diff_deletions") if r.get("diff_deletions") is not None else "-",
                ef=r.get("exported_func_count") if r.get("exported_func_count") is not None else "-",
                fc=(r.get("failure_categories") or "-"),
                pr=(f"[#{r['pr_number']}]({r['pr_url']})" if r.get("pr_url") else "-"),
            )
        )
    out.append("")

    return "\n".join(out) + "\n"


def render_scorecard(
    db_path: Path | str,
    round_name: str,
    md_out_dir: Path | str | None = None,
) -> str:
    """Read rows for ``round_name`` and return the fixed-width scorecard text.

    If ``md_out_dir`` is provided, also writes a markdown rendering to
    ``{md_out_dir}/{round_name}-scorecard.md``. Both renderings use the
    same underlying row set, so they cannot drift.
    """
    from claude_pipeline.abc_db import fetch_runs

    rows = fetch_runs(db_path, round_name)
    text = _format_scorecard_text(round_name, rows)

    if md_out_dir:
        md_dir = Path(md_out_dir)
        md_dir.mkdir(parents=True, exist_ok=True)
        md_path = md_dir / f"{round_name}-scorecard.md"
        md_path.write_text(_format_scorecard_markdown(round_name, rows))
        log.info("render_scorecard: wrote %s", md_path)

    return text
