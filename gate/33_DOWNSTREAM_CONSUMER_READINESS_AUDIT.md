# Step 33 — Downstream Consumer Readiness Audit

**State machine:** Write `current_state: DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_FULL** before declaring any next phase ready.

**Optional for GATE_STANDARD.**

**Skip for GATE_LITE.** Produce `DOWNSTREAM_CONSUMER_READINESS_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

"Phase 1 complete — ready for Phase 2" is a common claim that is often wrong. The next phase may depend on:
- A specific API shape that was changed at the last minute
- A database column that was renamed
- A module export that was reorganized
- A config key that was removed

This audit forces the agent to verify that the next-phase consumer can actually start given the current state of the package.

---

## Output file

Copy `DOWNSTREAM_CONSUMER_READINESS_TEMPLATE.md` to `reports/<task_area>/DOWNSTREAM_CONSUMER_READINESS.md`.

---

## Checks

### Check 1 — Identify next-phase consumers

What code, task, agent, or process depends on the output of this task?
- The next sprint's implementation node
- A downstream service that will import this module
- A test suite that will run against the new API
- A human reviewer who will make a decision based on this package

### Check 2 — Verify API contract matches what consumer expects

If the next phase has a known prompt or spec:
1. Does it reference functions/methods by the names they were actually given?
2. Does it expect a module at the path where it was actually placed?
3. Does it expect specific fields in the API response that are actually present?

### Check 3 — Verify no breaking changes were introduced

For any existing consumer of the changed module:
1. Was any exported function removed or renamed?
2. Was any function signature changed in a way that breaks callers?
3. Was any config key removed or renamed?

### Check 4 — Verify required artifacts exist

Does the next phase require specific artifacts from this package?
- Diff file at a specific path?
- Raw output file with specific naming?
- Snapshot at a specific path?
- Handoff document with specific fields?

Check each exists and is in the correct format.

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `DOWNSTREAM_READY` | Next phase can start without caveats |
| `DOWNSTREAM_READY_WITH_CAVEAT` | Next phase can start but the consumer should be aware of specified limitations |
| `DOWNSTREAM_NOT_READY` | Next phase must not start; listed blockers must be resolved first |

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Downstream ready (or with caveats) | `DOWNSTREAM_READY` or `DOWNSTREAM_READY_WITH_CAVEAT` | Continue |
| Downstream not ready | `DOWNSTREAM_NOT_READY` | `BLOCKED_HANDOFF_COMPLETE` |
