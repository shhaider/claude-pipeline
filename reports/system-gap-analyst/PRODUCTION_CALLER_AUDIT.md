# Production Caller Audit

**Task area:** system-gap-analyst
**Verdict:** PRODUCTION_CALLER_AUDIT_PASS

## Active production wiring

The new node `system_gap_analyst` is registered into the LangGraph state machine in both `build_graph` (the runtime compilation path used by the CLI) and `render_mermaid` (used by `claude-pipeline graph`). The compiled graph render in `mermaid_render.txt` shows both inbound (`research --> system_gap_analyst`) and outbound (`system_gap_analyst --> plan`) edges, proving the node is on the active production path between research and plan, not a stranded helper.

## Downstream caller (plan_node)

`plan_node` reads `state.get("gap_analysis")` and unconditionally formats `{gap_block}` into its prompt template. When `gap_analysis` is absent the gap_block resolves to `""`, preserving pre-SGA-era behaviour for resume/replay scenarios. The substring `MANDATORY ADDITIONAL DELIVERABLES` only appears when blocking_gaps is non-empty (test_blocking_gaps_inject_as_mandatory verifies, test_advisory_gaps_not_marked_mandatory verifies the negative).

## Verdict

PRODUCTION_CALLER_AUDIT_PASS — node is in the production graph, downstream consumer is wired, and the wiring is exercised by tests.
