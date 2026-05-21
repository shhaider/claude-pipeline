# Gate 5.2-R1 Self-Test Re-run

**Date:** 2026-05-01
**Command:**
```bash
cd /Users/syedhaider/Downloads/gate && python3 tests/test_check_gate_package.py
```

**Final exit code:** 0
**Result:** 36 passed, 0 failed

## Full output

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
```

## Coverage of R1 fixtures

The 15 R1 fixture-based tests appear at the end of the suite (lines 22-36 of output) and all PASS:

- test_missing_checker_report_final_mode
- test_absolute_raw_output_outside_package
- test_absolute_host_path_plus_package_copy
- test_lite_profile_missing_risk_task
- test_missing_not_applicable_proof
- test_empty_not_applicable_reason
- test_not_applicable_with_reason
- test_dirty_git_status_active_parallel_work
- test_dirty_git_status_ambient_doc_commit
- test_dirty_git_status_unknown_requires_human
- test_dirty_git_status_unclassified_paths
- test_output_contract_negated_token
- test_output_contract_structured_pass
- test_output_contract_structured_fail
- test_output_contract_inconsistent_verdict
- test_output_contract_actual_token_unstructured

(Note: 16 distinct R1 tests are present in the suite — slightly more than the "15 R1 fixtures" the protocol enumerates because `test_output_contract_inconsistent_verdict` reuses an R1 fixture and the structured-pass/fail and actual-token-unstructured cases are all R1 additions. All are accounted for.)

## Note on environment

Python 3.14.3. macOS (Darwin 24.6.0). No `timeout` binary available locally — the test runner is fast (single-digit seconds) so wall-clock timeout was not material here.

## Verdict

Self-tests PASS — 36/36, exit 0. Proceed to P03.
