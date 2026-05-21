# Stranded Helper Audit

**Task area:** system-gap-analyst
**Verdict:** STRANDED_HELPER_AUDIT_PASS

## New symbols inspected

| Symbol | File | Consumer | Stranded? |
|---|---|---|---|
| `system_gap_analyst_node` | nodes/system_gap_analyst.py | imported by graph.py and registered as a graph node | NO |
| `LENSES` (module-level tuple) | nodes/system_gap_analyst.py | used inside `system_gap_analyst_node` to build the lenses_block; also referenced in tests | NO |
| `USER_PACKET_TEMPLATE` | nodes/system_gap_analyst.py | used inside `system_gap_analyst_node` | NO |
| `OPUS_MODEL` | nodes/system_gap_analyst.py | passed to `run_claude(model=OPUS_MODEL, ...)` | NO |
| `PROMPT_PATH` | nodes/system_gap_analyst.py | read inside `system_gap_analyst_node` | NO |
| `_build_codebase_anchor` | nodes/system_gap_analyst.py | called by `system_gap_analyst_node` | NO |
| `GapAnalysis` (TypedDict) | state.py | declared on PipelineState and consumed by both producer (SGA node return) and consumer (plan_node read) | NO |
| `_format_gap` | nodes/plan.py | called by `plan_node` for both blocking and advisory branches | NO |

## Verdict

STRANDED_HELPER_AUDIT_PASS — no new symbol is unreferenced; every helper has at least one active caller in the production path.
