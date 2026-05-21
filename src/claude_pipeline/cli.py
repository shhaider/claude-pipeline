"""CLI entry point.

Subcommands:
  run    <owner/repo> <issue_number>  — fresh pipeline run
  resume <run_id>                      — resume a paused or crashed run
  status <run_id>                      — show current state of any run
  graph                                — print the pipeline graph as Mermaid
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
import subprocess
import sys
from pathlib import Path

from claude_pipeline.claude import assert_claude_available
from claude_pipeline.graph import build_graph, render_mermaid
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

RUNS_DIR = Path(__file__).resolve().parent.parent.parent / "runs"


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)-30s %(message)s",
        datefmt="%H:%M:%S",
    )


def _new_run_id() -> str:
    """Short readable run id: 8 hex chars. Unique per run."""
    return secrets.token_hex(4)


def _fetch_issue(repo: str, issue_number: int) -> dict:
    """Call gh CLI to fetch the issue. Returns parsed JSON."""
    proc = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo,
            "--json",
            "title,body,number,labels,state",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh issue view failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _create_worktree(repo: str, run_id: str, base_branch: str) -> tuple[Path, Path, str]:
    """Create a per-run worktree.

    Returns (run_dir, worktree_path, feature_branch).

    For MVP we clone fresh into runs/{run_id}/worktree/. A v0.2 upgrade
    will share a bare repo (like Conductor does) for speed.
    """
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    worktree = run_dir / "worktree"
    branch = f"claude-pipeline/{run_id}"

    url = f"https://github.com/{repo}.git"
    log.info("cloning %s into %s (this may take a minute)", url, worktree)
    proc = subprocess.run(
        ["git", "clone", "--depth", "50", "--branch", base_branch, url, str(worktree)],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {proc.stderr.strip()}")

    # Create the feature branch
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=str(worktree),
        check=True,
        timeout=30,
        capture_output=True,
        text=True,
    )
    log.info("worktree ready: %s on branch %s", worktree, branch)
    return run_dir, worktree, branch


def cmd_run(args: argparse.Namespace) -> int:
    assert_claude_available()
    repo = args.repo
    issue_number = args.issue

    # Pre-flight: fetch issue body
    issue = _fetch_issue(repo, issue_number)
    if issue.get("state") == "CLOSED":
        log.warning("issue #%d is CLOSED — proceeding anyway", issue_number)

    run_id = _new_run_id()
    run_dir, worktree, feature_branch = _create_worktree(repo, run_id, args.base)

    checkpoint_db = run_dir / "checkpoint.db"
    graph = build_graph(checkpoint_db)

    initial_state: PipelineState = {
        "run_id": run_id,
        "repo": repo,
        "issue_number": issue_number,
        "worktree_path": str(worktree),
        "base_branch": args.base,
        "feature_branch": feature_branch,
        "issue_title": issue["title"],
        "issue_body": issue.get("body") or "",
        "current_stage_idx": 0,
        "retry_count": 0,
        "error": None,
    }

    # Persist the initial inputs to a json file so `status` can read them
    # without traversing the checkpointer.
    (run_dir / "input.json").write_text(json.dumps(
        {
            "run_id": run_id,
            "repo": repo,
            "issue_number": issue_number,
            "feature_branch": feature_branch,
            "base_branch": args.base,
        },
        indent=2,
    ))

    config = {"configurable": {"thread_id": run_id}}
    log.info("pipeline run starting: id=%s repo=%s issue=#%d", run_id, repo, issue_number)
    print(f"\nRun id: {run_id}")
    print(f"Worktree: {worktree}")
    print(f"Branch:  {feature_branch}")
    print(f"Resume:  claude-pipeline resume {run_id}\n")

    try:
        final = graph.invoke(initial_state, config=config)
    except KeyboardInterrupt:
        log.warning("interrupted — resume with: claude-pipeline resume %s", run_id)
        return 130
    except Exception:
        log.exception("pipeline crashed — resume with: claude-pipeline resume %s", run_id)
        return 1

    if final.get("error"):
        print(f"\nFINAL STATE has error: {final['error']}", file=sys.stderr)
        return 2

    pr_url = final.get("pr_url")
    if pr_url:
        print(f"\nPR: {pr_url}\n")
        return 0
    print("\nPipeline completed but no PR was opened. Run status to inspect.", file=sys.stderr)
    return 3


def cmd_resume(args: argparse.Namespace) -> int:
    assert_claude_available()
    run_id = args.run_id
    run_dir = RUNS_DIR / run_id
    if not run_dir.exists():
        print(f"unknown run id: {run_id}", file=sys.stderr)
        return 4

    checkpoint_db = run_dir / "checkpoint.db"
    if not checkpoint_db.exists():
        print(f"no checkpoint db for run {run_id}", file=sys.stderr)
        return 5

    graph = build_graph(checkpoint_db)
    config = {"configurable": {"thread_id": run_id}}

    # Passing None as input + same thread_id resumes from the last checkpoint.
    log.info("resuming run %s", run_id)
    try:
        final = graph.invoke(None, config=config)
    except KeyboardInterrupt:
        log.warning("interrupted again — resume with: claude-pipeline resume %s", run_id)
        return 130
    except Exception:
        log.exception("pipeline crashed on resume — resume again: claude-pipeline resume %s", run_id)
        return 1

    if final.get("pr_url"):
        print(f"PR: {final['pr_url']}")
        return 0
    if final.get("error"):
        print(f"error: {final['error']}", file=sys.stderr)
        return 2
    print("resumed run completed but no PR was opened")
    return 3


def cmd_status(args: argparse.Namespace) -> int:
    run_dir = RUNS_DIR / args.run_id
    if not run_dir.exists():
        print(f"unknown run id: {args.run_id}", file=sys.stderr)
        return 4

    checkpoint_db = run_dir / "checkpoint.db"
    if not checkpoint_db.exists():
        print(f"no checkpoint db for run {args.run_id}", file=sys.stderr)
        return 5

    graph = build_graph(checkpoint_db)
    config = {"configurable": {"thread_id": args.run_id}}
    snapshot = graph.get_state(config)
    print(f"\nRun id:      {args.run_id}")
    print(f"Next node:   {', '.join(snapshot.next) if snapshot.next else '(done)'}")
    print(f"\nState (truncated):")
    for k, v in (snapshot.values or {}).items():
        if isinstance(v, str) and len(v) > 200:
            print(f"  {k}: {v[:200]}... ({len(v)} chars)")
        elif isinstance(v, list) and len(v) > 5:
            print(f"  {k}: [{len(v)} items]")
        else:
            print(f"  {k}: {v}")
    return 0


def cmd_graph(_args: argparse.Namespace) -> int:
    print(render_mermaid())
    return 0


def cmd_abc_run(args: argparse.Namespace) -> int:
    """Run one round of the ABC harness against a YAML config."""
    from claude_pipeline.abc_harness import load_round_config, run_round

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"config not found: {cfg_path}", file=sys.stderr)
        return 4

    cfg = load_round_config(cfg_path, round_name=args.round)
    log.info(
        "abc-run starting: round=%s repo=%s issues=%d variants=%s db=%s",
        cfg.round_name, cfg.repo, len(cfg.issues), cfg.variants, cfg.db_path,
    )
    inserted = run_round(cfg)
    print(f"\nabc-run finished: inserted {len(inserted)} rows into {cfg.db_path}")
    print(f"Render the scorecard with: claude-pipeline abc-scorecard {cfg.round_name} "
          f"--db {cfg.db_path}")
    return 0


def cmd_abc_scorecard(args: argparse.Namespace) -> int:
    """Render the scorecard for one round of the ABC harness."""
    from claude_pipeline.abc_harness import render_scorecard

    db_path = Path(args.db) if args.db else (RUNS_DIR / "abc-scores.db")
    if not db_path.exists():
        print(f"DB not found: {db_path}", file=sys.stderr)
        return 4

    md_out_dir = Path(args.md_out_dir) if args.md_out_dir else (RUNS_DIR / "abc-scores")
    text = render_scorecard(db_path, args.round, md_out_dir=md_out_dir)
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="claude-pipeline")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run a fresh pipeline on an issue")
    p_run.add_argument("repo", help="owner/name on GitHub")
    p_run.add_argument("issue", type=int, help="issue number")
    p_run.add_argument("--base", default="main", help="base branch to fork from")
    p_run.set_defaults(fn=cmd_run)

    p_res = sub.add_parser("resume", help="resume a paused / crashed run")
    p_res.add_argument("run_id")
    p_res.set_defaults(fn=cmd_resume)

    p_stat = sub.add_parser("status", help="show state of a run")
    p_stat.add_argument("run_id")
    p_stat.set_defaults(fn=cmd_status)

    p_g = sub.add_parser("graph", help="print the pipeline graph as Mermaid")
    p_g.set_defaults(fn=cmd_graph)

    p_abc = sub.add_parser("abc-run", help="run one ABC harness round from a YAML config")
    p_abc.add_argument("config", help="path to the round YAML config")
    p_abc.add_argument("--round", default=None,
                       help="override round name (defaults to yaml basename)")
    p_abc.set_defaults(fn=cmd_abc_run)

    p_score = sub.add_parser("abc-scorecard", help="render the scorecard for a round")
    p_score.add_argument("round", help="round name to render")
    p_score.add_argument("--db", default=None,
                         help="path to the SQLite DB (default: runs/abc-scores.db)")
    p_score.add_argument("--md-out-dir", default=None,
                         help="directory for the markdown rendering "
                              "(default: runs/abc-scores)")
    p_score.set_defaults(fn=cmd_abc_scorecard)

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
