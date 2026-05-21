# Downstream consumer readiness

**Task area:** `system_gap_analyst`

## Identified downstream consumers

1. **`plan_node`** (`src/claude_pipeline/nodes/plan.py`) — receives the augmented state after `contract_node`.
   - **Readiness:** TOLERANT. Reads only `state.get("research_brief", ...)` and `state.get("intake", {})`. Does not touch the new `contract` or `gap_analysis` keys. Adding them to state cannot break it.
   - **Future upgrade (separate issue):** wire `plan_node` to read `state["contract"].deliverables` and produce stages per deliverable. Tracked in `NEXT_PROMPT_DECISION.md`.

2. **`code_node`, `verify_node`, `pr_node`** (downstream of plan) — unchanged. They read `state["plan"]` and `state["intake"]`; the new state keys are invisible to them.

3. **LangGraph SQLite checkpointer** — persists every state key. New keys (`gap_analysis`, `contract`) are TypedDict shapes and serialize via the default channel. No checkpointer config change needed.

4. **`render_mermaid()` (docs / debugging)** — already updated to include the new nodes; verified by `raw/mermaid.txt`.

## Readiness verdict per consumer

| consumer | status |
|---|---|
| `plan_node` | READY (tolerant; doesn't consume new fields yet, doesn't break) |
| `code_node` | READY (unaffected) |
| `verify_node` | READY (unaffected) |
| `pr_node` | READY (unaffected) |
| SQLite checkpointer | READY (default serialization works) |
| `render_mermaid()` | READY (already updated) |

## Verdict

**PASS — `downstream_consumer_readiness`.** Every downstream consumer is either upgraded or tolerantly ignores the new state fields. No breaking change.
