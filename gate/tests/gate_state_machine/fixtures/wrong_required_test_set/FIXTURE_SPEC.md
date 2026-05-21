# Fixture: wrong_required_test_set

## Setup

- Task prompt: "Run tests/payment/checkout.test.js and tests/payment/refund.test.js"
- Test command used: `npx jest --testPathPattern=".*payment.*"`
- Raw output: 
  ```
  Test Suites: 3 passed, 3 total
  Tests: 89 passed, 89 total
  EXIT_CODE: 0
  ```
- The pattern matched:
  - `tests/payment/checkout.test.js` ✓
  - `tests/payment/refund.test.js` ✓  
  - `tests/payment/payment_utils.test.js` (not required — just happened to match)
- But `tests/payment/refund.test.js` was actually SKIPPED inside due to a `.skip` in the
  test file — this is not visible in the suite-level summary
- `REQUIRED_TEST_SET_EXACTNESS.md` claims:
  - `tests/payment/checkout.test.js`: Pass ✓
  - `tests/payment/refund.test.js`: Pass ✓ (incorrect — tests were skipped)

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Required test exactness: tests/payment/refund.test.js skipped tests not reported
       Pattern --testPathPattern=".*payment.*" matched the file but tests inside were skipped
       REQUIRED_TEST_SET_EXACTNESS.md: tests/payment/refund.test.js marked Pass ✓
       Raw output shows: 0 tests from refund.test.js (skipped tests hidden in summary)
       Invariant violated: required_test_file_produced_results
[WARN] Broad pattern used instead of exact test files:
       Command: npx jest --testPathPattern=".*payment.*"
       Required files: tests/payment/checkout.test.js, tests/payment/refund.test.js
       Note: broad pattern included an extra file not in the required set
```

## Expected invariant

`required_test_file_produced_results`

## Why this matters

89/89 tests passed. But the required test file ran 0 tests because all were skipped.
The summary counts do not include skipped tests. Without checking the individual file
output, this passes silently. The refund code is unverified.
