# Fixture: final_auditor_fail

Auditor verdict FAIL with REASON, BLOCKERS, REQUIRED_FIX, and RERUN_FROM BEGINNING.
HANDOFF.md says BLOCKED (consistent with verdict FAIL).

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification

## Expected
FAIL with `FINAL_PACKET_AUDITOR_FAIL`.

## Why
A FAIL verdict from the independent final auditor must always block, regardless of upstream signals.
