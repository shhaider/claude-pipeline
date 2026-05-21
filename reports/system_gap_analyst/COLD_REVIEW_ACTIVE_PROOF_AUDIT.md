# R2 — Design review (cold)

**Reviewer perspective:** Architecture / shape / coupling. Does the change live in the right places, with the right seams, at the right granularity?

## Module placement

- `nodes/system_gap_analyst.py` — correct. Mirrors the existing pattern (`nodes/research.py`, `nodes/plan.py`, etc.): one file per LangGraph node, exports a `_node(state) -> dict` function.
- `nodes/contract.py` — correct. New node sits in `nodes/`, consumes from upstream state, produces a structured payload for downstream.
- `prompts/metabuilder/35_system_gap_analyst.md` — correct. New directory tree but matches the path called out in the issue body and in `docs/metabuilder-port-spec.md`.

## Seam between system_gap_analyst and contract

The gap analyst writes `state["gap_analysis"]`. The contract_writer's `build_contract_packet` reads `state.get("gap_analysis", {})` and surfaces blocking/advisory lists in distinct sections with literal "MANDATORY" vs "NOT mandatory" framing.

- **Strength:** the seam is observable from a unit test without touching `claude` (the packet builder is a pure function). Tests verify the contract gets the gaps — they don't depend on the analyst LLM call succeeding.
- **Strength:** advisory and blocking are kept as separate lists end-to-end (not collapsed into a single severity-tagged list at the boundary), so a downstream contract writer cannot accidentally treat advisory as blocking.
- **Caveat (minor):** the source-of-truth for the 8 lens names lives in TWO places: `prompts/metabuilder/35_system_gap_analyst.md` and `nodes/system_gap_analyst.py:LENSES`. A future drift between the two would silently weaken the gate. Mitigated by `test_gap_packet_lenses_are_the_metabuilder_eight` enforcing the set in code, but the prompt file is not asserted against. **Suggested follow-up:** add a test that greps each lens name out of the prompt file.

## Codebase anchor block

`_build_codebase_anchor` reads `sources_consulted` and `implementation_details` out of the research brief when it's JSON-shaped, falls back to "research brief embedded as plain context" otherwise.

- **Strength:** doesn't require research_node to be upgraded first. Current research_node returns markdown; codebaseAnchor degrades cleanly.
- **Strength:** preserves the metabuilder semantics — when research_node is upgraded to emit JSON (per `docs/metabuilder-port-spec.md` step 3), the anchor block automatically becomes richer without any change to this node.

## Graph wiring

`_add_pipeline_nodes` was factored out so `build_graph` and `render_mermaid` use the same topology constructor. Prevents the previous code's drift risk (the topology was duplicated in both functions).

## State typing

New typed dicts: `GapFinding`, `GapAnalysis`, `ContractDeliverable`, `Contract`. All use `total=False` matching the file's existing convention. Field names match the metabuilder shape called out in the port spec.

## Subprocess / LLM transport

After the cycle-1 fix, `run_claude` is invoked with the supported flags only (`--model`, `--append-system-prompt`). The `--max-tokens` / `--temperature` flags previously passed via `extra_args` would have caused `claude` to exit non-zero (verified by reading `claude --help` output). This was the most material bug in cycle 1. Now removed.

## What this design intentionally does NOT do

- Does not modify `plan_node` to consume `contract.deliverables`. The plan still reads `research_brief` only. The seam exists (state carries `contract`), but the plan_node upgrade is a separate issue per the port spec's roadmap step 4. STALE_FILE_REGISTER notes this explicitly.
- Does not introduce SDK-level parameter control. The CLI limitation is documented; an SDK migration is a separate concern.
- Does not refactor any existing node. Additive only.

## Verdict (R2)

**PASS.** Shape is consistent with the file's existing patterns. Seams are observable. Drift risks identified and surfaced (lens-name dual-source). One suggested follow-up; not blocking.
