#!/usr/bin/env python3
"""
Self-tests for Gate 5.2 check_gate_package.py.
"""

import os
import subprocess
import sys
import importlib.util

GATE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKER = os.path.join(GATE_DIR, "tools", "check_gate_package.py")
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SPEC = importlib.util.spec_from_file_location("check_gate_package", CHECKER)
CHECKER_MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER_MOD)


def run_checker(
    fixture_name,
    *,
    profile="GATE_FULL",
    task_area=None,
    risk_tier="D3",
    task_kind="merge_verification",
    final=False,
):
    package_path = os.path.join(FIXTURES, fixture_name)
    task_area = task_area or fixture_name
    cmd = [
        sys.executable,
        CHECKER,
        "--package",
        package_path,
        "--task-area",
        task_area,
        "--gate-dir",
        GATE_DIR,
    ]
    if profile is not None:
        cmd += ["--profile", profile]
    if risk_tier is not None:
        cmd += ["--risk-tier", risk_tier]
    if task_kind is not None:
        cmd += ["--task-kind", task_kind]
    if final:
        cmd.append("--final")
    return subprocess.run(cmd, capture_output=True, text=True)


def assert_failed(result, token):
    assert result.returncode != 0, f"expected failure\nstdout:{result.stdout}\nstderr:{result.stderr}"
    combined = result.stdout + result.stderr
    assert token in combined, f"expected token {token}\nstdout:{result.stdout}\nstderr:{result.stderr}"


def assert_passed(result):
    assert result.returncode == 0, f"expected pass\nstdout:{result.stdout}\nstderr:{result.stderr}"
    assert "Result: PASS" in result.stdout, f"expected PASS banner\nstdout:{result.stdout}\nstderr:{result.stderr}"


def test_blank_exit_code():
    assert_failed(run_checker("blank_exit_code"), "EXIT_CODE_BLANK")


def test_post_pass_enoent():
    assert_failed(run_checker("post_pass_enoent"), "POST_PASS_UNCAUGHT_ERROR")


def test_missing_raw_output():
    result = run_checker("missing_raw_output")
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "RAW_OUTPUT_DECLARED_MISSING" in combined or "REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING" in combined


def test_manifest_stale_self_size():
    result = run_checker("manifest_stale_self_size")
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "MANIFEST_SELF_SIZE_STALE" in combined or "self-size" in combined


def test_missing_gate_source():
    result = run_checker("missing_gate_source")
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "gate_source_included" in combined or "gate_hash" in combined or "gate_used" in combined


def test_missing_required_proof_file():
    assert_failed(run_checker("missing_required_proof_file"), "REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING")


def test_happy_path_gate_full():
    assert_passed(run_checker("happy_path_gate_full", final=True))


def test_summary_claims_exit0_raw_missing_exit_code():
    assert_failed(run_checker("summary_claims_exit0_raw_missing_exit_code"), "EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW")


def test_summary_claims_exit0_raw_blank_exit_code():
    assert_failed(run_checker("summary_claims_exit0_raw_blank_exit_code"), "EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW")


def test_raw_has_exact_exit0():
    assert_passed(run_checker("raw_has_exact_exit0", final=True))


def test_stale_runtime_scope_labels():
    assert_failed(run_checker("stale_runtime_scope_labels", final=True), "STALE_MILESTONE_LABEL")


def test_matching_runtime_scope_labels():
    assert_passed(run_checker("matching_runtime_scope_labels", final=True))


def test_wrong_profile_lite_for_merge():
    assert_failed(
        run_checker(
            "wrong_profile_lite_for_merge",
            profile=None,
            risk_tier=None,
            task_kind=None,
        ),
        "WRONG_GATE_PROFILE",
    )


def test_correct_profile_full_for_merge():
    assert_passed(
        run_checker(
            "correct_profile_full_for_merge",
            profile=None,
            risk_tier=None,
            task_kind=None,
            final=True,
        )
    )


def test_wrong_path_proof_file():
    assert_failed(run_checker("wrong_path_proof_file"), "REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING")


def test_dirty_git_status_unclassified():
    assert_failed(run_checker("dirty_git_status_unclassified"), "DIRTY_GIT_STATUS_UNCLASSIFIED")


def test_dirty_git_status_task_relevant():
    assert_failed(run_checker("dirty_git_status_task_relevant"), "DIRTY_GIT_STATUS_TASK_RELEVANT")


def test_dirty_git_status_classified_unrelated():
    assert_passed(run_checker("dirty_git_status_classified_unrelated", final=True))


def test_warning_audit_blocking_prose():
    assert_failed(run_checker("warning_audit_blocking_prose"), "POST_PASS_UNCAUGHT_ERROR")


def test_warning_audit_expected_non_blocking_only():
    assert_passed(run_checker("warning_audit_expected_non_blocking_only", final=True))


def test_missing_checker_report_final_mode():
    report_path = os.path.join(
        FIXTURES,
        "missing_checker_report_final_mode",
        "reports",
        "missing_checker_report_final_mode",
        "GATE_PACKAGE_VALIDATION_REPORT.md",
    )
    if os.path.exists(report_path):
        os.remove(report_path)
    assert_failed(run_checker("missing_checker_report_final_mode", final=True), "MISSING_CHECKER_REPORT_FINAL_MODE")


# -----------------------------------------------------------------------------
# Gate 5.2-R1 P01 — host-path leakage
# -----------------------------------------------------------------------------


def test_absolute_raw_output_outside_package():
    """P01-bad: absolute host path in EVIDENCE_LEDGER, no in-package copy."""
    assert_failed(
        run_checker("absolute_raw_output_outside_package"),
        "HOST_PATH_NOT_PACKAGE_EVIDENCE",
    )


def test_absolute_host_path_plus_package_copy():
    """P01-good: host provenance recorded with a sibling in-package copy passes."""
    assert_passed(run_checker("absolute_host_path_plus_package_copy", final=True))


# -----------------------------------------------------------------------------
# Gate 5.2-R1 P02 — risk_tier / task_kind / reason mandatory for ALL profiles
# -----------------------------------------------------------------------------


def test_lite_profile_missing_risk_task():
    """P02-bad: GATE_LITE without risk_tier/task_kind must fire MISSING_RISK_TIER and MISSING_TASK_KIND."""
    result = run_checker(
        "lite_profile_missing_risk_task",
        profile=None,
        risk_tier=None,
        task_kind=None,
    )
    assert result.returncode != 0, f"expected failure\nstdout:{result.stdout}\nstderr:{result.stderr}"
    combined = result.stdout + result.stderr
    assert "MISSING_RISK_TIER" in combined, f"expected MISSING_RISK_TIER\nstdout:{result.stdout}\nstderr:{result.stderr}"
    assert "MISSING_TASK_KIND" in combined, f"expected MISSING_TASK_KIND\nstdout:{result.stdout}\nstderr:{result.stderr}"


# -----------------------------------------------------------------------------
# Gate 5.2-R1 P03 — NOT_APPLICABLE proof hard requirement
# -----------------------------------------------------------------------------


def test_missing_not_applicable_proof():
    """P03-bad: GATE_STANDARD without NA proofs fires MISSING_NOT_APPLICABLE_PROOF."""
    assert_failed(
        run_checker(
            "missing_not_applicable_proof",
            profile="GATE_STANDARD",
            risk_tier="D2",
            task_kind="normal_impl",
        ),
        "MISSING_NOT_APPLICABLE_PROOF",
    )


def test_empty_not_applicable_reason():
    """P03-bad: NA proof present but heading-only fires NOT_APPLICABLE_REASON_MISSING."""
    assert_failed(
        run_checker(
            "empty_not_applicable_reason",
            profile="GATE_STANDARD",
            risk_tier="D2",
            task_kind="normal_impl",
        ),
        "NOT_APPLICABLE_REASON_MISSING",
    )


def test_not_applicable_with_reason():
    """P03-good: substantive NA reasons let the package PASS."""
    assert_passed(
        run_checker(
            "not_applicable_with_reason",
            profile="GATE_STANDARD",
            risk_tier="D2",
            task_kind="normal_impl",
            final=True,
        )
    )


# -----------------------------------------------------------------------------
# Gate 5.2-R1 P04 — approved dirty-worktree label set
# -----------------------------------------------------------------------------


def test_dirty_git_status_active_parallel_work():
    """P04-good: ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH classification passes."""
    assert_passed(run_checker("dirty_git_status_active_parallel_work", final=True))


def test_dirty_git_status_ambient_doc_commit():
    """P04-good: AMBIENT_UNRELATED_DOC_COMMIT classification passes."""
    assert_passed(run_checker("dirty_git_status_ambient_doc_commit", final=True))


def test_dirty_git_status_unknown_requires_human():
    """P04-bad: UNKNOWN_REQUIRES_HUMAN classification blocks via UNKNOWN_REQUIRES_HUMAN_BLOCKER."""
    assert_failed(
        run_checker("dirty_git_status_unknown_requires_human"),
        "UNKNOWN_REQUIRES_HUMAN_BLOCKER",
    )


def test_dirty_git_status_unclassified_paths():
    """P04-bad: classification file exists but a dirty path is not in it — DIRTY_PATH_NOT_CLASSIFIED."""
    assert_failed(
        run_checker("dirty_git_status_unclassified_paths"),
        "DIRTY_PATH_NOT_CLASSIFIED",
    )


# -----------------------------------------------------------------------------
# Gate 5.2-R1 P05 — output-contract structured verdict + negation-aware fallback
# -----------------------------------------------------------------------------


def test_output_contract_negated_token():
    """P05-good: negated prose ('No STALE_MILESTONE_LABEL found') passes the fallback scan."""
    assert_passed(run_checker("output_contract_negated_token", final=True))


def test_output_contract_structured_pass():
    """P05-good: structured verdict PASS with empty blocking_findings."""
    assert_passed(run_checker("output_contract_structured_pass", final=True))


def test_output_contract_structured_fail():
    """P05-bad: structured verdict FAIL with STALE_MILESTONE_LABEL finding blocks."""
    assert_failed(
        run_checker("output_contract_structured_fail"),
        "STALE_MILESTONE_LABEL",
    )


def test_output_contract_inconsistent_verdict():
    """P05-bad: structured verdict PASS but blocking_findings non-empty fires OUTPUT_CONTRACT_VERDICT_INCONSISTENT."""
    assert_failed(
        run_checker("output_contract_inconsistent_verdict"),
        "OUTPUT_CONTRACT_VERDICT_INCONSISTENT",
    )


def test_output_contract_actual_token_unstructured():
    """P05-bad: prose audit with 'STALE_MILESTONE_LABEL detected' (no structured block) fires."""
    assert_failed(
        run_checker("output_contract_actual_token_unstructured"),
        "STALE_MILESTONE_LABEL",
    )


# -----------------------------------------------------------------------------
# Gate 5.3 — Final Packet Auditor
# -----------------------------------------------------------------------------


def test_final_auditor_missing():
    """5.3-bad: GATE_FULL package missing FINAL_PACKET_AUDITOR_REPORT.md fires
    FINAL_PACKET_AUDITOR_MISSING."""
    assert_failed(
        run_checker("final_auditor_missing"),
        "FINAL_PACKET_AUDITOR_MISSING",
    )


def test_final_auditor_pass():
    """5.3-good: GATE_FULL package with valid PASS auditor report passes."""
    assert_passed(run_checker("final_auditor_pass", final=True))


def test_final_auditor_fail():
    """5.3-bad: auditor verdict FAIL fires FINAL_PACKET_AUDITOR_FAIL."""
    assert_failed(
        run_checker("final_auditor_fail"),
        "FINAL_PACKET_AUDITOR_FAIL",
    )


def test_final_auditor_human_decision_but_ready_status():
    """5.3-bad: HUMAN_DECISION_REQUIRED verdict with READY handoff fires
    FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED."""
    assert_failed(
        run_checker("final_auditor_human_decision_but_ready_status"),
        "FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED",
    )


def test_final_auditor_schema_invalid():
    """5.3-bad: missing RERUN_FROM field fires FINAL_PACKET_AUDITOR_SCHEMA_INVALID."""
    assert_failed(
        run_checker("final_auditor_schema_invalid"),
        "FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
    )


def test_final_auditor_beginning_rerun_but_pass_handoff():
    """5.3-bad: RERUN_FROM:BEGINNING with READY handoff fires
    FINAL_PACKET_AUDITOR_RERUN_REQUIRED."""
    assert_failed(
        run_checker("final_auditor_beginning_rerun_but_pass_handoff"),
        "FINAL_PACKET_AUDITOR_RERUN_REQUIRED",
    )


def test_final_auditor_not_applicable_lite():
    """5.3-good: GATE_LITE non-export package with substantive NA reason passes."""
    assert_passed(
        run_checker(
            "final_auditor_not_applicable_lite",
            profile="GATE_LITE",
            risk_tier="D0",
            task_kind="docs",
            final=True,
        )
    )


def test_final_auditor_not_applicable_full():
    """5.3-bad: GATE_FULL with NA file (no report) fails — Full does not allow NA for the auditor."""
    result = run_checker("final_auditor_not_applicable_full", profile="GATE_FULL")
    assert result.returncode != 0, f"expected failure\nstdout:{result.stdout}\nstderr:{result.stderr}"
    combined = result.stdout + result.stderr
    # Either the missing-file flag or the required-proof-file flag must fire.
    assert (
        "FINAL_PACKET_AUDITOR_MISSING" in combined
        or "REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING" in combined
    ), f"expected missing/required-proof-file flag\nstdout:{result.stdout}\nstderr:{result.stderr}"


def test_final_auditor_structured_pass():
    assert_passed(run_checker("final_auditor_structured_pass", final=True))


def test_final_auditor_legacy_regex_report_rejected():
    assert_failed(run_checker("final_auditor_legacy_regex_report_rejected", final=True), "FINAL_PACKET_AUDITOR_SCHEMA_INVALID")


def test_final_auditor_independence_unverified():
    assert_failed(run_checker("final_auditor_independence_unverified", final=True), "FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED")


def test_final_auditor_independence_conflict():
    assert_failed(run_checker("final_auditor_independence_conflict", final=True), "FINAL_PACKET_AUDITOR_INDEPENDENCE_CONFLICT")


def test_final_auditor_independence_not_achieved_blocks_pass():
    assert_failed(run_checker("final_auditor_independence_not_achieved_blocks_pass", final=True), "FINAL_PACKET_AUDITOR_INDEPENDENCE_NOT_ACHIEVED")


def test_gate_full_plus_missing_domain_addenda():
    assert_failed(run_checker("gate_full_plus_missing_domain_addenda", profile=None, risk_tier=None, task_kind=None), "DOMAIN_ADDENDA_MISSING")


def test_gate_full_plus_missing_domain_addendum_source():
    assert_failed(run_checker("gate_full_plus_missing_domain_addendum_source", profile=None, risk_tier=None, task_kind=None), "DOMAIN_ADDENDUM_SOURCE_MISSING")


def test_gate_full_plus_missing_domain_addendum_proof():
    assert_failed(run_checker("gate_full_plus_missing_domain_addendum_proof", profile=None, risk_tier=None, task_kind=None), "DOMAIN_ADDENDUM_PROOF_MISSING")


def test_gate_full_plus_domain_addendum_pass():
    assert_passed(run_checker("gate_full_plus_domain_addendum_pass", profile=None, risk_tier=None, task_kind=None, final=True))


def test_gate_full_plus_inherits_gate_full_required_files():
    assert_failed(
        run_checker("gate_full_plus_missing_full_required_proof", profile=None, risk_tier=None, task_kind=None, final=True),
        "REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING",
    )


def test_exit_code_conflicting():
    assert_failed(run_checker("exit_code_conflicting"), "EXIT_CODE_CONFLICTING")


def test_exit_code_non_numeric():
    assert_failed(run_checker("exit_code_non_numeric"), "EXIT_CODE_NON_NUMERIC")


def test_exit_code_fenced_only():
    assert_failed(run_checker("exit_code_fenced_only"), "EXIT_CODE_MISSING")


def test_exit_code_fenced_conflicting_bare_zero():
    assert_passed(run_checker("exit_code_fenced_conflicting_bare_zero", final=True))


def test_dirty_paths_from_git_status_leading_space():
    parsed = CHECKER_MOD.dirty_paths_from_git_status(" M src/foo.py\n?? docs/note.md\nR  old.py -> new.py\n")
    assert parsed == ["src/foo.py", "docs/note.md", "old.py -> new.py"], parsed


def test_not_applicable_placeholder_reason():
    assert_failed(run_checker("not_applicable_placeholder_reason", profile="GATE_STANDARD", risk_tier="D2", task_kind="normal_impl"), "NOT_APPLICABLE_REASON_MISSING")


def test_not_applicable_zero_width_reason():
    assert_failed(run_checker("not_applicable_zero_width_reason", profile="GATE_STANDARD", risk_tier="D2", task_kind="normal_impl"), "NOT_APPLICABLE_REASON_MISSING")


def test_output_contract_not_applicable_empty_reason():
    assert_failed(run_checker("output_contract_not_applicable_empty_reason", final=True), "OUTPUT_CONTRACT_NA_REASON_MISSING")


def test_warning_audit_structured_pass():
    assert_passed(run_checker("warning_audit_structured_pass", final=True))


def test_warning_audit_structured_fail():
    assert_failed(run_checker("warning_audit_structured_fail"), "POST_PASS_UNCAUGHT_ERROR")


def test_warning_audit_fenced_example_token_only():
    assert_passed(run_checker("warning_audit_fenced_example_token_only", final=True))


def test_warning_audit_blockquote_blocking_token():
    assert_failed(run_checker("warning_audit_blockquote_blocking_token"), "POST_PASS_UNCAUGHT_ERROR")


def main():
    tests = [
        test_blank_exit_code,
        test_post_pass_enoent,
        test_missing_raw_output,
        test_manifest_stale_self_size,
        test_missing_gate_source,
        test_missing_required_proof_file,
        test_happy_path_gate_full,
        test_summary_claims_exit0_raw_missing_exit_code,
        test_summary_claims_exit0_raw_blank_exit_code,
        test_raw_has_exact_exit0,
        test_stale_runtime_scope_labels,
        test_matching_runtime_scope_labels,
        test_wrong_profile_lite_for_merge,
        test_correct_profile_full_for_merge,
        test_wrong_path_proof_file,
        test_dirty_git_status_unclassified,
        test_dirty_git_status_task_relevant,
        test_dirty_git_status_classified_unrelated,
        test_warning_audit_blocking_prose,
        test_warning_audit_expected_non_blocking_only,
        test_missing_checker_report_final_mode,
        # Gate 5.2-R1 P01
        test_absolute_raw_output_outside_package,
        test_absolute_host_path_plus_package_copy,
        # Gate 5.2-R1 P02
        test_lite_profile_missing_risk_task,
        # Gate 5.2-R1 P03
        test_missing_not_applicable_proof,
        test_empty_not_applicable_reason,
        test_not_applicable_with_reason,
        # Gate 5.2-R1 P04
        test_dirty_git_status_active_parallel_work,
        test_dirty_git_status_ambient_doc_commit,
        test_dirty_git_status_unknown_requires_human,
        test_dirty_git_status_unclassified_paths,
        # Gate 5.2-R1 P05
        test_output_contract_negated_token,
        test_output_contract_structured_pass,
        test_output_contract_structured_fail,
        test_output_contract_inconsistent_verdict,
        test_output_contract_actual_token_unstructured,
        # Gate 5.3 — Final Packet Auditor
        test_final_auditor_missing,
        test_final_auditor_pass,
        test_final_auditor_fail,
        test_final_auditor_human_decision_but_ready_status,
        test_final_auditor_schema_invalid,
        test_final_auditor_beginning_rerun_but_pass_handoff,
        test_final_auditor_not_applicable_lite,
        test_final_auditor_not_applicable_full,
        test_final_auditor_structured_pass,
        test_final_auditor_legacy_regex_report_rejected,
        test_final_auditor_independence_unverified,
        test_final_auditor_independence_conflict,
        test_final_auditor_independence_not_achieved_blocks_pass,
        test_gate_full_plus_missing_domain_addenda,
        test_gate_full_plus_missing_domain_addendum_source,
        test_gate_full_plus_missing_domain_addendum_proof,
        test_gate_full_plus_domain_addendum_pass,
        test_gate_full_plus_inherits_gate_full_required_files,
        test_exit_code_conflicting,
        test_exit_code_non_numeric,
        test_exit_code_fenced_only,
        test_exit_code_fenced_conflicting_bare_zero,
        test_dirty_paths_from_git_status_leading_space,
        test_not_applicable_placeholder_reason,
        test_not_applicable_zero_width_reason,
        test_output_contract_not_applicable_empty_reason,
        test_warning_audit_structured_pass,
        test_warning_audit_structured_fail,
        test_warning_audit_fenced_example_token_only,
        test_warning_audit_blockquote_blocking_token,
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print("Gate 5.4 self-tests — check_gate_package.py")
    print("=" * 60)
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL: {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"ERROR: {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print("-" * 60)
    print(f"{passed} passed, {failed} failed")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
