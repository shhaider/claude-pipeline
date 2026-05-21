# Gate 5.1 Upgrade Handoff

**Date:** 2026-05-01
**Final status:** GATE_5_1_READY_FOR_REVIEW

---

## What changed (P01–P09 summary)

### P01 — Strict EXIT_CODE validation
Added to: `03_EVIDENCE_CONSISTENCY.md`, `23_REQUIRED_TEST_SET_EXACTNESS.md`, `REQUIRED_TEST_SET_EXACTNESS_TEMPLATE.md`, `SCRIPT_SPEC_check_gate_package.md`

Six blocking EXIT_CODE flags: `EXIT_CODE_MISSING`, `EXIT_CODE_BLANK`, `EXIT_CODE_NON_NUMERIC`, `EXIT_CODE_NONZERO`, `EXIT_CODE_CONFLICTING`, `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW`. All are BLOCKING. Required regex: `^EXIT_CODE:0\s*$`.

### P02 — Post-PASS uncaught error detection
Added to: `03_EVIDENCE_CONSISTENCY.md`, `22_WARNING_OUTPUT_AUDIT.md`, `WARNING_OUTPUT_AUDIT_TEMPLATE.md`, `SCRIPT_SPEC_check_gate_package.md`

New blocking flag: `POST_PASS_UNCAUGHT_ERROR`. Triggered by Error:, ENOENT, UnhandledPromiseRejection, uncaughtException, Jest did not exit, or stack traces appearing AFTER a PASS summary line. Blocking unless explicitly justified with evidence.

### P03 — Manifest-driven raw output discovery
Added to: `15_FINAL_PACKAGE_AUDIT.md`, `22_WARNING_OUTPUT_AUDIT.md`, `23_REQUIRED_TEST_SET_EXACTNESS.md`, `SCRIPT_SPEC_check_gate_package.md`, `PACKAGE_MANIFEST_TEMPLATE.md`, `EVIDENCE_LEDGER_TEMPLATE.yaml`

Raw outputs must be registered as `artifact_type: raw_test_output` in EVIDENCE_LEDGER.yaml or listed in PACKAGE_MANIFEST.md "Raw Test Outputs" section. The checker discovers raw outputs from manifest/ledger, not by scanning named directories.

### P04 — Executable checker
Created: `tools/check_gate_package.py` (working Python 3 script, 0 pip dependencies).

Checks: required proof files, gate source, EXIT_CODE strict, post-PASS errors, package stat files, manifest self-size, git status proof, REQUIRED_TEST_SET_EXACTNESS, WARNING_OUTPUT_AUDIT, checker report. Gate Full requires checker to exit 0.

### P05 — Pre-PASS barrier in transition rules
Updated: `TRANSITION_RULES.md`, `10_GATE_VERDICT.md`

Added explicit pre-PASS barrier: GATE_VERDICT cannot issue PASS unless every required audit state is PASS/OK/NOT_APPLICABLE. Routing defined for all 20 blocking states including all EXIT_CODE and POST_PASS flags.

### P06 — Proof-file profile inconsistencies fixed
Updated: `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`

GATE_STANDARD: `WARNING_OUTPUT_AUDIT.md` and `REQUIRED_TEST_SET_EXACTNESS.md` moved from `required_conditional` to `required_always` (matching prose in GATE_PROFILES.md). GATE_FULL: `GATE_PACKAGE_VALIDATION_REPORT.md` added to `required_always`.

### P07 — Proof files must be exported
Updated: `PROOF_FILE_REQUIREMENTS.md`, `15_FINAL_PACKAGE_AUDIT.md`, `PACKAGE_MANIFEST_TEMPLATE.md`, `12_PASS_HANDOFF.md`

Hard rule: every required proof file must be physically included in the exported package. Comprehensive mandatory package contents list added to `12_PASS_HANDOFF.md`. Local path to gate is not proof — must include `gate_used/` or `gate_hash.txt`.

### P08 — Self-test fixtures and executable tests
Created: `tests/test_check_gate_package.py` (7 tests), 8 fixture directories (28+ files).

All 7 tests pass. Exercises: blank EXIT_CODE, post-PASS ENOENT, missing raw output, stale manifest self-size, missing gate source, missing required proof file, happy path.

### P09 — Usage guide
Created: `GATE_5_1_USAGE_GUIDE.md`. Updated: `00_START.md`.

---

## Would M77-P05A's blank EXIT_CODE be caught?

**Yes — mechanically.**

The blank EXIT_CODE failure:
1. `check_gate_package.py` calls `check_exit_code_strict()`
2. `EXIT_CODE_LINE_RE.findall(content)` finds `EXIT_CODE:` line
3. Value after stripping = `""` (empty string)
4. Branch: `value == ""` → emits flag `EXIT_CODE_BLANK` — FAIL
5. Checker exits nonzero
6. Gate Full requires checker exit 0 → PASS cannot be issued

Test fixture: `tests/fixtures/blank_exit_code/` — `test_blank_exit_code` passes, confirming mechanical detection.

---

## Would M77-P05A's post-PASS ENOENT be caught?

**Yes — mechanically.**

The ENOENT failure:
1. `check_gate_package.py` calls `check_post_pass_uncaught_errors()`
2. PASS summary line found at line N in raw output
3. Lines after PASS searched for `ENOENT` pattern
4. `ENOENT` found → emits flag `POST_PASS_UNCAUGHT_ERROR` — FAIL
5. Checker exits nonzero
6. Gate Full requires checker exit 0 → PASS cannot be issued

Test fixture: `tests/fixtures/post_pass_enoent/` — `test_post_pass_enoent` passes.

---

## M77-P05A failure classification

**MIXED** (confirmed by P00 baseline audit):

1. **GATE_NOT_FOLLOWED_STRICTLY** — Existing Warning Output Audit rules, if followed strictly, should have caught the post-PASS ENOENT (ENOENT was in the grep pattern). A strict reviewer would have classified it BLOCKING.

2. **GATE_MISSING_EXECUTABLE_ENFORCEMENT** — No executable checker existed. Without it, all checks depend on human/agent reading discipline. This is the primary structural gap.

3. **GATE_MISSING_CHECK** — `EXIT_CODE_BLANK` was not defined. The existing `EXIT_CODE_MISSING` flag did not cover blank-value EXIT_CODE lines. Gate 5.1 adds this case.

4. **GATE_RULE_AMBIGUITY** — No explicit "post-PASS position" detection rule existed. ENOENT could be classified as REQUIRES_FOLLOWUP without violating any existing rule.

---

## Profile selection — when to use each

| Profile | When to use | Minimum for |
|---|---|---|
| GATE_LITE | D0-D1: docs-only, single-line leaf module fixes | Nothing with tests |
| GATE_STANDARD | D2: normal feature work, non-hot modules | Has tests |
| GATE_FULL | D2-hot, D3, D4: hot files, migrations, merge verification, live behavior claims | Merge verification, package signout, hot files, migrations |

**Rule of thumb:** When in doubt between GATE_STANDARD and GATE_FULL, choose GATE_FULL.

---

## How to run the checker

```bash
python3 /Users/syedhaider/Downloads/gate/tools/check_gate_package.py \
    --package <your-export-package-folder> \
    --profile GATE_FULL \
    --task-area <task_area> \
    --gate-dir /Users/syedhaider/Downloads/gate
```

Exits 0 = PASS. Exits 1 = FAIL (fix and rerun). Exits 2 = configuration error.

---

## Mandatory proof files (Gate Full)

- GATE_PROFILE_SELECTION.md
- CURRENT_STATE.yaml
- CYCLE_TRACKER.md
- CLAIMS_LEDGER.yaml, EVIDENCE_LEDGER.yaml, STALE_FILE_REGISTER.yaml
- All 5 cold review reports (R1–R5)
- HANDOFF.md
- EVIDENCE_ADEQUACY_ASSESSMENT.md, EVIDENCE_CONSISTENCY_REGISTER.md
- PROMPT_CONTRACT_REVIEW.md, PRODUCTION_CALLER_AUDIT.md, CONSUMER_API_PROOF_AUDIT.md
- WARNING_OUTPUT_AUDIT.md, REQUIRED_TEST_SET_EXACTNESS.md
- STRANDED_HELPER_AUDIT.md, EXPORT_CHANNEL_AUDIT.md, DIFF_BASE_SCOPE_AUDIT.md
- DIRTY_WORKTREE_RECURRENCE.md, FLAKE_TIMEOUT_AUDIT.md
- DOWNSTREAM_CONSUMER_READINESS.md, NEXT_PROMPT_DECISION.md
- CTO_OPERATOR_INSIGHT_REVIEW.md, GATE_EFFECTIVENESS_LOG.md
- package_file_sizes.txt, package_file_hashes.txt
- GATE_PACKAGE_VALIDATION_REPORT.md (from checker)
- gate_used/ OR gate_hash.txt
- All raw test outputs (registered as artifact_type: raw_test_output)
- Final git status proof file

---

## Known limitations

1. `GATE_PACKAGE_VALIDATION_REPORT.md` circular dependency: checker skips this check on first run. Include report in package, then rerun.
2. PyYAML optional: install with `pip3 install pyyaml`. Without it, some YAML-dependent checks are skipped.
3. NOT_APPLICABLE file validation is informational (warn, not fail) — checker cannot determine if a state should have been skipped.
4. Manifest self-size regex: covers common formats; unusual manifest formats may not be detected.

---

## Open questions

1. Should the checker be integrated into CI/CD automatically? Currently must be run manually.
2. Should `EXIT_CODE:0` with optional whitespace (`EXIT_CODE: 0`) be accepted? Currently requires no space. The spec says no space — consistency is more important than flexibility.
3. The `weak_profile` fixture (Fixture 5) was created but the checker does not yet enforce profile escalation triggers (e.g., rejecting GATE_LITE for merge verification). This would require parsing the task prompt or GATE_PROFILE_SELECTION.md for escalation triggers. Current check only verifies profile is a valid value.
