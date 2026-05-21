# Production caller audit

**Task area:** `system_gap_analyst`

## Claim under audit

The new `system_gap_analyst_node` and `contract_node` are reachable from a real production caller (i.e. they will be executed by a real pipeline run, not stranded helpers).

## Caller path

```
src/claude_pipeline/cli.py
  → calls build_graph() in src/claude_pipeline/graph.py
  → build_graph() registers system_gap_analyst + contract as nodes
    (graph.py: _add_pipeline_nodes adds both with g.add_node)
  → and wires them into the topology
    (graph.py: g.add_edge("research", "system_gap_analyst"),
                g.add_edge("system_gap_analyst", "contract"),
                g.add_edge("contract", "plan"))
  → compiled graph is returned; CLI invokes graph.invoke(initial_state)
  → LangGraph dispatches each node by name in topological order;
    system_gap_analyst_node and contract_node WILL be called
    on every real pipeline run that reaches research.
```

## Verification

- `Grep` for `system_gap_analyst_node` in `src/`: import in `graph.py:18`, used in `_add_pipeline_nodes`. Reachable from `build_graph`.
- `Grep` for `contract_node` in `src/`: import in `graph.py:17`, used in `_add_pipeline_nodes`. Reachable from `build_graph`.
- `Grep` for `build_graph` in `src/`: called from `cli.py` (cli command entry point).
- Mermaid render confirms both nodes are on the path from START to END.

## Live-behavior status

`live_behavior_claimed = false` for this issue.

The issue's acceptance criteria are met by topology, packet construction, and unit-test evidence; no end-to-end live LLM run against a real GitHub issue is claimed by this commit. That is consistent with the architectural rule's "A/B every escalation" — live A/B comparison is the next-issue's scope.

## Verdict

**PASS — production caller verified by static reachability.** No live-run claim is being made; if a future issue claims one, it must add evidence of a real `claude-pipeline run` invocation.
