"""Prompt-expansion node: one Claude call PER STAGE in parallel.

Verbatim port of metabuilder's per-stage prompt expansion pass (line 3265
of plan_self_upgrade.js):
  - System prompt = `prompts/metabuilder/11_implementation_builder.md`.
  - User message = Python port of `buildPromptExpansionPacket()`:
    codebase anchor + relevant file excerpts (from gather_excerpts_for_files)
    + stage metadata + do_not_touch + acceptance criteria + contract
    deliverables verbatim + conditional discipline blocks.
  - Demands 11 numbered sections IN ORDER (truth boundary,
    do-not-claim-completion-unless, goal, read-these-files-first,
    in-scope, out-of-scope, fake-completion-scenarios, required changes,
    acceptance criteria, scope boundaries, stop condition).
  - Output is MARKDOWN (not JSON).
  - Tier 3 / Opus / max_tokens=8192 (the JS comment says Sonnet
    hallucinated paths at 8192 tok — Opus is the safe choice).

Per-stage prompts saved to `runs/{run_id}/prompts/P{NN}_{stage}.md` for
the code node to read. Parallel via ThreadPoolExecutor(max_workers=4).
"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from claude_pipeline.claude import ClaudeError, run_claude
from claude_pipeline.excerpts import gather_excerpts_for_files
from claude_pipeline.state import PipelineState, Stage

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder"
_IMPL_BUILDER_PATH = _PROMPTS_DIR / "11_implementation_builder.md"
_RUNS_DIR = Path(__file__).resolve().parents[3] / "runs"

MAX_PARALLEL = 4


def _load_role_prompt() -> str:
    try:
        return _IMPL_BUILDER_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing implementation_builder role prompt at {_IMPL_BUILDER_PATH}: {e}"
        ) from e


def _safe_stage_slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-")
    return s[:40] or "stage"


def _ftm_to_lists(stage: Stage) -> tuple[list[str], list[str], list[str]]:
    """Return (create, modify, do_not_touch) lists for a stage."""
    ftm = stage.get("file_touch_map", {})
    if isinstance(ftm, dict):
        create = [str(x) for x in (ftm.get("create") or [])]
        modify = [str(x) for x in (ftm.get("modify") or [])]
        dnt = [str(x) for x in (ftm.get("do_not_touch") or [])]
        return create, modify, dnt
    if isinstance(ftm, list):
        # flat list: treat as modify
        return [], [str(x) for x in ftm], []
    return [], [], []


def _render_contract_deliverables(deliverables: list[dict[str, Any]]) -> str:
    if not deliverables:
        return "(no deliverables specified)"
    out: list[str] = []
    for d in deliverables:
        out.append(f"- **{d.get('id', '?')}** — `{d.get('name', '?')}` — {d.get('description', '')}")
        for c in d.get("success_criteria", []) or []:
            out.append(f"    - success: {c}")
    return "\n".join(out)


def _build_codebase_anchor(state: PipelineState) -> str:
    """Short anchor: where the work happens, what the repo is."""
    return (
        f"Repository: {state.get('repo', '?')}\n"
        f"Worktree (your cwd): {state.get('worktree_path', '?')}\n"
        f"Issue: #{state.get('issue_number', '?')} — {state.get('issue_title', '?')}"
    )


_FILE_DISCIPLINE_RULES = [
    # (pattern_substring, block_text)
    (
        ".test.",
        "**TEST FILE DISCIPLINE:** Test files must not contain production logic. "
        "Use existing test conventions (pytest fixtures, jest mocks). No new test "
        "frameworks introduced in this stage.",
    ),
    (
        "auth",
        "**SECURITY DISCIPLINE:** Auth-adjacent file. Do not weaken existing checks. "
        "Do not log secrets. Do not change cookie/token defaults.",
    ),
    (
        "schema",
        "**SCHEMA DISCIPLINE:** Schema change detected. Preserve column defaults. "
        "Do not delete columns. Document migrations.",
    ),
]


def _conditional_discipline(file_touch_map_paths: list[str]) -> str:
    blob = "\n".join(file_touch_map_paths).lower()
    out: list[str] = []
    for needle, text in _FILE_DISCIPLINE_RULES:
        if needle in blob:
            out.append(text)
    return "\n\n".join(out)


def _build_user_packet(stage: Stage, state: PipelineState) -> str:
    """Port of buildPromptExpansionPacket.

    The output is a meta-prompt: it tells the implementation_builder
    role to WRITE A PROMPT (in markdown) that the coder will consume.
    """
    intake = state.get("intake", {})
    contract = state.get("contract", {}) or {}
    research_brief = state.get("research_brief", "")
    deliverables = contract.get("deliverables", []) or []

    create, modify, dnt = _ftm_to_lists(stage)
    touched = create + modify

    # Inline file excerpts for context — head of each existing file
    # that the stage will modify (newly-created files don't exist yet).
    worktree = state.get("worktree_path") or "."
    excerpts = gather_excerpts_for_files(modify, worktree)
    discipline = _conditional_discipline(touched + dnt)

    sid = stage.get("stage_id") or stage.get("name", "?")
    name = stage.get("name", "?")
    purpose = stage.get("purpose") or stage.get("description") or "?"
    role = stage.get("role", "implementation_builder")
    crit_lines: list[str] = []
    for c in stage.get("acceptance_criteria", []) or []:
        if isinstance(c, dict):
            crit_lines.append(
                f"  - check: `{c.get('check', '')}` — pass when: {c.get('pass_condition', '')}"
            )
        elif isinstance(c, str):
            crit_lines.append(f"  - {c}")
    if not crit_lines:
        crit_lines.append("  (none specified by planner — fall back to issue acceptance criteria)")

    intake_crit: list[str] = []
    for c in intake.get("acceptance_criteria", []) or []:
        intake_crit.append(f"  - {c}")

    create_bullets = "\n".join(f"  - {p}" for p in create) or "  (none)"
    modify_bullets = "\n".join(f"  - {p}" for p in modify) or "  (none)"
    dnt_bullets = "\n".join(f"  - {p}" for p in dnt) or "  (none)"

    lines = [
        "## Codebase anchor",
        "",
        _build_codebase_anchor(state),
        "",
        "## Stage to expand",
        "",
        f"- **Stage ID:** {sid}",
        f"- **Name:** {name}",
        f"- **Role:** {role}",
        f"- **Purpose:** {purpose}",
        "",
        "**File touch map (create):**",
        create_bullets,
        "",
        "**File touch map (modify):**",
        modify_bullets,
        "",
        "**Do-not-touch:**",
        dnt_bullets,
        "",
        "**Acceptance criteria (stage-level):**",
        "\n".join(crit_lines),
        "",
        "**Acceptance criteria (issue-level — must also be satisfied):**",
        "\n".join(intake_crit) or "  (none)",
        "",
        "## Contract deliverables (verbatim — must remain visible to the coder)",
        "",
        _render_contract_deliverables(deliverables),
        "",
        "## Research evidence (for context)",
        "",
        (research_brief or "(no research brief)")[:6000],
        "",
        "## Relevant file excerpts (head of files this stage will modify)",
        "",
        excerpts or "(no existing-file excerpts; stage may be all-new-files)",
    ]
    if discipline:
        lines.extend(["", "## Conditional discipline blocks", "", discipline])

    lines.extend(
        [
            "",
            "## Your job",
            "",
            "You are acting as implementation_builder. **Do NOT write code.** Your job is to",
            "produce the BRIEF that the coder will read. Output a markdown document with these",
            "11 numbered sections IN ORDER. Use these exact headings (`## N. Title`).",
            "",
            "1. Truth boundary — what is known vs. assumed vs. unknown for this stage.",
            "2. Do not claim completion unless — list 3-5 verifiable conditions; the coder",
            "   may not declare done until ALL are satisfied.",
            "3. Goal — one paragraph: what this stage produces and why.",
            "4. Read these files first — explicit list of files the coder must Read before",
            "   editing anything. Include line ranges if surgical.",
            "5. In-scope files — paths the coder MAY edit (from create + modify above).",
            "6. Out-of-scope files — paths the coder MUST NOT edit (from do_not_touch above).",
            "7. What would count as fake completion — 2-3 specific scenarios where tests",
            "   pass but the work is not actually done. Be concrete.",
            "8. Required changes — bullet list: what to add/modify, by file. Reference",
            "   existing patterns in the repo (read the excerpts above).",
            "9. Acceptance criteria — commands only. Every line is a shell command or grep",
            "   pattern that returns 0 on success. No prose criteria.",
            "10. Scope boundaries — call out anything the coder might be tempted to",
            "    'while we're at it' and explain why it's off-limits this stage.",
            "11. Stop condition — exact sentence the coder writes when done.",
            "",
            "Rules:",
            "- File path verification: any path you name in section 4 or 5 must appear in",
            "  the excerpts above OR in the file touch map. No invented paths.",
            "- Acceptance criteria (section 9) must be shell-runnable. No prose.",
            "- Stop condition (section 11) must end with the literal string",
            "  'Stage complete: <stage_id>' where <stage_id> matches this stage.",
            "- Output the markdown brief only. No JSON. No prose preamble outside the",
            "  numbered sections. No trailing commentary.",
        ]
    )
    return "\n".join(lines)


def _expand_one_stage(
    idx: int,
    stage: Stage,
    state: PipelineState,
    role_prompt: str,
    prompts_dir: Path,
) -> dict[str, Any]:
    """Worker for one stage. Returns {idx, stage_id, prompt_path, prompt_text, error}."""
    sid = stage.get("stage_id") or f"S{idx + 1}"
    slug = _safe_stage_slug(stage.get("name", sid))
    user_msg = _build_user_packet(stage, state)

    log.info(
        "expand: invoking claude for stage %s (idx=%d)", sid, idx
    )
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="opus",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return {
            "idx": idx,
            "stage_id": sid,
            "prompt_path": "",
            "prompt_text": "",
            "error": f"expand {sid}: claude call failed: {e}",
        }

    text = result.text.strip()
    if not text:
        return {
            "idx": idx,
            "stage_id": sid,
            "prompt_path": "",
            "prompt_text": "",
            "error": f"expand {sid}: empty output",
        }

    prompts_dir.mkdir(parents=True, exist_ok=True)
    fname = f"P{idx + 1:02d}_{slug}.md"
    fpath = prompts_dir / fname
    try:
        fpath.write_text(text, encoding="utf-8")
    except OSError as e:
        return {
            "idx": idx,
            "stage_id": sid,
            "prompt_path": "",
            "prompt_text": text,
            "error": f"expand {sid}: write failed: {e}",
        }

    log.info(
        "expand: stage %s done (%.1fs, $%.4f, %d turns) -> %s",
        sid,
        result.duration_s,
        result.cost_usd,
        result.num_turns,
        fpath.name,
    )
    return {
        "idx": idx,
        "stage_id": sid,
        "prompt_path": str(fpath),
        "prompt_text": text,
        "error": None,
    }


def prompt_expand_node(state: PipelineState) -> dict:
    """Run prompt-expansion for every stage in the plan, in parallel."""
    plan: list[Stage] = state.get("plan", []) or []
    if not plan:
        return {"error": "prompt_expand: empty plan"}

    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    run_id = state.get("run_id") or "unknown"
    prompts_dir = _RUNS_DIR / run_id / "prompts"

    log.info(
        "prompt_expand: launching %d stage(s) in parallel (workers=%d)",
        len(plan),
        min(MAX_PARALLEL, len(plan)),
    )
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL, len(plan))) as pool:
        futures = [
            pool.submit(_expand_one_stage, i, s, state, role_prompt, prompts_dir)
            for i, s in enumerate(plan)
        ]
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: r["idx"])
    errors = [r["error"] for r in results if r.get("error")]
    if errors:
        # If every single stage failed, that's a hard error.
        # If only some failed, log loudly and continue with the rest;
        # the code node will skip stages with no prompt_path.
        if len(errors) == len(results):
            return {"error": f"prompt_expand: all stages failed: {errors[0]}"}
        log.warning("prompt_expand: %d/%d stages failed", len(errors), len(results))

    # Mutate the plan in-place to attach prompt_path / expanded_prompt
    new_plan: list[Stage] = []
    for stage, r in zip(plan, results):
        merged: Stage = dict(stage)  # type: ignore[assignment]
        merged["prompt_path"] = r.get("prompt_path", "")
        merged["expanded_prompt"] = r.get("prompt_text", "")
        new_plan.append(merged)

    # Persist a manifest for debugging / resume inspection
    try:
        manifest = {
            "run_id": run_id,
            "stage_count": len(new_plan),
            "errors": errors,
            "stages": [
                {
                    "stage_id": s.get("stage_id"),
                    "name": s.get("name"),
                    "prompt_path": s.get("prompt_path"),
                    "has_prompt": bool(s.get("expanded_prompt")),
                }
                for s in new_plan
            ],
        }
        prompts_dir.mkdir(parents=True, exist_ok=True)
        (prompts_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    except OSError:
        pass

    log.info("prompt_expand done: %d prompts written", len([r for r in results if not r.get('error')]))
    return {"plan": new_plan, "error": None}
