# Fixture: bad_right_command_wrong_branch

## Setup

- `FINAL_HANDOFF.md` claims "post-merge tests ran on main after ORCH merged the integration branch"
- `post_merge_tests.log` shows 47/47 tests passed
- BUT `git branch --show-current` in the log shows `agentos-ng-integration`, not `main`
- `CURRENT_STATE.yaml` claims `PASS_HANDOFF_COMPLETE` but `execution_context_audit_result: null`

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Execution context audit: result is null — Step 17 was not run
       PASS_HANDOFF_COMPLETE requires execution_context_audit_result = PASS or NOT_APPLICABLE
[FAIL] Context claim verification: "post-merge tests ran on main"
       post_merge_tests.log line 4: git branch --show-current = agentos-ng-integration
       Expected: main
       Observed: agentos-ng-integration
       Invariant violated: right_command_wrong_context
```

## Expected invariant

`right_command_wrong_context`

## Why this matters

The tests genuinely ran. 47/47 passed. The evidence is not fabricated. But the context was wrong.
A reviewer reading only the test output would accept the claim. Only checking branch/HEAD proof in
the raw output catches this failure. Without Step 17, this packet would have been shipped as PASS
with a false "tested on main" claim.
