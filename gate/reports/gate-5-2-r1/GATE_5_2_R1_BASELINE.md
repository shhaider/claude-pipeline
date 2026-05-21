# Gate 5.2-R1 Baseline

**Generated at:** 2026-05-01 (R1 hardening pass entry)

## Environment

- Gate folder: `/Users/syedhaider/Downloads/gate`
- Checker path: `/Users/syedhaider/Downloads/gate/tools/check_gate_package.py`
- Python: `Python 3.14.3`
- PyYAML: `6.0.3`

## Baseline self-test result (before R1 changes)

```
Gate 5.2 self-tests — check_gate_package.py
21 passed, 0 failed
EXIT_CODE: 0
```

## Baseline Lane D cross-check

```
Result: PASS
Checks passed: 61  |  Checks failed: 0
EXIT_CODE: 0
```

## R1 issues to address

| P-step | Theme | New blocking flag(s) |
|---|---|---|
| P01 | Disallow exported-evidence host-path leakage | `HOST_PATH_NOT_PACKAGE_EVIDENCE` |
| P02 | Require profile metadata for ALL profiles (not just Standard+) | `MISSING_RISK_TIER`, `MISSING_TASK_KIND`, `MISSING_PROFILE_REASON` (now applies to LITE too) |
| P03 | Make NOT_APPLICABLE proof a hard requirement | `MISSING_NOT_APPLICABLE_PROOF`, `NOT_APPLICABLE_REASON_MISSING` |
| P04 | Approved dirty-worktree label set | `DIRTY_PATH_NOT_CLASSIFIED`, `UNKNOWN_REQUIRES_HUMAN_BLOCKER` |
| P05 | Output-contract structured verdict + negation-aware fallback | `OUTPUT_CONTRACT_VERDICT_INCONSISTENT` |

## Files planned for modification or creation

### Modified
- `tools/check_gate_package.py` — add path-containment helper, expand profile-metadata checks, harden NA proof check, expand dirty-label whitelist, add structured-verdict parser
- `tests/test_check_gate_package.py` — add ~14 new tests
- `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` — prune over-listed `not_applicable_proof_required` entries
- `GATE_PROFILE_SELECTOR.md` — note that risk_tier/task_kind/reason are mandatory for ALL profiles
- `GATE_PROFILES.md` — same
- `GATE_5_2_USAGE_RULE.md` — list 4 mandatory metadata fields, list approved dirty labels, note structured verdict block
- `PROOF_FILE_REQUIREMENTS.md` — new section for NA proof hard requirement
- `DIRTY_WORKTREE_RECURRENCE_TEMPLATE.md` — add 4 approved labels and example multi-row classification
- `15_FINAL_PACKAGE_AUDIT.md` — document structured output-contract verdict block
- `16_CANONICAL_HANDOFF_AUDIT.md` — same
- `tests/fixtures/happy_path_gate_full/...` — update so it still passes after P02/P03 hardening
- `tests/fixtures/correct_profile_full_for_merge/...` — same
- `tests/fixtures/raw_has_exact_exit0/...` — same (and any other existing fixture that the new gates affect)

### Created
- `OUTPUT_CONTRACT_CONSISTENCY_AUDIT_TEMPLATE.md` — new template with structured verdict block
- `tests/fixtures/absolute_raw_output_outside_package/...`
- `tests/fixtures/absolute_host_path_plus_package_copy/...`
- `tests/fixtures/lite_profile_missing_risk_task/...`
- `tests/fixtures/missing_not_applicable_proof/...`
- `tests/fixtures/empty_not_applicable_reason/...`
- `tests/fixtures/not_applicable_with_reason/...`
- `tests/fixtures/dirty_git_status_active_parallel_work/...`
- `tests/fixtures/dirty_git_status_ambient_doc_commit/...`
- `tests/fixtures/dirty_git_status_unknown_requires_human/...`
- `tests/fixtures/dirty_git_status_unclassified_paths/...` (some dirty paths missing from classification)
- `tests/fixtures/output_contract_negated_token/...`
- `tests/fixtures/output_contract_structured_pass/...`
- `tests/fixtures/output_contract_structured_fail/...`
- `tests/fixtures/output_contract_inconsistent_verdict/...`
- `tests/fixtures/output_contract_actual_token_unstructured/...`
- `reports/gate-5-2-r1/GATE_5_2_R1_BASELINE.md` (this file)
- `reports/gate-5-2-r1/GATE_5_2_R1_CHANGED_FILES.md`
- `reports/gate-5-2-r1/GATE_5_2_R1_SELF_TEST_RESULTS.md`
- `reports/gate-5-2-r1/GATE_5_2_R1_FAILURE_FIX_VERIFICATION.md`
- `reports/gate-5-2-r1/GATE_5_2_R1_HANDOFF.md`
