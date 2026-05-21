# Flake / Timeout / Load Sensitivity Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Time-sensitive assertion scan

Tests inspected: [list of test files]

| Test | File | Pattern found | Sensitivity type | Severity |
|---|---|---|---|---|
| [test name] | [file:line] | `setTimeout(fn, 100)` | TIMING | WARNING / BLOCKING |
| [test name] | [file:line] | `await delay(500)` | TIMING | WARNING / BLOCKING |

Time-sensitive patterns found: [count]

---

## Load-sensitive assumption scan

| Test | File | Assumption | Load sensitivity type | Severity |
|---|---|---|---|---|
| [test name] | [file:line] | [uses port 3000] | SHARED_PORT | BLOCKING |
| [test name] | [file:line] | [assumes < 200ms response] | RESPONSE_TIME | WARNING |

Load-sensitive patterns found: [count]

---

## Retry and flake pattern scan

| Test | File | Pattern | Interpretation |
|---|---|---|---|
| [test name] | [file:line] | [explicit retry] | MASKS_FLAKINESS |
| [test name] | [file:line] | [jest.setTimeout(10000)] | PRIOR_FLAKINESS |

Flake patterns found: [count]

---

## VPS load check (if applicable)

**Command:** `cat /proc/loadavg && free -h && nproc`
```
[output]
```

**Load at test time:** [value]
**CPU count:** [value]
**Load threshold (5x CPU):** [value]
**Tests run under acceptable load:** YES / NO

---

## Findings summary

| Category | Count | Max severity |
|---|---|---|
| Time-sensitive | [count] | WARNING / BLOCKING |
| Load-sensitive | [count] | WARNING / BLOCKING |
| Flake patterns | [count] | WARNING / BLOCKING |
| High load during run | YES/NO | WARNING / BLOCKING |

**Total blocking findings:** [count]

---

## Verdict

```
TEST_STABILITY_OK | TEST_STABILITY_WARNING_FOLLOWUP | TEST_STABILITY_BLOCKING
```

**Rationale:** [one paragraph]

**Follow-up required (if WARNING_FOLLOWUP):** [description of what should be fixed in a future sprint]
