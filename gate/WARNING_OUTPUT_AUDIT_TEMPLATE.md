# Warning Output Contradiction Audit

Preferred Gate 5.4 structured block:

```yaml
warning_output_audit:
  verdict: PASS
  blocking_warnings: []
  checked_raw_outputs:
    - reports/<task_area>/raw_test_output.txt
  total_warnings_found: 0
```

If this structured block is present, the checker validates it first. Legacy prose-only audits still work through fallback scanning.

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Raw output scan

**Directories scanned:**
- [path]
- [path]

**Scan command:**
```bash
grep -RInE "warn|warning|not found|failed|fallback|skipped|deprecated|could not|unable|timeout|ENOENT|EADDRINUSE" [raw-output-dir] || true
```

**Raw scan output file:** `reports/<task_area>/raw_warning_scan.txt`

**Total warnings found:** [count]

---

## EXIT_CODE scan (Gate 5.1 — required for every raw output file)

| Raw output file | EXIT_CODE line found? | Parsed value | EXIT_CODE flag |
|---|---|---|---|
| [path] | YES / NO | [value, blank, or absent] | [EXIT_CODE_MISSING / EXIT_CODE_BLANK / EXIT_CODE_NONZERO / EXIT_CODE:0 (valid)] |

---

## Post-PASS error scan (Gate 5.1)

| Raw output file | PASS summary line found? | Error found after PASS? | Error text | POST_PASS flag |
|---|---|---|---|---|
| [path] | YES / NO | YES / NO | [error text if found] | [POST_PASS_UNCAUGHT_ERROR or none] |

---

## Warning classification table

| # | Warning text | File | Line | Position (before/after PASS) | Classification | Contradicts claimed behavior? | Blocking? |
|---|---|---|---|---|---|---|---|
| 1 | [text] | [file] | [line] | [before/after PASS] | EXPECTED_NON_BLOCKING | YES / NO | NO |
| 2 | [text] | [file] | [line] | [before/after PASS] | CONTRADICTS_SUCCESS_CLAIM | YES | YES |
| 3 | [text] | [file] | [line] | [before/after PASS] | POST_PASS_UNCAUGHT_ERROR | YES | YES |
| 4 | [text] | [file] | [line] | [before/after PASS] | REQUIRES_FOLLOWUP | NO | NO |

---

## Blocking warnings (CONTRADICTS_SUCCESS_CLAIM / BLOCKING)

For each blocking warning:

**Warning:** [exact text]
**File:** [file:line]
**Claimed success behavior it contradicts:** [what the handoff/prompt claims is working]
**Why it contradicts:** [one sentence explaining the contradiction]
**Fix required:** [what must change for this warning to not contradict the claim]

---

## Non-blocking warnings requiring follow-up

For each REQUIRES_FOLLOWUP warning:

**Warning:** [exact text]
**Follow-up action:** [what should be done in a future sprint]
**Not blocking because:** [one sentence]

---

## Scan summary

| Classification | Count |
|---|---|
| EXPECTED_NON_BLOCKING | [count] |
| CONTRADICTS_SUCCESS_CLAIM | [count] |
| REQUIRES_FOLLOWUP | [count] |
| BLOCKING | [count] |
| **Total** | **[count]** |

**Blocking warnings:** [count]

---

## Verdict

```
WARNING_OUTPUT_AUDIT_PASS | WARNING_OUTPUT_AUDIT_BLOCKING_FOUND
```

**Rationale:** [one paragraph]
