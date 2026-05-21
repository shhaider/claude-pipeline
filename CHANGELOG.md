# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (v0.3 — context + reviewers)

- **Shared code session across stages.** `run_claude()` now accepts a `resume_session_id` parameter that maps to `claude --resume <id>`. The code node starts a fresh session for stage 0 and resumes the same session for every subsequent stage, so the implementer accumulates context across stages and can refactor work it produced earlier — the missing edge that lost v0.2's A/B test against the single-call baseline.
- **5-role review ladder** replacing the single verify-judges-everything node. After the code node and a slim test-runner verify, the diff flows through `pack_reviewer` → `reasoning_reviewer` → `governance_reviewer` → (optional `governance_repair`, max 2 rounds) → `release_gatekeeper`. Verbatim role prompts from metabuilder (`12_*`, `34_*`, `08_*`, `19_*`) loaded as `--append-system-prompt`.
- **Governance repair loop** (`nodes/governance_repair.py`, pure-Python port of metabuilder's 309-LOC `governance_repair_loop.js`). Extracts must_fix items from the governance verdict, identifies affected stages by stage_id mention or 4+-char keyword match, asks pack_planner for single-stage JSON patches, merges them, re-runs the affected stages on the resumed code session, then re-invokes governance_reviewer. Loops up to 2 rounds.
- **diff.capture_diff()** helper — captures `git diff <base>` for every reviewer to see the same change set, with an 80 KB head+tail cap.
- New `PipelineState` keys: `code_session_id`, `code_diff`, `pack_review`, `reasoning_review`, `governance_review`, `governance_repair_rounds`, `governance_repair_log`, `gatekeeper`.
- 25 new pytest cases covering the pure-Python pieces (governance_repair item extraction, stage-affect matching, patch parsing, merge, diff capture).

### Changed (v0.3)

- **`verify_node` slimmed to test-runner only.** It no longer judges acceptance criteria — that job moved to `governance_reviewer`, which sees the diff plus all prior verdicts. Verify still runs via `claude --print` because the pipeline doesn't know the target repo's test stack.
- **Graph topology** — `code → verify → pack_reviewer → reasoning_reviewer → governance_reviewer → {governance_repair | release_gatekeeper} → governance_repair → release_gatekeeper → {pr | error_exit}`. The v0.2 `retry_code` edge is removed; repair is now the governance_repair loop's responsibility.

## [0.1.0] - 2026-05-21

### Added

- LangGraph-based orchestrator that drives a GitHub issue through a single end-to-end pipeline run, with SQLite checkpointing (`langgraph-checkpoint-sqlite`) so paused or crashed runs can be resumed.
- Six-node pipeline covering intake → research → plan → code → verify → pr, wired as a LangGraph state machine with a verify-fail retry loop back into code (max 2 retries).
- `claude` CLI subprocess harness that invokes `claude --print` per node with a focused prompt and a slice of pipeline state, using a wall-clock timeout on every call.
- `claude-pipeline` CLI entry point with `run`, `resume`, `status`, and `graph` subcommands for starting fresh runs, resuming from checkpoint, inspecting run state, and rendering the graph as Mermaid.
