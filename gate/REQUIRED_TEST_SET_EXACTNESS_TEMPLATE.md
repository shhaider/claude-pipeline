# Required Test Set Exactness

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Required test set (from task prompt)

List each test file explicitly required by the task prompt:

1. `[path/to/test.spec.js]` — required because: [reason]
2. `[path/to/test.spec.js]` — required because: [reason]
3. OR: Required test set not specified in prompt → flag REQUIRED_TEST_SET_UNCLEAR

---

## Test commands used

List every test command run as part of this task:

| Command | Runs which tests | Raw output file | EXIT_CODE |
|---|---|---|---|
| `[npx jest tests/foo.spec.js]` | [exact files or pattern] | [path] | [0/1] |
| `[npm test]` | [all tests in project] | [path] | [0/1] |

---

## Required test set verification table (Gate 5.1)

| test claim | raw output path | listed in manifest? | included in package? | EXIT_CODE parsed | EXIT_CODE flag | post-pass error? | POST_PASS flag | verdict |
|---|---|---|---|---|---|---|---|---|
| [path/to/test.spec.js] | [path to raw output] | YES / NO | YES / NO | [EXIT_CODE:0 (valid) or blank or value] | [flag or none] | YES / NO | [POST_PASS_UNCAUGHT_ERROR or none] | PASS / FAIL |

---

## Broad pattern analysis

| Command | Pattern used | Could exclude required tests? | Required tests excluded? | Status |
|---|---|---|---|---|
| [command] | [pattern or "exact"] | YES/NO | YES/NO | OK / EXCLUDED_BY_PATTERN |

---

## Flags

| Flag | Applied to | Details | Blocking? |
|---|---|---|---|
| `REQUIRED_TEST_MISSING_FROM_RUN` | [test file] | [not found in raw output] | YES |
| `EXIT_CODE_MISSING` | [command/output file] | [no EXIT_CODE line in raw output] | YES |
| `EXIT_CODE_BLANK` | [command/output file] | [EXIT_CODE: line with no value] | YES |
| `EXIT_CODE_NON_NUMERIC` | [command/output file] | [EXIT_CODE value is not a number] | YES |
| `EXIT_CODE_NONZERO` | [command/output file] | [EXIT_CODE value is nonzero] | YES |
| `EXIT_CODE_CONFLICTING` | [command/output file] | [multiple EXIT_CODE lines with different values] | YES |
| `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` | [command/output file] | [EXIT_CODE:0 in handoff but absent from raw output file] | YES |
| `POST_PASS_UNCAUGHT_ERROR` | [command/output file] | [Error/ENOENT/stack trace appearing after PASS summary line] | YES (unless explicitly justified) |
| `REQUIRED_TEST_EXCLUDED_BY_PATTERN` | [test file] | [pattern does not match file name] | YES |
| `REQUIRED_TEST_SET_UNCLEAR` | [prompt] | [prompt does not specify which tests] | YES |
| `RAW_OUTPUT_NOT_IN_MANIFEST` | [output file] | [raw output exists in package but not listed in manifest/ledger] | FULL: YES / STANDARD: WARNING |

**Total flags:** [count]
**Blocking flags:** [count]

---

## Verdict

```
REQUIRED_TEST_SET_EXACTNESS_PASS | REQUIRED_TEST_SET_EXACTNESS_FAIL
```

**Rationale:** [one paragraph]
