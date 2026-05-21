# Gate 5.2-R1 — Changed Files

## Modified files (existing)

| Path | Purpose |
|---|---|
| `tools/check_gate_package.py` | Added `_is_path_in_package` helper; updated `RawOutputRef` with leak-tracking fields; rewrote `register_raw_ref` to detect host-path leakage and accept `package_relative_override`; updated `discover_raw_test_outputs` to read `provenance_host_path`/`package_relative_path`; added host-path leak check in `check_exit_code_strict`; made `MISSING_RISK_TIER`/`MISSING_TASK_KIND`/`MISSING_PROFILE_REASON` apply to all profiles in `resolve_profile_context`; rewrote `check_not_applicable_files` from advisory to hard-blocking with substantive-reason check; rewrote `check_final_git_status` to use the 4-label whitelist plus `UNKNOWN_REQUIRES_HUMAN_BLOCKER` and `DIRTY_PATH_NOT_CLASSIFIED` flags; rewrote `check_output_contract_consistency` to prefer a structured YAML verdict block and fall back to a negation-aware prose scan |
| `tests/test_check_gate_package.py` | Added 15 new test functions covering P01–P05 and registered them in `main()` |
| `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` | Trimmed `GATE_LITE.not_applicable_proof_required` from 19 entries to 8 (the ones operators actually want enforced) now that the list is hard-blocking |
| `GATE_PROFILES.md` | Added Gate 5.2-R1 mandatory profile-metadata table |
| `GATE_PROFILE_SELECTOR.md` | Added Gate 5.2-R1 mandatory metadata note |
| `GATE_5_2_USAGE_RULE.md` | Added Gate 5.2-R1 hardening summary, expanded approved dirty-label list, refreshed operator checklist |
| `PROOF_FILE_REQUIREMENTS.md` | Added "NOT_APPLICABLE Proof Hard Requirement (Gate 5.2-R1)" section |
| `DIRTY_WORKTREE_RECURRENCE_TEMPLATE.md` | Added 4-label whitelist with usage guide and example multi-row classification table |
| `15_FINAL_PACKAGE_AUDIT.md` | Appended Gate 5.2-R1 sections for structured verdict, host-path leak, profile metadata, NA proof requirement |
| `16_CANONICAL_HANDOFF_AUDIT.md` | Appended structured-verdict reference |
| `GATE_PROFILE_SELECTION_TEMPLATE.md` | Updated YAML selector output template to require all four mandatory fields |

## New files

### Templates / docs

| Path | Purpose |
|---|---|
| `OUTPUT_CONTRACT_CONSISTENCY_AUDIT_TEMPLATE.md` | Copyable template with structured verdict block |

### Reports

| Path | Purpose |
|---|---|
| `reports/gate-5-2-r1/GATE_5_2_R1_BASELINE.md` | Baseline self-test + Lane D verification before R1 |
| `reports/gate-5-2-r1/GATE_5_2_R1_CHANGED_FILES.md` | This file |
| `reports/gate-5-2-r1/GATE_5_2_R1_SELF_TEST_RESULTS.md` | Final self-test + happy-path + Lane D output |
| `reports/gate-5-2-r1/GATE_5_2_R1_FAILURE_FIX_VERIFICATION.md` | Per-P-step failure mode → flag → fixture mapping |
| `reports/gate-5-2-r1/GATE_5_2_R1_HANDOFF.md` | Top-level handoff |

### Fixtures

| Path | Profile | Verdict | Validates |
|---|---|---|---|
| `tests/fixtures/absolute_raw_output_outside_package/` | GATE_FULL | FAIL | P01 host-path leak with no in-package copy |
| `tests/fixtures/absolute_host_path_plus_package_copy/` | GATE_FULL | PASS | P01 host provenance + package-relative copy |
| `tests/fixtures/lite_profile_missing_risk_task/` | GATE_LITE | FAIL | P02 risk_tier/task_kind missing on Lite |
| `tests/fixtures/missing_not_applicable_proof/` | GATE_STANDARD | FAIL | P03 NA proof file missing |
| `tests/fixtures/empty_not_applicable_reason/` | GATE_STANDARD | FAIL | P03 NA file present but heading-only |
| `tests/fixtures/not_applicable_with_reason/` | GATE_STANDARD | PASS | P03 substantive NA reasons |
| `tests/fixtures/dirty_git_status_active_parallel_work/` | GATE_FULL | PASS | P04 ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH |
| `tests/fixtures/dirty_git_status_ambient_doc_commit/` | GATE_FULL | PASS | P04 AMBIENT_UNRELATED_DOC_COMMIT |
| `tests/fixtures/dirty_git_status_unknown_requires_human/` | GATE_FULL | FAIL | P04 UNKNOWN_REQUIRES_HUMAN blocker |
| `tests/fixtures/dirty_git_status_unclassified_paths/` | GATE_FULL | FAIL | P04 dirty path missing from classification |
| `tests/fixtures/output_contract_negated_token/` | GATE_FULL | PASS | P05 negated token in fallback prose scan |
| `tests/fixtures/output_contract_structured_pass/` | GATE_FULL | PASS | P05 structured verdict PASS |
| `tests/fixtures/output_contract_structured_fail/` | GATE_FULL | FAIL | P05 structured verdict FAIL |
| `tests/fixtures/output_contract_inconsistent_verdict/` | GATE_FULL | FAIL | P05 verdict-vs-findings inconsistency |
| `tests/fixtures/output_contract_actual_token_unstructured/` | GATE_FULL | FAIL | P05 positive prose detection in fallback |

Total: 11 modified + 16 new = 27 file changes; 15 new fixtures; 15 new tests.
