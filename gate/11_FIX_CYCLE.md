# Step 11 — Fix Cycle

You are here because the gate returned `FAIL_AUTOFIX_REQUIRED`, or `15_FINAL_PACKAGE_AUDIT.md` / `16_CANONICAL_HANDOFF_AUDIT.md` returned FAIL and could not self-fix.

## First — read and update CURRENT_STATE.yaml

Write `current_state: FIX_CYCLE_IN_PROGRESS`.

## Then — check the cycle counter

Open `reports/<task_area>/CYCLE_TRACKER.md`.

- If this was **Cycle 5**: stop. You have reached the maximum. Go to `13_BLOCKED_HANDOFF.md`.
- If this was **Cycle 1–4**: continue below.

---

## What to do

### 1. List every AUTOFIX_REQUIRED blocker

Pull the complete blocker list from `COLD_REVIEW_ADJUDICATION.md`. Every `AUTOFIX_REQUIRED` blocker must be addressed before the next cycle starts.

Do not address `HUMAN_BLOCKED` blockers here — those go to `13_BLOCKED_HANDOFF.md`. If there are both `AUTOFIX_REQUIRED` and `HUMAN_BLOCKED` blockers, fix the autofixable ones first; the human-blocked ones still block the final gate.

### 2. Fix every autofix blocker

Fix each blocker within the original allowed task scope.

**Hard rule: do not start the next cycle until every `AUTOFIX_REQUIRED` blocker from this cycle is addressed.** Partially fixing and re-running is not allowed — if you fix 3 of 4 blockers and re-run, the unfixed blocker will reappear and consume another cycle unnecessarily.

**Scope discipline:** The fix phase may not:
- Start a later project phase
- Expand feature scope
- Modify forbidden files
- Merge unrelated work
- Perform opportunistic cleanup outside the task
- Change architecture without authorization
- Rewrite history to make evidence look cleaner
- Delete inconvenient evidence instead of clearly superseding it

### 3. Rerun affected tests

If code, tests, runtime behavior, evidence requirements, reports, snapshots, or packaging changed — rerun those tests. Save new raw outputs with exact commands and exit codes.

### 4. Regenerate stale artifacts

Regenerate everything that the fix touched or invalidated:
- Manifests
- Diffs
- Changed-file snapshots
- RTMs
- Raw outputs
- Handoffs
- Package file listings
- Evidence Adequacy Assessment (if evidence was created or changed)
- Evidence Consistency Register
- Closed-loop gate report

**For cold review reports:** The reports of any Reviewer 1–4 whose prior report contained BLOCKING findings should be regenerated now for your own fix-verification — to confirm the blocker is actually resolved before the next cycle. All five reports will be rewritten fresh when the panel runs again in the next cycle regardless.

### 5. Update CURRENT_STATE.yaml and the cycle tracker

Write to CURRENT_STATE.yaml:
```yaml
cycles:
  <N>:
    fixes_applied: [list of fixes]
```

In `reports/<task_area>/CYCLE_TRACKER.md`, record:
- Which cycle just completed (the one that failed)
- Each AUTOFIX_REQUIRED blocker and the fix applied
- Tests rerun
- Artifacts regenerated

### 6. Confirm: has anything changed that could affect other reviewers?

The fix for one reviewer's blocker can introduce issues detectable by a different reviewer. All 5 reviewers will run fresh in the next cycle — you do not need to predict what they will find, but you should be aware that a fix to R2's blocker (missing test) could introduce a pattern R3 would catch (wrong import path in the new test file).

---

## Starting the next cycle

The next cycle begins at `01_EVIDENCE_ADEQUACY.md` — not at the panel. Evidence adequacy must be reassessed with the updated artifacts.

**The next cycle is a full cycle: evidence adequacy → consistency preflight → all 5 reviewers. Do not skip to the panel or skip to the reviewers that failed last time.**

Before starting the next cycle, also update STALE_FILE_REGISTER.yaml: register any reports from the just-completed cycle that have now been superseded as `HISTORICAL_PRIOR_CYCLE`.

---

## Routing

| Situation | State to write | Next file |
|---|---|---|
| Cycle 1–4, all AUTOFIX blockers addressed | `FIX_CYCLE_COMPLETE` | `01_EVIDENCE_ADEQUACY.md` (start new cycle, increment cycle_count) |
| Cycle 5 just completed (maximum reached) | `MAX_CYCLES_REACHED` | `13_BLOCKED_HANDOFF.md` |
| HUMAN_BLOCKED blockers also exist (alongside autofixable ones) | Fix autofixable ones → `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` | `13_BLOCKED_HANDOFF.md` (human blockers still prevent PASS) |

---

## Final Auditor Failure Rerun Policy (Gate 5.3)

When the Final Packet Auditor (state 37) returns FAIL, this fix cycle is the entry point for the resulting work. Apply the following rules based on profile:

### GATE_FULL and GATE_FULL_PLUS_DOMAIN_ADDENDUM
- Any FINAL_PACKET_AUDITOR_VERDICT: FAIL → fix the issues, then RESTART the gate from Evidence Adequacy.
- Re-run all required reviewers and audits.
- Reason: a fix can change evidence, scope, tests, package contents, or report consistency. A surface-only re-check is unsafe.

### GATE_STANDARD
- If the fix changes source, tests, runtime behavior, package contents, or status claims → restart from Evidence Adequacy.
- If the fix is only a typo in a non-authoritative report and no proof artifacts changed → targeted rerun allowed:
  RERUN_FROM: TARGETED_STATE:<state name>
  followed by FINAL_PACKET_AUDITOR again.

### GATE_LITE
- Targeted rerun allowed for docs-only / report-only fixes.
- If source/test/runtime artifacts changed → upgrade profile to GATE_STANDARD or GATE_FULL based on profile selection.

### Repeated failure
If the same package fails FINAL_PACKET_AUDITOR twice:
- Escalate one profile level (Lite → Standard, Standard → Full, Full → Full+Domain) if possible.
- Require CTO / Operator Insight Review.
- Record in Gate Effectiveness Log with `repeated_final_auditor_failure: true`.
