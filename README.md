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

## Architectural rules (binding on all upgrades)

### Rule 1 — Every step is an LLM judgment by default

Deterministic steps require A/B-test evidence that they outperform an LLM call at the same decision. The default for any new decision point in this pipeline is "spawn an LLM". The burden of proof is on "hardcode this" — usually meaning mechanical string operations (JSON parsing, entropy, file copies) where there is no judgment to make.

Concrete consequences:
- Retry counts, retry strategies, "which stage to redo" → LLM, not constants.
- Commit messages, PR bodies, branch names → LLM, not templates.
- "Which base branch", "what files to stage", "is this a final state" → LLM, with the LLM having read the repo conventions.
- The only steps that may stay deterministic without A/B justification are pure-mechanical ones (`json.loads`, `secrets.token_hex`, `git add -A` of an already-decided file list).

### Rule 2 — Port from metabuilder, don't reimagine

Where metabuilder has an analog of a node, use metabuilder's prompts, decision logic, and post-processing verbatim. Swap only the LLM transport (local proxy → `claude --print`). Reimaginings need explicit justification (e.g. "this metabuilder path required a system that doesn't exist here"). See `docs/metabuilder-port-spec.md` for the canonical port reference.

### Rule 3 — A/B every escalation

The pipeline only gains complexity when an A/B test shows the new version matches or beats the prior version on the same issue. The first baseline is a single `claude --print` call with the issue body. After that, each version is the baseline for the next.

## Pipeline phases

```
gh issue → INTAKE → RESEARCH → SYSTEM_GAP_ANALYST → CONTRACT → PLAN → CODE → VERIFY → PR
                                                                          ↑      │
                                                                          └──── (verify fail loops back, max 2 retries) ──┘
```

Each phase is a LangGraph node. Each node shells out to `claude --print` with a focused prompt and a slice of pipeline state. State persists to a SQLite checkpoint after every node — pipelines that crash mid-flight can be resumed.

### Adversarial gap analysis (`system_gap_analyst`)

Sitting between **research** and **contract**, the `system_gap_analyst` is an adversarial pre-pass ported from metabuilder. Its job is to find what is missing, unstated, or quietly broken in the framing before the contract is locked in. It walks 8 named lenses — *infrastructure-assumed-but-not-mentioned, silent-failure, cross-cutting-concerns, next-stage-prerequisites, YAGNI-cut, fake-completion, architecture-smell, developer-contract-completeness* — and emits a structured `{blocking_gaps, advisory_gaps, summary}` document. Blocking gaps are injected into the contract_writer's user packet as **MANDATORY ADDITIONAL DELIVERABLES** that the contract must cover; advisory gaps ride along as suggestions only. The pass runs as a fresh Tier 3 / Opus session at temperature 0.2 so its judgment isn't anchored to anything earlier in the run.

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
│   ├── system_gap_analyst.py
│   ├── contract.py
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
