# Gate 5.2-R1 Targeted Fixture Verification

**Date:** 2026-05-01

## Methodology note

The acceptance protocol's example invocation used `--task-area r1_acceptance_test`. Fixtures store proof files under `reports/<fixture_name>/` (matching their fixture-name task area), so a synthetic task area causes spurious "MISSING required proof file" errors that mask R1 behavior under test.

To exercise R1's actual behavior the way the in-suite tests do, this audit ran each fixture with `--task-area <fixture_name>` and the same `--risk-tier`/`--task-kind` defaults the test runner uses (`D3` / `merge_verification` for GATE_FULL fixtures, `D2` / `normal_impl` for GATE_STANDARD fixtures, no risk/task for the GATE_LITE missing-metadata fixture). Where the in-suite test calls with `final=True` the manual run also passes `--final`.

The intent of the protocol — verify the 10 R1 behaviors are correctly enforced — is preserved.

## Results matrix

| # | Fixture | Profile | Final? | Expected | Observed exit | Key diagnostic | Verdict |
|---|---------|---------|--------|----------|---------------|----------------|---------|
| 1 | `absolute_raw_output_outside_package` | GATE_FULL | no | FAIL | 1 | `HOST_PATH_NOT_PACKAGE_EVIDENCE` present | PASS |
| 2 | `absolute_host_path_plus_package_copy` | GATE_FULL | yes | PASS | 0 | 47 checks passed, 0 failed | PASS |
| 3 | `lite_profile_missing_risk_task` | GATE_LITE | no | FAIL | 1 | `MISSING_RISK_TIER` + `MISSING_TASK_KIND` present | PASS |
| 4 | `missing_not_applicable_proof` | GATE_STANDARD | no | FAIL | 1 | `MISSING_NOT_APPLICABLE_PROOF` present | PASS |
| 5 | `not_applicable_with_reason` | GATE_STANDARD | yes | PASS | 0 | 33 checks passed, 0 failed | PASS |
| 6 | `dirty_git_status_active_parallel_work` | GATE_FULL | yes | PASS | 0 | 46 checks passed, 0 failed | PASS |
| 7 | `dirty_git_status_unknown_requires_human` | GATE_FULL | no | FAIL | 1 | `UNKNOWN_REQUIRES_HUMAN_BLOCKER` present | PASS |
| 8 | `output_contract_negated_token` | GATE_FULL | yes | PASS | 0 | 45 checks passed, 0 failed | PASS |
| 9 | `output_contract_structured_fail` | GATE_FULL | no | FAIL | 1 | `STALE_MILESTONE_LABEL` flag emitted from structured FAIL verdict | PASS |
| 10 | `happy_path_gate_full` (with `--final`) | GATE_FULL | yes | PASS | 0 | 45 checks passed, 0 failed | PASS |

## Commands run (representative)

Fixture 1 (FAIL on host-path leak):
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/absolute_raw_output_outside_package \
  --profile GATE_FULL \
  --task-area absolute_raw_output_outside_package \
  --gate-dir /Users/syedhaider/Downloads/gate \
  --risk-tier D3 --task-kind merge_verification
# EXIT: 1, key flag: HOST_PATH_NOT_PACKAGE_EVIDENCE
```

Fixture 3 (FAIL on missing GATE_LITE metadata):
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/lite_profile_missing_risk_task \
  --task-area lite_profile_missing_risk_task \
  --gate-dir /Users/syedhaider/Downloads/gate
# EXIT: 1, key flags: MISSING_RISK_TIER + MISSING_TASK_KIND
```

Fixture 10 (PASS in --final mode):
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/happy_path_gate_full \
  --profile GATE_FULL \
  --task-area happy_path_gate_full \
  --gate-dir /Users/syedhaider/Downloads/gate \
  --risk-tier D3 --task-kind merge_verification --final
# EXIT: 0, 45 PASS / 0 FAIL
```

## Verdict

10/10 fixtures match expected. Proceed to P04.
