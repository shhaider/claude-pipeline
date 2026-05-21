# Step 10 — Gate Verdict

You are here after Reviewer 5 has issued a verdict in `COLD_REVIEW_ADJUDICATION.md`.

## Step 1 — Read CURRENT_STATE.yaml

Confirm `current_state: R5_COMPLETE`. Write `current_state: GATE_VERDICT_ISSUED`.

## Step 2 — Map Reviewer 5's verdict to the gate verdict

| Reviewer 5 verdict | Preliminary gate verdict |
|---|---|
| `READY_FOR_REVIEW` | `PASS_FOR_HANDOFF` |
| `NEEDS_CORRECTION` | `FAIL_AUTOFIX_REQUIRED` |
| `BLOCKED` | `FAIL_BLOCKED_REQUIRES_HUMAN` |
| `STOP_AND_REDESIGN` | `FAIL_BLOCKED_REQUIRES_HUMAN` |

## Step 3 — Enforcement Authority Audit override

If `ENFORCEMENT_AUTHORITY_AUDIT.md` was applicable, apply these overrides after the R5 mapping above:

| Enforcement verdict | Override gate verdict |
|---|---|
| `FAIL_AUTOFIX_REQUIRED` | Gate verdict becomes `FAIL_AUTOFIX_REQUIRED` minimum (escalates if R5 was PASS) |
| `FAIL_BLOCKED_REQUIRES_HUMAN` | Gate verdict becomes `FAIL_BLOCKED_REQUIRES_HUMAN` minimum |

A `PASS_FOR_HANDOFF` is not allowed if `ENFORCEMENT_AUTHORITY_AUDIT.md` records any FAIL.

Check `cycles.<N>.enforcement_audit_result` in CURRENT_STATE.yaml. If it is `FAIL_AUTOFIX_REQUIRED` or `FAIL_BLOCKED_REQUIRES_HUMAN`, override the gate verdict accordingly.

## Step 4 — Write gate verdict to CURRENT_STATE.yaml

Write to CURRENT_STATE.yaml:
```yaml
current_state: GATE_PASS_FOR_HANDOFF   # or GATE_FAIL_AUTOFIX_REQUIRED or GATE_FAIL_BLOCKED_REQUIRES_HUMAN
cycles:
  <N>:
    r5_verdict: <R5 verdict>
    gate_verdict: <final gate verdict after override>
    blockers_autofix: <count>
    blockers_human_blocked: <count>
```

## Step 5 — Update the cycle tracker

Open `reports/<task_area>/CYCLE_TRACKER.md` and record:
- Reviewer 5 verdict for this cycle
- Gate verdict (after enforcement override if applicable)
- Blocker count (AUTOFIX / HUMAN_BLOCKED)
- Whether cycle passed or failed

---

## Pre-PASS Barrier Check (Gate 5.1)

Before issuing `GATE_PASS_FOR_HANDOFF`, perform this barrier check. If any item is unchecked, issue `GATE_FAIL_AUTOFIX_REQUIRED` or `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` instead:

```
Pre-PASS Barrier Checklist:
[ ] All required states for selected profile are present in CURRENT_STATE.yaml
[ ] No required state is FAIL/BLOCKING/UNCERTAIN/missing
[ ] check_gate_package.py exits 0 (Gate Full — required; Gate Standard — recommended)
[ ] GATE_PACKAGE_VALIDATION_REPORT.md present in package (Gate Full — skip on first run)
[ ] EXIT_CODE validation: no EXIT_CODE_MISSING/BLANK/NONZERO/CONFLICTING in any raw output
[ ] Post-PASS error check: no POST_PASS_UNCAUGHT_ERROR in any raw output
[ ] (Gate 5.3) FINAL_PACKET_AUDITOR_REPORT.md exists at reports/{task_area}/
[ ] (Gate 5.3) FINAL_PACKET_AUDITOR_VERDICT is PASS
[ ] (Gate 5.3) All five required fields are present in the report (VERDICT, REASON, BLOCKERS, REQUIRED_FIX, RERUN_FROM)
```

If any EXIT_CODE or POST_PASS flag is present: route to `GATE_FAIL_AUTOFIX_REQUIRED` → `FIX_CYCLE_IN_PROGRESS`.

If any required audit state is FAIL but not fixable within scope: route to `GATE_FAIL_BLOCKED_REQUIRES_HUMAN`.

---

## Routing

| Gate verdict | State to write | Next file |
|---|---|---|
| `PASS_FOR_HANDOFF` | `GATE_PASS_FOR_HANDOFF` → `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | `15_FINAL_PACKAGE_AUDIT.md` |
| `FAIL_AUTOFIX_REQUIRED` | `GATE_FAIL_AUTOFIX_REQUIRED` | `11_FIX_CYCLE.md` |
| `FAIL_BLOCKED_REQUIRES_HUMAN` | `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` | `13_BLOCKED_HANDOFF.md` |

**Note:** PASS routes through `15_FINAL_PACKAGE_AUDIT.md` → `16_CANONICAL_HANDOFF_AUDIT.md` → `17_EXECUTION_CONTEXT_AUDIT.md` before reaching `12_PASS_HANDOFF.md`. All three are non-negotiable — no exceptions.
