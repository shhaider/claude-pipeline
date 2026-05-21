# Warning Output Audit

**Cycle:** 1
**Verdict:** PASS

The raw test output `reports/system-gap-analyst/raw/pytest.log` was scanned for unresolved warnings, deprecation notices, and post-PASS uncaught errors.

```yaml
warning_output_audit:
  verdict: PASS
  scanned_raw_outputs:
    - reports/system-gap-analyst/raw/pytest.log
  blocking_warnings: []
  non_blocking_warnings: []
  summary: "9/9 tests passed; pytest emits no DeprecationWarning, PytestWarning, or unhandled tracebacks; no lines appear after the standard '9 passed in 0.01s' summary aside from the trailing 'EXIT_CODE:0' line; no POST_PASS_UNCAUGHT_ERROR pattern detected."
```

---

## What was scanned

- Lines before the test session start banner: none of interest.
- Lines between collection and `PASSED` markers: none of interest.
- Lines after the final `9 passed in 0.01s` summary: only the gate-required `EXIT_CODE:0` shell-emitted line. No `Error:`, no `ENOENT`, no `UnhandledPromiseRejection`, no `uncaughtException`, no `Jest did not exit`, no stack-trace `    at ` lines (the patterns in `POST_PASS_ERROR_PATTERNS` in `check_gate_package.py`).
- Stderr captured into the same log via `2>&1`: empty.

---

## Findings

- **Blocking:** none
- **Non-blocking:** none

## Verdict

PASS.
