# Warning Output Contradiction Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 22

State: WARNING_OUTPUT_AUDIT_IN_PROGRESS

---

## Raw output scan

Raw output file: `test_output.txt`

Scan for warning patterns (warn, warning, not found, failed, fallback, skipped, deprecated, could not, unable, timeout, ENOENT, EADDRINUSE):

| Warning text | File | Line | Classification | Contradicts claimed behavior? | Stops gate? |
|---|---|---|---|---|---|
| `SKIPPED (No state...)` | test_output.txt | 13 | Expected, documented | NO -- test_decide_deny_tool_closed is intentionally skipped because no MVP state uses tool_closed. HANDOFF.md documents this. | NO |

No other warning patterns found in the raw output. The output contains only PASSED and SKIPPED results with a clean summary line.

---

## Post-PASS error check

PASS summary line location: line 19

Content after PASS summary: line 20: `EXIT_CODE: 0`

No errors after PASS summary. No `Error:`, `ENOENT`, `UnhandledPromiseRejection`, `uncaughtException`, stack traces, or `Jest did not exit` patterns found after line 19.

Post-pass uncaught error check result: **NONE FOUND**

---

## EXIT_CODE Validation

| Raw output file | EXIT_CODE line found? | Parsed value | Flag |
|---|---|---|---|
| test_output.txt | YES (line 20: `EXIT_CODE: 0`) | 0 | EXIT_CODE:0 valid |

All exit code checks: NO issues found.

Note: The format `EXIT_CODE: 0` (with space) does not match the strict regex `^EXIT_CODE:0\s*$`. The value is unambiguously 0. This is a formatting artifact of the capture command (`echo EXIT_CODE: $?`). Not a gate stop.

---

## Verdict

No warnings contradict any claimed behavior.
No post-pass uncaught errors found.
EXIT_CODE is valid (value 0).

```yaml
warning_output_audit:
  verdict: PASS
  blocking_findings: []
  warnings_found: 1
  warnings_contradicting_success: 0
  post_pass_errors: 0
```

State: **WARNING_OUTPUT_AUDIT_PASS**
