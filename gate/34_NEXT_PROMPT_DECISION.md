# Step 34 — Next Prompt Decision

**State machine:** Write `current_state: NEXT_PROMPT_DECISION_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for D2+ packages** (GATE_STANDARD and GATE_FULL).

**Skip for GATE_LITE / D0 / D1.** Produce `NEXT_PROMPT_DECISION_NOT_APPLICABLE.md`.

---

## Why this step exists

After a task completes, the next prompt may be stale. The original next-phase prompt was written before this task ran. Now that the task has completed, the gate has new information:
- What was actually changed (vs. what the prompt assumed would be changed)
- What evidence exists (vs. what the prompt assumed would exist)
- What blockers remain (vs. the clean handoff the prompt assumed)
- What the CTO/operator review revealed (adjacent bugs, scope changes, simplification opportunities)

This step produces a decision artifact that the orchestrator can use to determine the correct next action.

---

## Output file

Copy `NEXT_PROMPT_DECISION_TEMPLATE.md` to `reports/<task_area>/NEXT_PROMPT_DECISION.md`.

---

## Required questions

### Q1 — Continue / correction / split / defer / stop?

| Option | When to use |
|---|---|
| `CONTINUE` | The next prompt is still valid; proceed as planned |
| `CORRECTION` | The next prompt needs revision before it can be used; return to prompt-architect |
| `SPLIT` | The next prompt is too large given what this task revealed; split it into two or more nodes |
| `DEFER` | The next prompt depends on a condition that is not yet met; park it until the condition is met |
| `STOP` | The work reveals that the planned next phase is the wrong approach; escalate to operator |

### Q2 — Recommended model/tier/effort for next step

Specify:
- Model: [claude-opus / claude-sonnet / claude-haiku / or "auto"]
- Effort tier: [D0/D1/D2/D2-hot/D3/D4]
- Gate profile: [GATE_LITE / GATE_STANDARD / GATE_FULL / GATE_FULL_PLUS_DOMAIN_ADDENDUM]
- Estimated complexity: [LOW / MEDIUM / HIGH]

### Q3 — Exact next allowed action

One sentence specifying exactly what the next agent should do first.

Examples:
- "Read `P02_wire_caller.md` and implement the production caller for `userRepo.findById`."
- "Fix the `INFRASTRUCTURE_READY_NOT_WIRED` finding before proceeding to the next phase."
- "Run the migration runner proof check that was blocked by scope in this task."

### Q4 — Forbidden next actions

One or more sentences specifying what the next agent must NOT do.

Examples:
- "Do not attempt to merge until the production caller is proven."
- "Do not modify `runtime_lane_registry.js` — that is a hot file requiring separate GATE_FULL authorization."
- "Do not start Phase 3 until Phase 2 has a passing `DOWNSTREAM_READY` verdict."

---

## Hard rule

A task can pass the gate but the previous next prompt may still be stale. The gate passage does not guarantee the next prompt is correct. Always check the next prompt for staleness given what this task actually produced.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Decision artifact written | `NEXT_PROMPT_DECISION_COMPLETE` | `GATE_VERDICT_ISSUED` |
