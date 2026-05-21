# Consumer API proof audit

**Task area:** `system_gap_analyst`

## New consumer-facing symbols introduced

Public surfaces added by this commit (importable from `src/claude_pipeline/`):

| symbol | module | consumers |
|---|---|---|
| `system_gap_analyst_node` | `claude_pipeline.nodes.system_gap_analyst` | `graph.py` (build_graph + _add_pipeline_nodes) |
| `build_gap_analysis_packet` | `claude_pipeline.nodes.system_gap_analyst` | tests; also reusable by future surgical-revision logic |
| `LENSES` | `claude_pipeline.nodes.system_gap_analyst` | tests (cross-check of the 8 names) |
| `contract_node` | `claude_pipeline.nodes.contract` | `graph.py` |
| `build_contract_packet` | `claude_pipeline.nodes.contract` | tests; also reusable by surgical-revision logic |
| `GapFinding`, `GapAnalysis`, `ContractDeliverable`, `Contract` | `claude_pipeline.state` | not yet read by `plan_node` (deferred to next issue per HANDOFF.md); referenced by tests as fixtures |

## Each public symbol has a consumer

- `system_gap_analyst_node` → used in `graph.py`. ✓
- `contract_node` → used in `graph.py`. ✓
- `build_gap_analysis_packet` → used in `tests/test_system_gap_analyst.py`. ✓
- `build_contract_packet` → used in `tests/test_system_gap_analyst.py`. ✓
- `LENSES` → used in tests. ✓
- New typed dicts on `PipelineState` → present in state schema for runtime persistence; will be read by upgraded plan_node in next issue. Acceptable per port-spec step 4; STALE_FILE_REGISTER notes this explicitly.

## Verdict

**PASS — every newly added public symbol has at least one live consumer in the codebase or test suite.** No stranded exports.
