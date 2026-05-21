# Step 13 — Blocked Handoff

## First — write CURRENT_STATE.yaml

Write to `reports/<task_area>/CURRENT_STATE.yaml`:
```yaml
current_state: BLOCKED_HANDOFF_COMPLETE
gate_completed: true
final_gate_verdict: FAIL_BLOCKED_REQUIRES_HUMAN
handoff_type: BLOCKED
handoff_completed_at: <ISO timestamp>
remaining_human_blocked_blockers: [list]
```

---

You are here because one of the following occurred:

- Evidence Adequacy Assessment returned `EVIDENCE_BLOCKED_REQUIRES_HUMAN`
- Evidence Consistency Preflight found blockers that cannot be fixed within scope
- Enforcement Authority Audit (step 14) returned `FAIL_BLOCKED_REQUIRES_HUMAN`
- Reviewer 5 returned `BLOCKED` or `STOP_AND_REDESIGN`
- Maximum correction cycles (5) have been reached without `PASS_FOR_HANDOFF`
- (Gate 5.3) FINAL_PACKET_AUDITOR (state 37) returned `HUMAN_DECISION_REQUIRED`

Do not continue attempting to fix. Return the blocked handoff now.

---

## Required blocked handoff content

Your blocked handoff must include all of the following:

### Why you are blocked

State exactly which condition above applies and which file/step sent you here.

### All remaining blockers

For each blocker:

```
BLOCKER: [name]
Source: [which reviewer or which preflight check]
Classification: HUMAN_BLOCKED / MAX_CYCLES_REACHED / EVIDENCE_BLOCKED / CONSISTENCY_BLOCKED
Evidence: [exact quote or file reference]
Why it cannot be autofixed: [one sentence]
```

### Fixes already attempted (if applicable)

For each prior cycle:

```
Cycle [N]:
- Blockers found: [list]
- Fixes applied: [list]
- Outcome: [still blocked / different blocker appeared]
```

### Enforcement Authority blockers (if applicable)

If the block originated from `14_ENFORCEMENT_AUTHORITY_AUDIT.md`, include:

```
ENFORCEMENT_BLOCKER: [name]
Protected action: [what action was claimed to be prevented]
Bypass path found: [how the unsafe action can still occur]
Advisory vs authoritative: [classification]
Evidence: [raw output or git log showing bypass]
Why it cannot be autofixed: [one sentence — typically: requires architectural change or changes to a system outside current scope]
```

### Current package state

- Final branch
- Final HEAD SHA
- Final `git status --short`
- What IS complete and evidenced
- What is NOT complete or evidenced

### Next allowed human instruction

State explicitly what the user must decide or do before work can resume. Do not leave this vague.

Examples:
- "User must decide whether [X] is within scope before this blocker can be resolved."
- "Fixing this requires touching [Y], which was listed as forbidden. User must authorize or remove the restriction."
- "Reviewer 5 returned STOP_AND_REDESIGN. The design problem is [Z]. User must decide whether to redesign or accept the current approach with known gaps."
- "Maximum cycles reached. The remaining blockers are [list]. User must either expand scope or accept the current state."

---

## Update the cycle tracker

Record the final blocked status in `reports/<task_area>/CYCLE_TRACKER.md`.

---

## Include in the blocked package

- `CYCLE_TRACKER.md`
- `COLD_REVIEW_ADJUDICATION.md` from the most recent cycle
- `EVIDENCE_ADEQUACY_ASSESSMENT.md` if one was written
- `EVIDENCE_CONSISTENCY_REGISTER.md` if one was written
- `ENFORCEMENT_AUTHORITY_AUDIT.md` if one was written
- Any cold review reports from the most recent cycle
- This blocked handoff document

Return the blocked handoff to the user.

---

## Gate 4.1 — Overclaim taxonomy for blocked handoffs

Even blocked handoffs must use the correct outcome label. Add one of the following to the "Current package state" section:

| Label | When to use in a BLOCKED handoff |
|---|---|
| `PREPLANNING_BLOCKED` | Preplanning package is incomplete or ambiguous |
| `PACKAGE_BLOCKED` | Work package cannot proceed |
| `MERGE_NOT_VERIFIED` | Branch was submitted but merge proof is absent |
| `INFRASTRUCTURE_READY_NOT_WIRED` | Code exists and tests pass, but wiring was blocked |
| `TEST_HELPER_ONLY` | Only test infrastructure was added; production wiring blocked |

**Hard rule:** A blocked handoff must not say "BLOCKED" alone. It must use one of these labels to describe what kind of blocked state the work is in. This allows downstream agents to reason about partial reuse of the blocked package.
