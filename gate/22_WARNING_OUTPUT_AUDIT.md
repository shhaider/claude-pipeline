# Step 22 — Warning Output Contradiction Audit

## Gate 5.4 blocking tokens

If `WARNING_OUTPUT_AUDIT.md` contains unresolved `BLOCKING`, `CONTRADICTS_SUCCESS_CLAIM`, `POST_PASS_UNCAUGHT_ERROR`, `EXIT_CODE_BLANK`, `EXIT_CODE_NONZERO`, or `CHECKPOINT_READBACK_WARNING_BLOCKING`, the package fails.

**State machine:** Write `current_state: WARNING_OUTPUT_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_STANDARD and GATE_FULL** when any raw test output, command output, or server output is present in the package.

**Skip for GATE_LITE.** Produce `WARNING_OUTPUT_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

Tests can exit with code 0 and be counted as "passing" while the raw output contains warnings that directly contradict the claimed success. Examples:
- "Tests: 47/47 PASS" but the output contains "ENOENT: no such file or directory — config.json" — the feature that reads config.json is untested
- "Migration applied successfully" but output contains "WARN: table users already exists — skipping" — the migration was a no-op, not a real application
- "Service started" but output contains "fallback: using in-memory store (Redis unavailable)" — the Redis-backed behavior is untested

This audit scans all raw outputs for warnings and classifies each one relative to the task's success claims.

---

## Output file

Update `reports/<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` (append a "Warning Scan" section, or write standalone to `reports/<task_area>/WARNING_OUTPUT_AUDIT.md`).

Copy `WARNING_OUTPUT_AUDIT_TEMPLATE.md` to `reports/<task_area>/WARNING_OUTPUT_AUDIT.md`.

---

## Required raw output scan

Run against all raw output directories in the package:

```bash
grep -RInE "warn|warning|not found|failed|fallback|skipped|deprecated|could not|unable|timeout|ENOENT|EADDRINUSE" <raw-output-dir> || true
```

If no raw output directory exists: record "NO RAW OUTPUT DIRECTORY FOUND" as a blocker (cannot perform audit).

Save output to `reports/<task_area>/raw_warning_scan.txt`.

---

## Warning classification

For each warning found:

| Warning text | File | Line | Classification | Contradicts claimed behavior? | Blocking? |
|---|---|---|---|---|---|
| [exact warning text] | [file] | [line] | [class] | YES / NO | YES / NO |

### Classification options

| Classification | Meaning |
|---|---|
| `EXPECTED_NON_BLOCKING` | Warning is expected and documented; does not affect claimed behavior (e.g., "debug mode active", "using test credentials") |
| `CONTRADICTS_SUCCESS_CLAIM` | Warning directly contradicts a claimed success behavior. ALWAYS BLOCKING. |
| `REQUIRES_FOLLOWUP` | Warning indicates a condition that should be addressed in a future sprint but does not block this handoff |
| `BLOCKING` | Warning indicates a condition that prevents the claimed behavior from working correctly |

---

## Hard rule

A warning that contradicts claimed behavior is **blocking** even when:
- All tests passed with EXIT_CODE:0
- Test counts match
- The implementer marked the task complete
- A prior reviewer did not flag it

"Tests pass" and "warning contradicts success claim" are simultaneously true — the tests proved something other than what the warning reveals.

---

## EXIT_CODE Validation in Warning Audit (Gate 5.1)

As part of warning scanning, verify EXIT_CODE for every raw output file. Add a section to the warning table:

| Raw output file | EXIT_CODE line found? | Parsed value | Flag |
|---|---|---|---|
| [path] | YES/NO | [value or blank] | [EXIT_CODE_MISSING / EXIT_CODE_BLANK / EXIT_CODE_NONZERO / EXIT_CODE:0 (valid)] |

A blank `EXIT_CODE:` line (no value) must be flagged `EXIT_CODE_BLANK` — this is BLOCKING, not a warning.

---

## Post-PASS Uncaught Error Detection — Hard Rule (Gate 5.1)

The warning scan MUST check for errors appearing AFTER any PASS summary line.

Scan sequence:
1. Run the warning grep against all raw outputs
2. For each raw output: identify the position of the PASS summary line (e.g., `Tests: N passed`)
3. For any warning match in step 1: check if it appears AFTER the PASS summary line
4. If YES: classify as `POST_PASS_UNCAUGHT_ERROR` — BLOCKING

Blocking post-PASS patterns to scan for (use after locating PASS line):
- `Error:` (case-sensitive)
- `ENOENT`
- `UnhandledPromiseRejection`
- `uncaughtException`
- `Jest did not exit`
- Stack traces: lines starting with `    at ` (4 spaces + `at`)

Flag: `POST_PASS_UNCAUGHT_ERROR`

The Warning Output Audit must classify `POST_PASS_UNCAUGHT_ERROR` as BLOCKING unless the package provides an explicit, evidence-backed reason it is expected and non-impacting (with a named reference to the specific error and why it does not affect result correctness).

Mere proximity to a PASS line is NOT sufficient justification. "Tests passed" does NOT override a blocking post-PASS error.

Add `POST_PASS_UNCAUGHT_ERROR` column to the warning classification table when applicable.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| No CONTRADICTS_SUCCESS_CLAIM or BLOCKING warnings | `WARNING_OUTPUT_AUDIT_PASS` | Continue in reviewer sequence |
| One or more CONTRADICTS_SUCCESS_CLAIM or BLOCKING warnings | `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` | `FIX_CYCLE_IN_PROGRESS` |

---

## Also update

Append a "Warning Scan Results" section to `reports/<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` with the scan summary and any blocking findings.

Append a "Warning Output Findings" section to `reports/<task_area>/15_FINAL_PACKAGE_AUDIT.md` with any warnings that affect the package status claim.
