# Step 23 — Required Test Set Exactness

## Gate 5.4 raw-output proof rule

Summary claims do not substitute for raw proof. If a handoff, RTM, manifest, or other summary claims `EXIT_CODE:0` while the raw output lacks an accepted `EXIT_CODE:0` line, the checker must raise `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW`.

**State machine:** Write `current_state: REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_STANDARD and GATE_FULL.**

**Skip for GATE_LITE.** Produce `REQUIRED_TEST_SET_EXACTNESS_NOT_APPLICABLE.md`.

---

## Why this step exists

A task prompt that says "run the payment tests" does not mean "run every test matching `.*payment.*`". A broad pattern can include tests that are not the required tests, exclude required tests whose names do not match the pattern, or include tests that test something unrelated. The gate requires that the exact required test files were included in the test run and that the raw output confirms this.

---

## Output file

Copy `REQUIRED_TEST_SET_EXACTNESS_TEMPLATE.md` to `reports/<task_area>/REQUIRED_TEST_SET_EXACTNESS.md`.

---

## Required table (Gate 5.1 — includes EXIT_CODE parsed and post-pass error columns)

| test claim | raw output path | listed in manifest? | included in package? | EXIT_CODE parsed | EXIT_CODE flag | post-pass error? | POST_PASS flag | verdict |
|---|---|---|---|---|---|---|---|---|
| [path/to/test.spec.js] | [path to raw output] | YES / NO | YES / NO | [e.g. EXIT_CODE:0 (valid)] | [flag or none] | YES / NO | [POST_PASS_UNCAUGHT_ERROR or none] | PASS / FAIL |

---

## Checks

### Check 1 — Identify the required test set

From the task prompt, identify exactly which test files must be run:
- If the prompt names specific test files: list them
- If the prompt says "run tests for [feature]": identify which test files cover that feature
- If the prompt is ambiguous: flag it as `REQUIRED_TEST_SET_UNCLEAR` (see hard rule)

### Check 2 — Verify each required test file was included

For each required test file:
1. Find the test command used in the raw output
2. Verify that the command would include this specific file (not just a broader pattern)
3. Verify the file name appears in the raw output as a passing or failing test suite
4. If the file is absent from the raw output: flag `REQUIRED_TEST_MISSING_FROM_RUN`

### Check 3 — Verify EXIT_CODE for each test command (Gate 5.1 — strict)

For each test command that claimed to run the required test set:
1. Find the EXIT_CODE line in the raw output
2. Apply the exact regex: `^EXIT_CODE:0\s*$`
3. If the line matches: EXIT_CODE is valid
4. If no EXIT_CODE line: flag `EXIT_CODE_MISSING` — BLOCKING
5. If `EXIT_CODE:` with no value: flag `EXIT_CODE_BLANK` — BLOCKING
6. If value is not a number: flag `EXIT_CODE_NON_NUMERIC` — BLOCKING
7. If value is nonzero: flag `EXIT_CODE_NONZERO` — BLOCKING
8. If multiple EXIT_CODE lines with different values: flag `EXIT_CODE_CONFLICTING` — BLOCKING
9. If EXIT_CODE:0 appears only in the handoff/summary but not in the raw output file: flag `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` — BLOCKING

All six flags are BLOCKING. None may be classified EXPECTED_NON_BLOCKING.

**Also check for post-PASS errors:**
After finding the PASS summary line in each raw output, scan for errors appearing AFTER it (Error:, ENOENT, UnhandledPromiseRejection, uncaughtException, stack traces). If found: flag `POST_PASS_UNCAUGHT_ERROR` — BLOCKING unless explicitly justified with evidence.

### Check 4 — Verify broad patterns did not substitute for exact test sets

If the test command used a broad pattern (e.g., `--testPathPattern=.*`, `jest --all`, `npm test`):
1. Check whether the required test files are a strict subset of what the pattern runs
2. If the pattern runs more tests than required: this is acceptable (extra coverage is OK)
3. If the pattern runs fewer tests than required (because some required files have names that do not match the pattern): flag as `REQUIRED_TEST_EXCLUDED_BY_PATTERN`

---

## Hard rules

1. A broad pattern is not a substitute for an exact required test set unless the prompt explicitly says "run all tests" and there is no specific required set.
2. A test file listed in the task's required set but absent from the raw output is always a blocker.
3. A missing EXIT_CODE is always a blocker — cannot verify pass/fail without it.
4. A blank EXIT_CODE (`EXIT_CODE:` with no value) is BLOCKING — same as missing.
5. EXIT_CODE:0 in a handoff/summary document but absent from the raw output file is BLOCKING.
6. A raw output with `POST_PASS_UNCAUGHT_ERROR` is BLOCKING unless explicitly justified.
7. Raw outputs must be registered in PACKAGE_MANIFEST.md or EVIDENCE_LEDGER.yaml with `artifact_type: raw_test_output`. An unregistered raw output file in the package is a WARNING for GATE_STANDARD and BLOCKING for GATE_FULL.

---

## Raw Output Discovery — Manifest-Driven (Gate 5.1)

The checker must NOT scan only directories named `raw/` or `raw_outputs/`.

Required behavior:
- Every raw test output must be listed in PACKAGE_MANIFEST.md or EVIDENCE_LEDGER.yaml with `artifact_type: raw_test_output`
- Checks apply to ALL files marked as raw test outputs, regardless of directory or filename
- If a handoff claims a test was run but the raw output is absent from manifest/ledger/package: BLOCKING
- If a raw output exists in package but is not in manifest/ledger: BLOCKING for Gate Full, WARNING for Gate Standard

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| All required test files present in raw output with EXIT_CODE:0 | `REQUIRED_TEST_SET_EXACTNESS_PASS` | Continue |
| Any required test file missing from run | `REQUIRED_TEST_SET_EXACTNESS_FAIL` | `FIX_CYCLE_IN_PROGRESS` |
| Any EXIT_CODE missing or nonzero | `REQUIRED_TEST_SET_EXACTNESS_FAIL` | `FIX_CYCLE_IN_PROGRESS` |
