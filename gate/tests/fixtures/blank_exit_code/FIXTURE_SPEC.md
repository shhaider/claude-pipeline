# Fixture Spec: blank_exit_code

**Scenario:** Raw output contains `EXIT_CODE:` with no numeric value. This simulates
a blank PIPESTATUS capture (e.g., `echo "EXIT_CODE:$?"` where `$?` was not captured correctly).

**Expected checker result:** FAIL with flag `EXIT_CODE_BLANK`

**Why this matters:** This is the exact failure mode in M77-P05A where the raw output
ended with `EXIT_CODE:` (blank) instead of `EXIT_CODE:0`. Under Gate 5.0 rules, the
`EXIT_CODE_MISSING` flag did not cover this case because an EXIT_CODE line was technically
present. Gate 5.1 adds `EXIT_CODE_BLANK` as a distinct blocking flag.
