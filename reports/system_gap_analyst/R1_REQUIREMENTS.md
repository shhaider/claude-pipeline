# R1 — Requirements review (cold)

**Reviewer perspective:** I have not seen the implementation. I read the issue body and check what the work claims to deliver against what it actually delivers.

## Issue acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | `src/claude_pipeline/nodes/system_gap_analyst.py` exists with `system_gap_analyst_node(state) -> dict` | **PASS** | File present; `def system_gap_analyst_node(state: PipelineState) -> dict:` at line ~200 of the module. Returns `{"gap_analysis": analysis, "error": None}`. |
| 2 | Graph topology shows `research → system_gap_analyst → contract` in the Mermaid render | **PASS** | `raw/mermaid.txt` shows edges `research --> system_gap_analyst;`, `system_gap_analyst --> contract;`, `contract --> plan;`. |
| 3 | Contract node's user packet includes blocking gaps from `gap_analysis` when present | **PASS** | `build_contract_packet` calls `_format_blocking_gaps(blocking)` which emits the `MANDATORY ADDITIONAL DELIVERABLES` block. Tested by `test_blocking_gaps_injected_as_mandatory_into_contract_packet`. |
| 4 | `pytest -v tests/test_system_gap_analyst.py` passes (≥4 tests) | **PASS** | 9 tests, all PASSED. See `raw/pytest.txt`. |
| 5 | Existing v0.3 tests (54) still pass | **N/A** | Repo was at v0.1 with 0 existing tests. Vacuously satisfied; full suite is now 9 tests. The issue body's "54 tests from v0.3" assumes a state the repo is not in. |
| 6 | README architecture diagram updated | **PASS** | `README.md:40-58` updated with new pipeline diagram + adversarial-pre-lane explainer paragraph. |

## Out-of-scope claims (issue body)

| # | Claim | Honored? |
|---|---|---|
| 1 | Do not port `cto_orchestrator` lane | **YES** — no cto_orchestrator code present. |
| 2 | Do not change tier routing | **YES** — no changes to `claude.py` or any tier-routing layer (none exists yet). |
| 3 | Do not touch verify ladder | **YES** — `verify.py` untouched (verified via diff). |

## Required builders / packet content (issue body §1)

| Required | Present? |
|---|---|
| Intake decisions in packet | YES — `## Intake decisions` block with JSON-dumped intake |
| Research brief in packet | YES — `## Research brief` block |
| `codebaseAnchor` block (from research's `sources_consulted` + `implementation_details`) | YES — `_build_codebase_anchor` extracts those fields when research output is JSON-shaped, falls back to plain context when it's markdown |
| 8 named lenses spelled out for the model | YES — `_format_lenses()` emits all 8 by name with descriptions |
| Output JSON schema `{blocking_gaps, advisory_gaps, summary}` | YES — packet's output-schema block matches; node parses into typed `GapAnalysis` |
| Fresh session (no resume) | YES — `run_claude` is called without any session-resume argument |
| Tier 3 (Opus) | YES — `model="claude-opus-4-7"` |
| Temperature 0.2 | **PARTIAL** — flag not exposed by `claude --print`; documented as known limitation in docstring + `claude_help.txt` |
| Max tokens 8192 | **PARTIAL** — same limitation |

## Required state field (issue body §3)

`gap_analysis: dict` added to `PipelineState`. Present in `state.py`. Persisted because LangGraph persists all state fields after every node by default.

## Required tests (issue body §4)

| Test | Present? |
|---|---|
| (a) packet contains all 8 lenses | YES — `test_gap_packet_contains_all_eight_lenses` |
| (b) packet includes intake + research | YES — `test_gap_packet_includes_intake_decisions` + `test_gap_packet_includes_research_brief` |
| (c) blocking gaps injected into contract input | YES — `test_blocking_gaps_injected_as_mandatory_into_contract_packet` |
| (d) advisory gaps present but not mandatory | YES — `test_advisory_gaps_injected_as_suggestions_not_mandatory` |

Plus 5 bonus tests covering: lens-set equality, issue identifier presence, empty-gaps absence path, no-gap_analysis-key backwards compat.

## Verdict (R1)

**PASS with two acknowledged partials.** The two partials (`temperature`/`max_tokens` not set) are surfaced honestly in the code docstring and in `claude_help.txt`; they are a CLI-surface limitation, not an implementation omission. R4 (risk) addresses whether this matters substantively.
