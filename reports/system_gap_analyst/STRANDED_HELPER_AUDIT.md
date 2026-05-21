# Stranded helper audit

**Task area:** `system_gap_analyst`

## New helpers / private symbols introduced

| symbol | module | consumer |
|---|---|---|
| `_format_lenses` | `nodes/system_gap_analyst.py` | `build_gap_analysis_packet` |
| `_build_codebase_anchor` | `nodes/system_gap_analyst.py` | `build_gap_analysis_packet` |
| `_coerce_finding` (gap analyst) | `nodes/system_gap_analyst.py` | `system_gap_analyst_node` |
| `_load_system_prompt` | `nodes/system_gap_analyst.py` | `system_gap_analyst_node` |
| `_format_blocking_gaps` | `nodes/contract.py` | `build_contract_packet` |
| `_format_advisory_gaps` | `nodes/contract.py` | `build_contract_packet` |
| `_coerce_deliverable` | `nodes/contract.py` | `contract_node` |
| `_add_pipeline_nodes` | `graph.py` | `build_graph` + `render_mermaid` (de-dup helper) |
| `SYSTEM_PROMPT_PATH` (module const) | `nodes/system_gap_analyst.py` | `_load_system_prompt` |
| `LENSES` (module const) | `nodes/system_gap_analyst.py` | `_format_lenses`, tests |

## Stranded-helper check

- Every new `_*` private helper has exactly one or more callers within the same module or a test file.
- No helper exported then never used.
- `_add_pipeline_nodes` is the deliberate refactor that prevents `build_graph` and `render_mermaid` from drifting; before this commit they duplicated the topology — now they share it.

## Verdict

**PASS — no stranded helpers.** Every introduced private symbol has at least one live caller.
