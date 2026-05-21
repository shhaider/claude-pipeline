# 18 — Gate profile selection

## Declared profile

| field | value |
|---|---|
| `selected_profile` | **GATE_FULL** |
| `risk_tier` | **D2** |
| `task_kind` | **prompt_authoring** |

## Why GATE_FULL

The change authors a new role prompt file (`prompts/metabuilder/35_system_gap_analyst.md`) that will drive an LLM call. Per the gate judge's first-cycle citation of Gate 5.4: any commit that adds or modifies a prompt file falls under `prompt_authoring` task_kind, which mandates minimum GATE_FULL. We honor that classification rather than appeal it.

## Why D2 risk tier (not D3)

Risk tier reflects blast radius if the change is wrong. This change is **D2 (moderate)** rather than D3 (high) because:

- **Additive only.** No existing nodes' behaviour changes. `research`, `intake`, `plan`, `code`, `verify`, `pr` are untouched semantically; the topology only inserts new nodes between `research` and `plan`.
- **No production runtime is wired to the new graph yet.** `cli.py` calls `build_graph(...)` which now returns a graph that includes `system_gap_analyst` and `contract` nodes. But the new nodes only execute when a real pipeline run is launched against a real issue. In test invocations, no LLM call is made (tests are pure-python against packet builders).
- **plan_node degrades gracefully.** It reads `state.get("research_brief", ...)` and never touches `state["contract"]` or `state["gap_analysis"]`, so an empty contract / missing gap_analysis cannot break it.
- **No migrations, no schema changes, no secrets, no auth path, no hot loop, no concurrency primitives.**
- **No SDK dependencies added.** `dependencies` in `pyproject.toml` unchanged.

If this were touching `claude.py` (the subprocess transport) or `verify.py` (the gate enforcer), or wiring something irreversible into `cli.py`, it would be D3.

## Why prompt_authoring (not normal_impl)

The new prompt is the dispositive artifact — it's what the model will execute against. Even though the bulk of LOC is Python (node + packet builder + tests), the value of the change is the verbatim port of the metabuilder role + the integration seam for blocking/advisory gaps. `19_PROMPT_CONTRACT_REVIEW` is therefore required and produced (`PROMPT_CONTRACT_REVIEW.md`).

## Reasoning

The judge's first-cycle FAIL was correct on process grounds (no gate package). The substantive code was correct except for the unsupported `claude --max-tokens` / `--temperature` flags, which the judge flagged in fix #6 and which this cycle removes. With the profile honestly selected (GATE_FULL, not GATE_LITE; D2, not D3 because additive), and the package now produced, the pre-PASS barrier is reachable.
