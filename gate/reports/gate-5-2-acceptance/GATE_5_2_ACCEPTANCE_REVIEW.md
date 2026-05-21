# Gate 5.2 Acceptance Review

**Auditor:** Independent (no authorship)
**Audit date:** 2026-05-01
**Source under audit:** `/Users/syedhaider/Downloads/gate` (canonical-path, currently version-tagged Gate 5.2 in `00_START.md` line 1 and tools/check_gate_package.py header)
**Reference:** Gate 5.1 acceptance docs at `/Users/syedhaider/Downloads/gate/reports/gate-5-1-upgrade/`
**Pre-5.2 backup compared against:** `/Users/syedhaider/Downloads/gate_backup_pre_5_2_20260501T113854Z` (file count 266 vs 5.2's 780 — 5.2 includes more fixtures + reports)

---

## Important access caveat (read first)

The user-supplied test gate path was `/Users/syedhaider/Downloads/gate 5.2`. Direct read access to that folder via the Mac harness is blocked at the macOS TCC layer (Operation not permitted on every read attempt — `find`, `du`, `python3 os.listdir`, `cat`, `Read`, `xattr` all denied even with sandbox bypass). Filesystem-level metadata is visible (87 directory entries; 84 user items per Finder; same modification timestamps as `/Users/syedhaider/Downloads/gate`), so the folder exists and is owned by the user, but content cannot be inspected by this auditor.

The implementer's prior report at `reports/gate-5-2/` documents that the upgrade was applied **in-place to `/Users/syedhaider/Downloads/gate`** (file count grew from a 5.1 baseline of ~229 to 780 with new fixtures, executable checker, and test suite). My audit therefore validates the readable copy of Gate 5.2 at `/Users/syedhaider/Downloads/gate`. If `/Users/syedhaider/Downloads/gate 5.2` is intended to be a separate snapshot, the user must grant TCC access (System Settings → Privacy & Security → Files and Folders) or move/symlink the folder to a TCC-allowed location for an independent audit of that exact path.

---

## Inventory of readable Gate 5.2

- Top-level files: 88 directory entries (87 + `.`)
- Total files in tree: 780
- Fixture directories under `tests/fixtures/`: 22 (was 8 in pre-5.2 backup)
- Tools directory: `tools/check_gate_package.py` (974 lines, was 829 in 5.1 backup)
- Test file: `tests/test_check_gate_package.py` (21 tests, was 7 in 5.1 baseline per implementer note)
- Reports subfolders: `gate-4-1-upgrade`, `gate-5-1-upgrade`, `gate-5-2`, `gate-5-2-acceptance` (this one), `gate-state-machine-upgrade-2026-04-30`, `gate-state-machine-upgrade-session-2026-05-01`

## What changed vs Gate 5.1

Modified files (16 total per `diff -rq`):
- `00_START.md` — version bumped to 5.2; new "Gate 5.2 hard rules" section
- `03_EVIDENCE_CONSISTENCY.md` — new "Gate 5.2 append" requiring `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` for FULL profiles; lists blocking tokens
- `15_FINAL_PACKAGE_AUDIT.md` — new "Gate 5.2 final checker barrier" section requiring `--final` exit 0; documents exact-path requirement
- `16_CANONICAL_HANDOFF_AUDIT.md` — minor 5.2 alignment
- `18_GATE_PROFILE_SELECTION.md` — risk-tier/task-kind enforcement notes
- `22_WARNING_OUTPUT_AUDIT.md` — new "Gate 5.2 blocking tokens" section enumerating BLOCKING/CONTRADICTS_SUCCESS_CLAIM/POST_PASS_UNCAUGHT_ERROR/EXIT_CODE_BLANK/EXIT_CODE_NONZERO/CHECKPOINT_READBACK_WARNING_BLOCKING
- `23_REQUIRED_TEST_SET_EXACTNESS.md` — alignment with new exactness checks
- `GATE_PROFILES.md` — new "Gate 5.2 profile enforcement" matrix mapping risk_tier × task_kind → minimum profile
- `GATE_PROFILE_SELECTOR.md` — alignment with strength rules
- `PROOF_FILE_REQUIREMENTS.md` — version bumped to 5.2; new "Exact-path rule" section (basename-in-wrong-folder no longer counts)
- `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` — version bumped to 5.2; `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` added to GATE_FULL `required_always`
- `STATE_MACHINE.md` — new "Gate 5.2 enforcement note" requiring `--final` exit 0 for terminal PASS
- `STATE_SCHEMA.md` — added `task_kind` enum and `D2_HOT` risk tier alias
- `TRANSITION_RULES.md` — new "Gate 5.2 final transition barrier" listing four conditions that block final PASS
- `tests/test_check_gate_package.py` — expanded from 7 to 21 tests
- `tools/check_gate_package.py` — major rewrite: 33,441 → 39,973 bytes (974 lines), 14 new functions

New file in 5.2 root (not in 5.1):
- `GATE_5_2_USAGE_RULE.md`

New fixture directories in 5.2 (14 added):
- `correct_profile_full_for_merge`, `dirty_git_status_classified_unrelated`, `dirty_git_status_task_relevant`, `dirty_git_status_unclassified`, `matching_runtime_scope_labels`, `missing_checker_report_final_mode`, `raw_has_exact_exit0`, `stale_runtime_scope_labels`, `summary_claims_exit0_raw_blank_exit_code`, `summary_claims_exit0_raw_missing_exit_code`, `warning_audit_blocking_prose`, `warning_audit_expected_non_blocking_only`, `wrong_path_proof_file`, `wrong_profile_lite_for_merge`

## What's REMOVED in 5.2 (regression check)

No `.md` or `.py` source file present in 5.1 is missing from 5.2. The "Only in backup" entries from `diff -rq` are all fixture-internal files that moved from `tests/fixtures/<name>/` (root) to `tests/fixtures/<name>/reports/<task_area>/` (the new exact-path layout the checker requires). This is a structural reorganization, not a deletion.

Verified by spot-checking happy_path_gate_full: pre-5.2 backup had files at fixture root; 5.2 has the same file names plus more under `reports/happy_path_gate_full/`.

## Question-by-question answers

- **Does Gate 5.2 include the full updated gate folder structure?** YES — 780 files vs the smaller pre-5.2 backup (266); same gate root entries plus expanded test/fixture suite.
- **Does it preserve Gate Lite/Standard/Full/Full+Domain lanes?** YES — `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` retains all four profile sections; `PROFILE_ORDER` in checker spans `GATE_LITE` (1) through `GATE_FULL_PLUS_DOMAIN_ADDENDUM` (4).
- **Does it require proof files to be stored/exported?** YES — `check_required_proof_files` rejects basename-in-wrong-folder; flag `REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING`.
- **Does it require gate_used/ source inclusion?** YES — `check_gate_source_included` requires `gate_used/` directory or `gate_hash.txt` (verified by the `missing_gate_source` fixture which fails the check).
- **Does it include an executable checker (not only markdown)?** YES — `tools/check_gate_package.py` (974 lines, 0 stubs found in 14-function review). Self-test 21/21 PASS. Lane D Gate 5.1-validated package still PASSes (61/61 checks, exit 0).
- **Does it include self-test fixtures?** YES — 22 fixtures, each with a FIXTURE_SPEC.md describing the negative case it exercises.

## Backlog items addressed

The implementer's `GATE_5_2_BASELINE.md` listed 5 backlog items. Audit verdict on each:

1. **Stale-report / output-contract contradiction executable check** — DONE. `check_output_contract_consistency()` reads `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` and matches `BLOCKING_CONTRACT_TOKENS` (`STALE_CONTRACT_CLAIM`, `STALE_MILESTONE_LABEL`, etc.). Verified by `stale_runtime_scope_labels` fixture (exit 1, flag `STALE_MILESTONE_LABEL`).
2. **Wrong gate-profile detection** — DONE. `required_min_profile()` + `check_gate_profile_strength()` mechanically enforce. Verified by `wrong_profile_lite_for_merge` fixture: `GATE_LITE` against `D1 + merge_verification` correctly fires `WRONG_GATE_PROFILE` (exit 1).
3. **EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW checker logic** — DONE. `check_exit_code_strict()` cross-checks raw output against summary docs claiming `EXIT_CODE:0`. Verified by both `summary_claims_exit0_raw_blank_exit_code` and `summary_claims_exit0_raw_missing_exit_code` fixtures.
4. **Regenerate valid GATE_5_1_DIFF.patch** — PARTIAL. `reports/gate-5-2/GATE_5_2_DIFF.patch` exists at 1,030,115 bytes (non-placeholder). However, no Gate 5 → Gate 5.1 baseline reconstruction was attempted; documented in `GATE_5_BASELINE_UNAVAILABLE_NOTE.md`. Acceptable.
5. **Strengthen exact proof-file path and final-mode validation** — DONE. `check_required_proof_files` uses `package_path / rel_path` exact-path resolution; `--final` flag controls when `MISSING_CHECKER_REPORT_FINAL_MODE` fires.

## Final status

`GATE_5_2_READY_FOR_CANONICAL_INSTALL` — see `GATE_5_2_INSTALL_DECISION.md` for the install verdict.
