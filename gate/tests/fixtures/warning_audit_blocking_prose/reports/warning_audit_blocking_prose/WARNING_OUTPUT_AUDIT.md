# Warning Output Contradiction Audit

**Task area:** happy_path_gate_full
**Audit completed at:** 2026-05-01T00:00:00Z

## EXIT_CODE scan

| Raw output file | EXIT_CODE line found? | Parsed value | EXIT_CODE flag |
|---|---|---|---|
| raw_test_output.txt | YES | 0 | EXIT_CODE:0 (valid) |

## Post-PASS error scan

| Raw output file | PASS summary line found? | Error found after PASS? | Error text | POST_PASS flag |
|---|---|---|---|---|
| raw_test_output.txt | YES | NO | none | none |

## Warning classification table

| # | Warning text | File | Line | Position | Classification | Contradicts claimed behavior? | Blocking? |
|---|---|---|---|---|---|---|---|
| 1 | Error: ENOENT after PASS | raw_test_output.txt | 9 | post-pass | POST_PASS_UNCAUGHT_ERROR | YES | YES |

## Verdict

WARNING_OUTPUT_AUDIT_FAIL

**Rationale:** POST_PASS_UNCAUGHT_ERROR is unresolved and blocking.
