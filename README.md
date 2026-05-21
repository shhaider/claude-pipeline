# claude-pipeline

GitHub issue → PR orchestrator. Built on LangGraph with Claude Code CLI as the harness.

## Status

v0.1.0 (in flight). MVP scope: take a GitHub issue, run it through intake → research → plan → code → test → commit/PR.

Designed to **self-bootstrap**: once v0.1 is working, point it at this repo and feed it issues that upgrade itself toward the full metabuilder-equivalent pipeline.

## Stack

- Python 3.11+
- `langgraph` — state-machine orchestration with built-in checkpointing
- `langgraph-checkpoint-sqlite` — SQLite-backed pause/resume
- `claude` CLI — the LLM harness (no proxy, no custom tool exec, no custom memory)

## Pipeline phases (MVP)

```
gh issue → INTAKE → RESEARCH → PLAN → CODE → VERIFY → PR
              ↑                            │
              └───── (verify fail loops back, max 2 retries) ──┘
```

Each phase is a LangGraph node. Each node shells out to `claude --print` with a focused prompt and a slice of pipeline state. State persists to a SQLite checkpoint after every node — pipelines that crash mid-flight can be resumed.

## CLI

```bash
# Run a fresh pipeline on a GitHub issue:
claude-pipeline run <owner/repo> <issue_number>

# Resume a paused / crashed run:
claude-pipeline resume <run_id>

# Inspect state of any run:
claude-pipeline status <run_id>

# Render the graph as Mermaid:
claude-pipeline graph
```

## Layout

```
src/claude_pipeline/
├── state.py        # TypedDict for graph state
├── graph.py        # LangGraph wiring
├── nodes/          # one file per phase
│   ├── intake.py
│   ├── research.py
│   ├── plan.py
│   ├── code.py
│   ├── verify.py
│   └── pr.py
├── claude.py       # subprocess wrapper for `claude --print`
└── cli.py          # entry point

prompts/            # prompt templates per node
runs/               # per-invocation state + checkpoint DB
tests/              # pytest suite
```

## Out of scope (until v0.2+)

- Multi-node-per-phase (intake-clarify, intake-scope-broaden, etc.)
- Parallel prompt expansion
- Governance review pass
- Per-stage iteration loops (4-Correction, 2-Revision, repair cycle)
- Routing between software / writing lanes
- Per-node tool-use restrictions (Claude Code already handles this)

All of those are upgrade issues that will be filed against this repo and built BY this pipeline.

## Constraints

- Claude Code CLI auth uses whatever's in `CLAUDE_CONFIG_DIR` (default `~/.claude`)
- `gh` CLI must be authenticated for the target repo
- Each pipeline invocation creates a fresh git worktree under `runs/{run_id}/worktree/`
- Subprocess wall-clock timeout on every `claude --print` call (default 10 min)

## Co-authorship

Every commit and PR body produced by the pipeline ends with a git trailer attributing the change to the pipeline:

```
Co-Authored-By: claude-pipeline <noreply@anthropic.com>
```

This makes machine-generated changes auditable at a glance from `git log` and the GitHub PR view.
