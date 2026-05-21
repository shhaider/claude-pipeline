# Fixture: helper_test_only_claiming_production

## Setup

- Task: "Add `formatMemoryForExport()` helper to memoryUtils.js"
- `memoryUtils.js` exports `formatMemoryForExport()`
- Callers found:
  - `tests/memory/formatMemoryForExport.test.js` — imports `formatMemoryForExport`
  - No other callers exist in src/, app/, or lib/
- `STRANDED_HELPER_AUDIT.md` shows:
  - Production caller: none found
  - Test caller: `tests/memory/formatMemoryForExport.test.js`
  - Verdict: PRODUCTION_WIRED (incorrect — should be TEST_HELPER_ONLY)
- `CURRENT_STATE.yaml` records `stranded_helper_audit_result: PASS`
- `FINAL_HANDOFF.md` claims: "formatMemoryForExport is now production wired"
- `final_outcome_label: LIVE_BEHAVIOR_FIXED`

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Stranded helper overclaim:
       Helper: formatMemoryForExport (memoryUtils.js)
       Production callers: NONE
       Test callers: tests/memory/formatMemoryForExport.test.js
       STRANDED_HELPER_AUDIT.md verdict: PRODUCTION_WIRED (incorrect)
       Correct verdict: TEST_HELPER_ONLY
       Invariant violated: stranded_helper_verdict_matches_caller_search
[FAIL] final_outcome_label LIVE_BEHAVIOR_FIXED contradicts stranded helper finding:
       No production caller proven
       Correct label: TEST_HELPER_ONLY or INFRASTRUCTURE_READY_NOT_WIRED
```

## Expected invariant

`stranded_helper_verdict_matches_caller_search`

## Why this matters

The helper was written. Tests pass. But no production code exports or calls it.
The function exists only in test memory. If the next sprint tries to wire it,
the caller will need to import it — and the first import must be proven. Labeling
this as LIVE_BEHAVIOR_FIXED misleads downstream planners into skipping the wiring step.
