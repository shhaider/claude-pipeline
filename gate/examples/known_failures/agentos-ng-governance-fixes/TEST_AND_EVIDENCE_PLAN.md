# Test and Evidence Plan

**Task area:** agentos-ng-governance-fixes
**Date:** 2026-04-30
**Reason:** Evidence Adequacy Assessment returned EVIDENCE_UPGRADE_REQUIRED

## Gap closure plan

| requirement/behavior | evidence type | file/test/probe to create | command | expected output/failure signal | raw output path | proof type |
|---|---|---|---|---|---|---|
| Formal change manifest | artifact-proof | CHANGE_MANIFEST.md | code inspection of agentos_ng.py + classifier.py | Named sections per blocker, line references | reports/agentos-ng-governance-fixes/CHANGE_MANIFEST.md | artifact-proof |
| RTM | artifact-proof | RTM.md | cross-reference blocker list to evidence files | Each requirement row has status SATISFIED | reports/agentos-ng-governance-fixes/RTM.md | artifact-proof |
| Manifest | artifact-proof | MANIFEST.md | list all evidence files | All files enumerated | reports/agentos-ng-governance-fixes/MANIFEST.md | artifact-proof |
| Handoff | artifact-proof | HANDOFF.md | synthesize all evidence | Final handoff fields complete | reports/agentos-ng-governance-fixes/HANDOFF.md | artifact-proof |
| Package file listing | package-proof | PACKAGE_FILE_LISTING.txt | `find /Users/syedhaider/Downloads/agentos_ng_pilot/e2e_v2 -type f \| sort` | All e2e_v2 files listed | reports/agentos-ng-governance-fixes/PACKAGE_FILE_LISTING.txt | package-proof |
| Producer-before-consumer unit test | active-path | verify test_schedule_plan_excludes_hard_block covers new logic | grep + test inspection | Test name present; logic hits exclusion_reasons | existing test file | active-path |

## Enforcement-specific plan rows

| protected action | invalid condition | attempted bypass path | expected blocked side effect | final source-of-truth check | raw output path |
|---|---|---|---|---|---|
| Merge to main | Scope violations (T-004) | ORCH auto-merge to integration branch; AgentOS-NG validate gate | T-004 commit absent from main | git log main before/after | e2e_v2/v2_blocker1_T004_assertion.txt + git log files |
| Merge to main | Out-of-scope changes (T-009) | ORCH auto-merge to integration branch; AgentOS-NG validate gate | T-009 commit absent from main | git log main before/after | e2e_v2/v2_blocker1_T009_assertion.txt + git log files |
| Merge to main | MCO review blocking (T-004) | cmd_merge gate | T-004 commit absent from main after MCO blocked | git log main | e2e_v2/v2_git_log_main_after_T004_blocked.txt |
| Consumer task start | Producer not yet complete (T-008) | build_schedule_plan() greedy selection | T-008 excluded from selected_tasks | plan output showing T-008 in EXCLUDED with reason | e2e_v2/v2_plan_output.txt |
| False completion unblock | Worker reports done with no files changed (T-010) | cmd_validate() | Validate exits non-zero; merge not attempted | validate output + absence from main | e2e_v2/v2_validate_T010.log |

## Execution status

All plan items completed inline. Artifacts created:
- CHANGE_MANIFEST.md ✓
- RTM.md ✓
- MANIFEST.md ✓
- HANDOFF.md ✓
- PACKAGE_FILE_LISTING.txt ✓
