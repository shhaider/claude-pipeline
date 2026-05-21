# Step 4 — Panel Entry

**State machine:** Verify CURRENT_STATE.yaml shows `ENFORCEMENT_AUDIT_PASS` or `ENFORCEMENT_AUDIT_NOT_APPLICABLE` as the most recent enforcement state. Then write `current_state: PANEL_ENTRY_VERIFIED`.

You are here because the Evidence Consistency Preflight passed and the Enforcement Authority Audit (step 14) returned PASS or NOT_APPLICABLE. The evidence package is adequate, internally consistent, and — if the task involved enforcement — has verified that enforcement is authoritative. You are now ready to run the 5-reviewer cold panel.

---

## Critical rules — read before running any reviewer

### The panel produces one verdict, not five

Reviewers 1–4 produce **findings reports only**. They do not issue pass or fail verdicts. Reviewer 5 reads all four reports and produces the **sole consolidated verdict**. Individual reviewer reports do not separately pass or fail the package.

### Do not apply any fix mid-cycle

The panel runs against the package as it exists right now. If a reviewer finds a blocker, note it — do not patch it and ask the next reviewer or Reviewer 5 to treat the fix as reviewed.

**Fixing mid-cycle and then having Reviewer 5 adjudicate as if the fix had been reviewed is a protocol violation.** Reviewer 5 must adjudicate what Reviewers 1–4 actually saw, not what was patched between runs.

Fixes happen only after Reviewer 5 issues the cycle's verdict, the gate returns `FAIL_AUTOFIX_REQUIRED`, and you move to `11_FIX_CYCLE.md`.

### Universal reviewer conduct

These rules apply to every reviewer without exception:

- Do not be charitable. Assume the executor is overconfident. Assume summaries may be stale. Assume "almost done" is a failure.
- Do not praise.
- Do not summarize the implementation unless needed to explain a blocker.
- Fail closed. When in doubt, flag it.
- Reviewers 1–4 classify each finding as BLOCKING or NON-BLOCKING. They do not issue verdicts.
- The implementer cannot override any reviewer's findings.

### Check the cycle counter before starting

Open `reports/<task_area>/CYCLE_TRACKER.md`. Record that this cycle is beginning and which cycle number it is.

If this is Cycle 6 or beyond, stop — go to `13_BLOCKED_HANDOFF.md` (maximum cycles reached).

---

## Required pre-panel gate check

Before running any reviewer, confirm:

- `reports/<task_area>/ENFORCEMENT_AUTHORITY_AUDIT.md` exists (if applicable) and records `PASS` or `NOT_APPLICABLE`
- If the task involves enforcement/gating/control and this file is absent or records a FAIL, do not proceed — return to `14_ENFORCEMENT_AUTHORITY_AUDIT.md`

## Report files to create this cycle

All four must be written fresh this cycle, even if earlier cycles produced versions:

```
reports/<task_area>/COLD_REVIEW_REQUIREMENTS_AUDIT.md
reports/<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md
reports/<task_area>/COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md
reports/<task_area>/COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md
reports/<task_area>/COLD_REVIEW_ADJUDICATION.md
```

---

## Routing — run reviewers in order

Read and execute each reviewer file in sequence. Do not skip any. Do not jump ahead to R5 before R1–R4 are complete.

| Step | File |
|---|---|
| Reviewer 1 | `05_R1_REQUIREMENTS.md` |
| Reviewer 2 | `06_R2_ACTIVE_PROOF.md` |
| Reviewer 3 | `07_R3_AI_PATTERNS.md` |
| Reviewer 4 | `08_R4_HANDOFF.md` |
| Reviewer 5 | `09_R5_ADJUDICATION.md` (only after R1–R4 are all complete) |

**Next step:** Read `05_R1_REQUIREMENTS.md`.
