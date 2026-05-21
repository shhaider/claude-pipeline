# Handoff — system_gap_analyst adversarial pre-lane

**Readiness:** READY_FOR_REVIEW
**Status:** PASS_HANDOFF_COMPLETE
**Outcome label:** INFRASTRUCTURE_READY_NOT_WIRED
**Task ID:** SYSTEM-GAP-ANALYST-001
**Task area:** system-gap-analyst
**Closes:** GitHub issue #9

---

## Summary

Ports metabuilder's `system_gap_analyst` adversarial pre-lane between `research` and `plan` in the claude-pipeline LangGraph. The new node loads `prompts/metabuilder/35_system_gap_analyst.md` as a system prompt, builds a user packet (intake + research brief + codebase anchor + issue + 8-lens menu + JSON output reminder), invokes `claude --print` with `model=claude-opus-4-7`, parses the JSON, validates the 8 canonical lens slugs, and emits `gap_analysis: {blocking_gaps, advisory_gaps, summary}` into pipeline state. `plan_node` injects blocking gaps as MANDATORY ADDITIONAL DELIVERABLES and advisory gaps as suggestions.

When the contract/planner split lands (roadmap item 4 in `docs/metabuilder-port-spec.md`), the injection target moves from `plan_node` to the new contract node. Until then `plan_node` is the injection target.

---

## Git state

- **Branch:** V3-rerun-1779380607 (off `main`)
- **Implementation commit:** `6fcf87d` — "Add system_gap_analyst adversarial pre-lane between research and plan"
- **Gate package commit:** lands on the same branch after this gate run completes.
- **Final worktree status:** clean — see `git_status_final.txt`.

---

## Evidence layer

- Tests: 9/9 PASS in `tests/test_system_gap_analyst.py`.
- Raw test output: `reports/system-gap-analyst/raw/pytest.log` (E001) with exact `EXIT_CODE:0`.
- Test command (no env-var prerequisites): `python3 -m pytest tests/test_system_gap_analyst.py -v` from repo root.
- Source files: `src/claude_pipeline/nodes/system_gap_analyst.py` (E003), `src/claude_pipeline/graph.py` (E002), `src/claude_pipeline/state.py`, `src/claude_pipeline/nodes/plan.py`, `prompts/metabuilder/35_system_gap_analyst.md`, `tests/test_system_gap_analyst.py` (E005), `conftest.py` (E006).

---

## Reviewer panel results

| Reviewer | Blocking | Non-blocking |
|---|---|---|
| R1 — Requirements | 0 | 0 |
| R2 — Active Proof | 0 | 0 |
| R3 — AI Patterns | 0 | 0 |
| R4 — Handoff | 0 | 0 |
| R5 — Adjudication | READY_FOR_REVIEW | n/a |

Gate verdict: **PASS_FOR_HANDOFF**. Audits 15/16/37 PASS; 17 NOT_APPLICABLE (no execution-context claims beyond the recorded HEAD/branch which are mechanically verifiable from `git`).

---

## Out of scope (deliberately deferred)

- `nodes/contract.py` and the contract/planner split — roadmap item 4.
- `cto_orchestrator` adversarial pre-lane — separate issue (roadmap item 7).
- Tuning `temperature=0.2` and `max_tokens=8192` — requires extending the `claude --print` transport; tracked at the call site with a one-line comment.

---

## Where to look next

1. Read `prompts/metabuilder/35_system_gap_analyst.md` — the role contract.
2. Read `src/claude_pipeline/nodes/system_gap_analyst.py` — packet builder + lens validation.
3. Read `src/claude_pipeline/nodes/plan.py` — the `_render_gap_blocks` helper and `{gap_blocks}` placeholder.
4. Read `tests/test_system_gap_analyst.py` — behavioural coverage.
5. Read `reports/system-gap-analyst/NEXT_PROMPT_DECISION.md` — recommended next issue.
