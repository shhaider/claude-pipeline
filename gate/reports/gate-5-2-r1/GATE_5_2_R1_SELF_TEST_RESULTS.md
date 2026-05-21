# Gate 5.2-R1 — Self-test and cross-check results

## Self-test suite

Command:
```bash
cd /Users/syedhaider/Downloads/gate && python3 tests/test_check_gate_package.py
```

Output:
```
============================================================
Gate 5.2 self-tests — check_gate_package.py
============================================================
PASS: test_blank_exit_code
PASS: test_post_pass_enoent
PASS: test_missing_raw_output
PASS: test_manifest_stale_self_size
PASS: test_missing_gate_source
PASS: test_missing_required_proof_file
PASS: test_happy_path_gate_full
PASS: test_summary_claims_exit0_raw_missing_exit_code
PASS: test_summary_claims_exit0_raw_blank_exit_code
PASS: test_raw_has_exact_exit0
PASS: test_stale_runtime_scope_labels
PASS: test_matching_runtime_scope_labels
PASS: test_wrong_profile_lite_for_merge
PASS: test_correct_profile_full_for_merge
PASS: test_wrong_path_proof_file
PASS: test_dirty_git_status_unclassified
PASS: test_dirty_git_status_task_relevant
PASS: test_dirty_git_status_classified_unrelated
PASS: test_warning_audit_blocking_prose
PASS: test_warning_audit_expected_non_blocking_only
PASS: test_missing_checker_report_final_mode
PASS: test_absolute_raw_output_outside_package
PASS: test_absolute_host_path_plus_package_copy
PASS: test_lite_profile_missing_risk_task
PASS: test_missing_not_applicable_proof
PASS: test_empty_not_applicable_reason
PASS: test_not_applicable_with_reason
PASS: test_dirty_git_status_active_parallel_work
PASS: test_dirty_git_status_ambient_doc_commit
PASS: test_dirty_git_status_unknown_requires_human
PASS: test_dirty_git_status_unclassified_paths
PASS: test_output_contract_negated_token
PASS: test_output_contract_structured_pass
PASS: test_output_contract_structured_fail
PASS: test_output_contract_inconsistent_verdict
PASS: test_output_contract_actual_token_unstructured
------------------------------------------------------------
36 passed, 0 failed
============================================================
EXIT: 0
```

**Result: 36/36 PASS (21 baseline + 15 new for Gate 5.2-R1).**

---

## Cross-check 1 — happy_path_gate_full fixture

Command:
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/happy_path_gate_full \
  --profile GATE_FULL --task-area happy_path_gate_full \
  --risk-tier D3 --task-kind merge_verification \
  --gate-dir . --final
```

Output (final lines):
```
Result: PASS
Checks passed: 45  |  Checks failed: 0
EXIT: 0
```

**Result: PASS — no regression.**

---

## Cross-check 2 — Lane D production package (METAOS_AUDIT_LANE_D_SIGNOUT.zip)

Command:
```bash
mkdir -p /tmp/lane_d_for_r1_check_final
cd /tmp/lane_d_for_r1_check_final
unzip -o /Users/syedhaider/Downloads/METAOS_AUDIT_LANE_D_SIGNOUT.zip > /dev/null
python3 /Users/syedhaider/Downloads/gate/tools/check_gate_package.py \
  --package /tmp/lane_d_for_r1_check_final \
  --profile GATE_FULL --task-area metaos_audit_lane_d \
  --gate-dir /Users/syedhaider/Downloads/gate
```

Output (final lines):
```
Result: PASS
Checks passed: 61  |  Checks failed: 0
EXIT: 0
```

**Result: PASS — no regression. The Lane D package was validated under unmodified Gate 5.2 and remains green under Gate 5.2-R1 hardening.**

---

## Regression summary

- Self-tests: 36/36 PASS, 0 regressions vs. baseline 21/21.
- happy_path fixture: PASS, 0 regressions.
- Lane D production package: PASS (61/61), 0 regressions.

**Zero regressions introduced by Gate 5.2-R1 hardening pass.**
