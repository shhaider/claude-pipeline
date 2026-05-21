# Gate 5.1 Changed Files

**Date:** 2026-05-01

---

## Files modified (existing files)

| File | What changed |
|---|---|
| `03_EVIDENCE_CONSISTENCY.md` | Added EXIT_CODE Validation hard rule (6 flags, all BLOCKING); added Post-PASS Uncaught Error Detection hard rule (POST_PASS_UNCAUGHT_ERROR flag); updated RAW_TEST_OUTPUT_TABLE columns |
| `22_WARNING_OUTPUT_AUDIT.md` | Added EXIT_CODE scan table; added post-PASS error scan section; defined POST_PASS_UNCAUGHT_ERROR flag; updated warning classification table with position column |
| `23_REQUIRED_TEST_SET_EXACTNESS.md` | Updated required table to include EXIT_CODE parsed/flag and post-pass columns; updated Check 3 to define all 6 EXIT_CODE flags; added manifest-driven raw output discovery rule; added 5 new hard rules |
| `REQUIRED_TEST_SET_EXACTNESS_TEMPLATE.md` | Updated required table columns; added EXIT_CODE_BLANK, EXIT_CODE_NON_NUMERIC, EXIT_CODE_CONFLICTING, EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW, POST_PASS_UNCAUGHT_ERROR, RAW_OUTPUT_NOT_IN_MANIFEST flags |
| `WARNING_OUTPUT_AUDIT_TEMPLATE.md` | Added EXIT_CODE scan table; added post-PASS error scan table; added position column to warning classification table; added POST_PASS_UNCAUGHT_ERROR classification |
| `SCRIPT_SPEC_check_gate_package.md` | Replaced verify_raw_output_exit_codes() spec with strict version; added verify_post_pass_uncaught_errors() spec; added verify_raw_outputs_in_manifest() spec; updated main() to include Gate 5.1 checks |
| `15_FINAL_PACKAGE_AUDIT.md` | Added manifest-driven raw output discovery rule; added required proof files export check; added pre-PASS barrier checklist |
| `TRANSITION_RULES.md` | Added pre-PASS barrier section (REQUIRED_PROFILE_AUDITS_VERIFIED) with routing for all 20 blocking states including EXIT_CODE flags and POST_PASS_UNCAUGHT_ERROR |
| `10_GATE_VERDICT.md` | Added pre-PASS barrier checklist before routing |
| `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` | Moved WARNING_OUTPUT_AUDIT.md and REQUIRED_TEST_SET_EXACTNESS.md from required_conditional to required_always for GATE_STANDARD; added GATE_PACKAGE_VALIDATION_REPORT.md to GATE_FULL required_always |
| `PROOF_FILE_REQUIREMENTS.md` | Strengthened gate source folder requirement; added Proof File Export Requirement section listing all mandatory package contents |
| `PACKAGE_MANIFEST_TEMPLATE.md` | Added Raw Test Outputs section with EXIT_CODE/post-pass columns |
| `EVIDENCE_LEDGER_TEMPLATE.yaml` | Documented raw_test_output as a named artifact_type with required fields |
| `12_PASS_HANDOFF.md` | Expanded "Include in the package" to comprehensive mandatory list for Gate 5.1 |
| `00_START.md` | Added Gate 5.1 callout with key changes and link to GATE_5_1_USAGE_GUIDE.md |

---

## Files created (new files)

| File | Description |
|---|---|
| `tools/check_gate_package.py` | Working Python 3 executable checker — validates EXIT_CODE, post-PASS errors, required proof files, manifest integrity |
| `GATE_5_1_USAGE_GUIDE.md` | Usage guide for Gate 5.1 — what changed, when to use each profile, checker usage, prompt snippet |
| `tests/test_check_gate_package.py` | 7-test self-test suite for the checker |
| `tests/fixtures/blank_exit_code/` (4 files) | Fixture: blank EXIT_CODE — expected FAIL |
| `tests/fixtures/post_pass_enoent/` (4 files) | Fixture: ENOENT after PASS — expected FAIL |
| `tests/fixtures/missing_raw_output/` (4 files) | Fixture: raw output absent from package — expected FAIL |
| `tests/fixtures/manifest_stale_self_size/` (4 files) | Fixture: manifest self-size 0 — expected FAIL |
| `tests/fixtures/weak_profile/` (2 files) | Fixture: GATE_LITE for merge verification — expected FAIL |
| `tests/fixtures/missing_gate_source/` (4 files) | Fixture: no gate_used/ or gate_hash.txt — expected FAIL |
| `tests/fixtures/missing_required_proof_file/` (3 files) | Fixture: CYCLE_TRACKER.md absent for Gate Full — expected FAIL |
| `tests/fixtures/happy_path_gate_full/` (28 files) | Fixture: minimal valid Gate Full package — expected PASS |
| `reports/gate-5-1-upgrade/GATE_5_1_BASELINE_AUDIT.md` | P00 baseline audit |
| `reports/gate-5-1-upgrade/GATE_5_1_SELF_TEST_RESULTS.md` | P10 self-test results |
| `reports/gate-5-1-upgrade/GATE_5_1_CHANGED_FILES.md` | This file |
| `reports/gate-5-1-upgrade/GATE_5_1_HANDOFF.md` | Final handoff |

---

## Files NOT modified (out of scope, confirmed untouched)

- All project runtime/source code
- All gate step files not listed above (01, 02, 04, 05–09, 11, 13–14, 16–19, 20–21, 24–36, etc.)
- All template files not listed above
- All GATE_4_1_USAGE_GUIDE.md (preserved, Gate 5.1 guide is separate)
- All YAML/template/example files not listed above
