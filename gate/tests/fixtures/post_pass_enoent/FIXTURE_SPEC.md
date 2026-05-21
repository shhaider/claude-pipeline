# Fixture Spec: post_pass_enoent

**Scenario:** Raw output contains a Jest PASS summary and `EXIT_CODE:0`, but is followed
by an `Error: ENOENT` cache write failure. This simulates the exact M77-P05A post-PASS
error pattern.

**Expected checker result:** FAIL with flag `POST_PASS_UNCAUGHT_ERROR`

**Why this matters:** The output contains a valid `EXIT_CODE:0` line, so EXIT_CODE
validation passes. The defect is the ENOENT error appearing AFTER the PASS summary line.
Gate 5.0 had no explicit rule about position-relative errors. Gate 5.1 adds
`POST_PASS_UNCAUGHT_ERROR` as a distinct blocking flag that catches errors after PASS.
