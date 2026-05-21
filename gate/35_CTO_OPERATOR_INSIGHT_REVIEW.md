# Step 35 — CTO / Operator Insight Review

**State machine:** Write `current_state: CTO_OPERATOR_INSIGHT_REVIEW_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for D2-hot / D3 / D4.** Optional for D2.

**Skip for GATE_LITE.** Produce `CTO_OPERATOR_INSIGHT_REVIEW_NOT_APPLICABLE.md`.

---

## What this step is

This is NOT another reviewer. This is an outer-frame lens. The five cold reviewers (R1–R5) look inside the package for evidence quality and correctness. The CTO/Operator insight review looks at the package from outside — asking: "Given what just happened, what do we learn about the project, the process, and the next direction?"

The five reviewers are adversarial about the evidence. The CTO review is thoughtful about the trajectory.

---

## Output file

Copy `CTO_OPERATOR_INSIGHT_REVIEW_TEMPLATE.md` to `reports/<task_area>/CTO_OPERATOR_INSIGHT_REVIEW.md`.

---

## Required questions

### Q1 — What did this task reveal?

Not just "the tests pass" — what did the process of doing this task teach you about:
- The codebase (unexpected complexity, hidden dependencies, brittle areas)
- The architecture (design tensions, over-engineering, under-engineering)
- The process (what went wrong, what worked, where time was wasted)
- The prompt quality (was the task well-specified, or did it require significant interpretation)

### Q2 — Does it change the next prompt?

Given what this task revealed, is the pre-written next prompt still the right thing to build?

- Is there a simpler approach that achieves the same goal?
- Is there prior art (existing library, existing module) that makes this unnecessary?
- Did this task reveal that the next phase depends on something that is not yet ready?
- Did this task reveal that the next phase was already done by a different sprint?

### Q3 — Does it change the roadmap?

Did this task reveal:
- A new required task that was not in the roadmap (add it now)
- A roadmap item that is now completed (mark it done)
- A roadmap item that should be deleted (wrong approach, now superseded)
- A dependency ordering change (B must come before A, not after)

### Q4 — Adjacent bugs revealed

During this task, did you observe:
- A bug in a nearby module that was not part of the task scope
- An error or warning that was not the focus of this task but indicates a real problem
- A test that is obviously wrong but passing for the wrong reason

List each. Do not fix them — note them for follow-up.

### Q5 — Requires human decision?

Is there anything in this task's outcome that requires a human (operator) to make a decision before the next phase can proceed?

- An ambiguous design choice that affects multiple future sprints
- A security concern that needs security review
- A scope expansion request revealed by the task
- A conflict between two roadmap items that both look correct

### Q6 — Should we stop?

Given everything: should this line of work continue as planned, or should it pause?

Reasons to stop:
- The approach is fundamentally wrong (discovered during implementation)
- The task reveals that the overall architecture needs rethinking
- The effort-to-value ratio has shifted unfavorably
- A simpler alternative has been discovered that makes this unnecessary

### Q7 — Should work be simplified, deleted, or replaced by prior art?

Specifically:
- Is there a well-maintained open-source library that does what this code does?
- Is there a pattern in the existing codebase that already solves this problem?
- Is the current implementation 3x more complex than necessary?

---

## Hard rule

This step must be honest. If the task went well and there is nothing remarkable to note, say so briefly (3 sentences). If the task revealed problems, this is the place to document them — not to bury them in the five reviewer reports.

---

## Routing

Write `current_state: CTO_OPERATOR_INSIGHT_REVIEW_COMPLETE` to CURRENT_STATE.yaml.

Route to: `34_NEXT_PROMPT_DECISION.md`
