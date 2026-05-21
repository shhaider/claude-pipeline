# Cold Review — R3: AI Failure-Pattern Audit

**Reviewer:** R3 (AI Patterns)
**Cycle:** 1
**Verdict:** PASS — no blocking, no non-blocking findings.

---

## Mandate

R3 scans the change for the eight AI-failure-mode categories from `34_software_reasoning_reviewer.md` (the metabuilder reasoning reviewer): hot-path-bypass, fake-complete, interface-error, dependency-inversion, error-suppression, schema-drift, policy-bypass, anchor-drift.

---

## Category-by-category scan

| Category | Surface inspected | Finding |
|---|---|---|
| **hot-path-bypass** | The new node is inserted INTO the hot path between `research` and `plan` in both `build_graph` and `render_mermaid`. No bypass edge exists. | none |
| **fake-complete** | `system_gap_analyst_node` does not return `{"gap_analysis": ...}` unless it has parsed real JSON with valid lens slugs from `run_claude`. The "no system prompt found" path returns an error, not a no-op success. `_render_gap_blocks` only emits MANDATORY when blocking_gaps is non-empty — empty-arrays don't claim "covered". | none |
| **interface-error** | `state.py` exposes `GapAnalysisItem`/`GapAnalysis` as `TypedDict(total=False)`, matching the file's existing convention. `plan_node` reads `state.get("gap_analysis", {})` (defensive). The packet builder uses `state.get(...)` everywhere. No `KeyError`-prone direct access. | none |
| **dependency-inversion** | The node depends on `run_claude`, `extract_json`, and `PipelineState`/`GapAnalysis` — same dependencies as the existing `intake.py`, `research.py`, `plan.py`. No new dependency inversion. | none |
| **error-suppression** | `_coerce_gap_items` distinguishes structural failures (raises `ValueError`, caught at node boundary → `error` field) from soft failures (unknown lens → log warning + drop). This is deliberate, not suppression: the operator sees the warning, and the structural-failure path is loud. The node-boundary `except (ValueError, json.JSONDecodeError)` returns `{"error": ...}` rather than swallowing — same pattern as `plan_node` and `intake_node`. | none |
| **schema-drift** | The 8 canonical lens slugs are declared in `CANONICAL_LENS_SLUGS` in the node module and reproduced verbatim in the system prompt, the user packet (via `LENSES` table), and the test set (via `CANONICAL_SLUGS` constant). `test_canonical_lens_slugs_match_node_constant` binds the test-set version to the production frozenset, so a future drift would fail tests. | none |
| **policy-bypass** | No policy table is touched. The node honours the task prompt's "do not extend `run_claude` to expose temp/max_tokens" rule — only `model=...` is set; a one-line comment at the call site documents the limitation. | none |
| **anchor-drift** | The codebase-anchor block in `_build_gap_analysis_packet` gracefully degrades when `research_anchor` is absent (covered by `test_packet_omits_anchor_gracefully_when_missing`) and prefers structured `sources_consulted`/`implementation_details` when present (`test_packet_uses_structured_anchor_when_present`). | none |

---

## Hindsight check

If I were the next reviewer rereading this change after one cycle of dogfooding:

- Would I be surprised by anything? No. The injection point in `plan_node` is the most reasonable target until the contract/planner split lands, and that future migration is explicitly called out in both the source comments and the README.
- Would I add anything? No within scope. The temp/max_tokens transport upgrade is correctly out of scope and tracked.

---

## Findings

- **Blocking:** none
- **Non-blocking:** none

## Verdict

PASS.
