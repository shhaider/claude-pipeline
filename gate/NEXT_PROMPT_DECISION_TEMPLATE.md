# Next Prompt Decision

**Task ID:** [task_id]
**Task area:** [task_area]
**Decision made at:** [ISO timestamp]

---

## What this task actually produced

Summarize (3–5 bullet points):
- Changed: [what files/behaviors actually changed]
- Evidence: [what proof exists vs. what was assumed]
- Blockers carried forward: [if any]
- Surprises: [anything the task revealed that the prompt did not anticipate]

---

## Q1 — Continue / correction / split / defer / stop?

**Decision:** CONTINUE | CORRECTION | SPLIT | DEFER | STOP

**Rationale:** [one paragraph]

If CORRECTION:
- What must change in the next prompt before it can be used?
- Return to: [prompt-architect name]

If SPLIT:
- Split into how many nodes? [N]
- Node 1: [description]
- Node 2: [description]

If DEFER:
- Condition that must be met before this proceeds: [condition]
- Where it is tracked: [roadmap entry / ticket]

If STOP:
- Why this approach is wrong: [one paragraph]
- What the operator must decide: [decision required]

---

## Q2 — Recommended model/tier/effort for next step

| Item | Value |
|---|---|
| Model | claude-opus / claude-sonnet / claude-haiku / auto |
| Risk tier | D0 / D1 / D2 / D2-hot / D3 / D4 |
| Gate profile | GATE_LITE / GATE_STANDARD / GATE_FULL / GATE_FULL_PLUS_DOMAIN_ADDENDUM |
| Estimated complexity | LOW / MEDIUM / HIGH |
| Rationale | [one sentence] |

---

## Q3 — Exact next allowed action

```
[One specific sentence: "Read X and do Y."]
```

---

## Q4 — Forbidden next actions

1. [forbidden action and why]
2. [forbidden action and why]

---

## Stale next-prompt check

**Was there a pre-written next prompt?** YES / NO

If YES:
- Next prompt file: [path]
- Still valid? YES / NO
- If NO, what needs to change: [list changes]

---

## Summary

```yaml
next_action: CONTINUE | CORRECTION | SPLIT | DEFER | STOP
recommended_model: claude-opus | claude-sonnet | claude-haiku | auto
recommended_risk_tier: D0 | D1 | D2 | D2-hot | D3 | D4
recommended_gate_profile: GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS_DOMAIN_ADDENDUM
next_allowed_action: "[exact one sentence]"
forbidden_next_actions:
  - "[forbidden action]"
```
