# Fixture: warning_contradicts_success

## Setup

- Task: "Wire Redis cache for session storage"
- `FINAL_HANDOFF.md` claims: "Redis session cache is now live"
- `raw_outputs/test_run.log` contains:
  ```
  Tests: 47/47 PASS
  EXIT_CODE: 0
  WARN: Redis connection failed — falling back to in-memory store
  WARN: Session data will not persist across server restarts
  ```
- `WARNING_OUTPUT_AUDIT.md` is absent from the package
  (GATE_STANDARD was selected; warning audit was skipped)
- `CURRENT_STATE.yaml` records `warning_output_audit_result: NOT_APPLICABLE`
  (incorrect — GATE_STANDARD requires warning audit when raw output is present)
- All 47 tests pass because tests use the in-memory fallback, not Redis

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Warning contradicts success claim:
       Claimed behavior: "Redis session cache is now live"
       Warning in raw_outputs/test_run.log line 5: "Redis connection failed — falling back to in-memory store"
       Warning in raw_outputs/test_run.log line 6: "Session data will not persist across server restarts"
       Tests passed using in-memory fallback, not Redis
       Invariant violated: warning_does_not_contradict_success_claim
[FAIL] WARNING_OUTPUT_AUDIT.md absent but raw output contains warnings:
       Profile GATE_STANDARD requires warning audit when raw output is present
       raw_outputs/test_run.log contains 2 WARN lines
       CURRENT_STATE.yaml: warning_output_audit_result: NOT_APPLICABLE (incorrect)
```

## Expected invariant

`warning_does_not_contradict_success_claim`

## Why this matters

47/47 tests passed. EXIT_CODE was 0. The tests are not wrong — they tested the
in-memory fallback correctly. But the claim "Redis session cache is now live" is
false. The feature is unverified. A warning scan catches this in 2 seconds.
Without the warning audit, this ships as "Redis wired" when Redis was never used.
