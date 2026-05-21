# Prompt Contract Review

**Task area:** system-gap-analyst
**Verdict:** PROMPT_CONTRACT_PASS

## Prompts reviewed

| Prompt | File | Role | Notes |
|---|---|---|---|
| SGA system prompt (role) | prompts/metabuilder/35_system_gap_analyst.md | --append-system-prompt for the SGA node | Verbatim port from metabuilder; 8 lens names preserved. Required output schema explicitly documented (single JSON object, no markdown fences, `lens`/`gap`/`recommendation` fields). |
| SGA user packet | nodes/system_gap_analyst.py USER_PACKET_TEMPLATE | Per-invocation user packet | Includes issue header, intake JSON, research brief, codebase anchor, numbered lenses block, explicit JSON-only instruction. |
| Plan injection block | nodes/plan.py gap_block | Per-invocation insertion into plan_node prompt | Wording `MANDATORY ADDITIONAL DELIVERABLES` for blocking, `ADVISORY SUGGESTIONS` for advisory. Both surfaces explicitly tested. |

## Contract checks

- Role prompt and user packet agree on output shape (`blocking_gaps`, `advisory_gaps`, `summary`).
- `_format_gap` in plan.py defensively accepts `gap` OR `description` keys against LLM drift; documented in PLAN.md §7 risk 7.
- No prompt asks for behaviour that is not also constrained by the test surface.
- No conflict between system and user prompts (system prompt requires JSON-only output; user prompt repeats the instruction).

## Verdict

PROMPT_CONTRACT_PASS — system and user surfaces are coherent, tests bind to the contract, and downstream consumers know what shape to expect.
