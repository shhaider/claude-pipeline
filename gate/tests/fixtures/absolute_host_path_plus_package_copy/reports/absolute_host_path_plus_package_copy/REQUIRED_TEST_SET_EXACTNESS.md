# Required Test Set Exactness

**Task area:** absolute_host_path_plus_package_copy
**Audit completed at:** 2026-05-01T00:00:00Z

## Required test set verification table

| test claim | raw output path | listed in manifest? | included in package? | EXIT_CODE parsed | EXIT_CODE flag | post-pass error? | POST_PASS flag | verdict |
|---|---|---|---|---|---|---|---|---|
| tests/foo.test.js | raw/test_output.txt | YES | YES | EXIT_CODE:0 (valid) | none | NO | none | PASS |

## Verdict

REQUIRED_TEST_SET_EXACTNESS_PASS

**Rationale:** Raw output present in package at raw/test_output.txt with EXIT_CODE:0 valid, no post-PASS errors. The host provenance path is recorded in the ledger but does not substitute for the in-package copy.
