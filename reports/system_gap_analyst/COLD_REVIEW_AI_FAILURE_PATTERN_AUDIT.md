# R3 — Test adequacy review (cold)

**Reviewer perspective:** Are the tests load-bearing? Would they fail in the right places if the code was wrong?

## Inventory

`tests/test_system_gap_analyst.py` — 9 tests, all green (`raw/pytest.txt`, `EXIT_CODE:0`).

| # | Test | What it pins |
|---|---|---|
| 1 | `test_gap_packet_contains_all_eight_lenses` | All 8 lens names appear verbatim in the user packet — if one is dropped, this fails. |
| 2 | `test_gap_packet_lenses_are_the_metabuilder_eight` | The `LENSES` table contains exactly the 8 metabuilder lens names (no typos, no additions, no drift). |
| 3 | `test_gap_packet_includes_intake_decisions` | Intake values (task_type, complexity_tier, risk_flag, scope_plan) reach the packet. |
| 4 | `test_gap_packet_includes_research_brief` | Research brief text reaches the packet under the right heading. Codebase-anchor block present. |
| 5 | `test_gap_packet_includes_issue_identifier` | `Issue #N` + issue title surfaced so the model knows what it's analyzing. |
| 6 | `test_blocking_gaps_injected_as_mandatory_into_contract_packet` | Each blocking gap's `gap`, `recommendation`, `lens` reaches the contract packet under the MANDATORY heading; `gap_analysis_blocking` source-tag is in the output schema. |
| 7 | `test_blocking_gaps_absent_when_gap_analysis_empty` | When gap_analysis has empty arrays, the MANDATORY/Advisory sections are not emitted (prevents empty-header noise). |
| 8 | `test_contract_packet_works_without_gap_analysis_key` | Resumed runs from before the upgrade don't break the contract builder. |
| 9 | `test_advisory_gaps_injected_as_suggestions_not_mandatory` | Advisory text appears AFTER the mandatory block; literal "NOT mandatory" appears; "suggestion" present in framing. |

## Adequacy checklist

| Criterion | Status | Notes |
|---|---|---|
| **Relevant** | PASS | Tests target the exact functions the production graph uses (`build_gap_analysis_packet`, `build_contract_packet`). |
| **Real-path** | PASS | Tests import the production modules. No mocks, no doubles. |
| **Behavioral** | PASS | Assertions check observable substring presence and ordering — not implementation shape (no `_private` symbol inspection). |
| **Specific** | PASS | Each test would FAIL with a localized error if a specific concern broke: a missing lens, a dropped recommendation, a mis-ordered section. Not boilerplate "code doesn't crash" tests. |
| **Failure-aware** | PASS | Tests #7 + #8 cover the "no gaps" and "no gap_analysis key" paths — the easy-to-regress edge cases. |
| **Repeatable** | PASS | Pure-python; no fixtures with hidden state; no external services. Re-runs are deterministic. |
| **Raw-output-backed** | PASS | `raw/pytest.txt` captures the full output including `EXIT_CODE:0`. |

## What tests intentionally do NOT cover

- The actual LLM call inside `system_gap_analyst_node` and `contract_node` is not tested with a stub. Reasoning: the issue says "No LLM calls in tests — use fixture state dicts." The node functions are thin wrappers around `run_claude` + JSON parsing; the parsing logic is exercised indirectly via `_coerce_finding` defaults but not asserted. **Acceptable risk** — the failure mode (claude returns malformed JSON) is bounded by the `extract_json` helper and the node's explicit `error` return.
- The Mermaid render is not asserted in unit tests. Reasoning: it's captured in `raw/mermaid.txt` and inspected by R1. A unit test that asserts mermaid string contents would be brittle to LangGraph rendering changes.

## Verdict (R3)

**PASS.** Tests are load-bearing, behavioral, and cover the required four cases plus five honest edge cases. The two intentional gaps (LLM-call coverage, mermaid assertion) are documented and reasonable.
