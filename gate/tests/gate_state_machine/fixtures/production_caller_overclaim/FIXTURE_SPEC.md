# Fixture: production_caller_overclaim

## Setup

- `FINAL_HANDOFF.md` claims: "Live behavior fixed: userRepo.findById now returns the correct user object"
- `CURRENT_STATE.yaml` records `final_outcome_label: LIVE_BEHAVIOR_FIXED`
- `PRODUCTION_CALLER_AUDIT.md` table shows:
  - Changed module: `src/repositories/userRepository.js`
  - Production caller found: NO
  - Test caller: `tests/repositories/userRepository.test.js`
  - Verdict (in audit): INFRASTRUCTURE_READY_NOT_WIRED
- But `CURRENT_STATE.yaml` says `production_caller_audit_result: PASS`
  (contradiction — the audit found no production caller but still recorded PASS)
- Tests: 23/23 PASS, EXIT_CODE: 0

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Overclaim: final_outcome_label is LIVE_BEHAVIOR_FIXED but PRODUCTION_CALLER_AUDIT shows no production caller
       PRODUCTION_CALLER_AUDIT.md: Production caller found: NO
       CURRENT_STATE.yaml: production_caller_audit_result: PASS  (contradicts audit file)
       Invariant violated: final_outcome_label_matches_production_caller_audit
[FAIL] CURRENT_STATE.yaml production_caller_audit_result contradicts PRODUCTION_CALLER_AUDIT.md:
       State file says: PASS
       Audit file says: NO production caller found
```

## Expected invariant

`final_outcome_label_matches_production_caller_audit`

## Why this matters

Tests can pass and code can be correct while no production code calls it. The 23 tests
passing prove the module works in isolation — not that any live user request will reach it.
Labeling this LIVE_BEHAVIOR_FIXED will mislead the next agent into assuming the feature
is deployed when it is merely implemented.
