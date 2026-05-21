# Required Test Set Exactness

**Task area:** missing_raw_output

## Required test set verification table

| test claim | raw output path | listed in manifest? | included in package? | EXIT_CODE parsed | EXIT_CODE flag | post-pass error? | POST_PASS flag | verdict |
|---|---|---|---|---|---|---|---|---|
| tests/foo.test.js | raw_test_output.txt | YES | NO | N/A (file missing) | EXIT_CODE_MISSING | N/A | none | FAIL |

## Verdict

REQUIRED_TEST_SET_EXACTNESS_FAIL

**Rationale:** Raw output file raw_test_output.txt is listed in the manifest and ledger but is absent from the package.
