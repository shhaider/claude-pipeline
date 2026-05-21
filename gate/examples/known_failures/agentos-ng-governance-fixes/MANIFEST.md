# Artifact Manifest

**Task:** agentos-ng-governance-fixes
**Date:** 2026-04-30

## Implementation source files (not in git — see CHANGE_MANIFEST.md)

| file | path | description | lines |
|---|---|---|---|
| agentos_ng.py | /Users/syedhaider/.codex/agentos_ng/agentos_ng.py | Main AgentOS-NG orchestration module — contains BLOCKER 1, 3, and 4 fixes | 2076 |
| classifier.py | /Users/syedhaider/.codex/agentos_ng/classifier.py | Dependency classifier module — contains BLOCKER 2 fix | 857 |
| test_classifier.py | /Users/syedhaider/.codex/agentos_ng/tests/test_classifier.py | Classifier unit tests — 17 tests, all passing | 465 |

## Evidence source snapshots (copies of implementation files in evidence package)

| file | path |
|---|---|
| agentos_ng.py (snapshot) | /Users/syedhaider/Downloads/agentos_ng_pilot/e2e_v2/agentos_ng.py |
| classifier.py (snapshot) | /Users/syedhaider/Downloads/agentos_ng_pilot/e2e_v2/classifier.py |
| test_classifier.py (snapshot) | /Users/syedhaider/Downloads/agentos_ng_pilot/e2e_v2/test_classifier.py |

## Acceptance test artifacts

| file | path | content |
|---|---|---|
| E2E acceptance results | e2e_v2/v2_ACCEPTANCE_RESULTS.md | Final summary of all 5 blocker tests |
| T-004 blocker 1 assertion | e2e_v2/v2_blocker1_T004_assertion.txt | Before/after git log + validate result for T-004 |
| T-009 blocker 1 assertion | e2e_v2/v2_blocker1_T009_assertion.txt | Before/after git log + validate result for T-009 |
| Blocker 2 plan assertion | e2e_v2/v2_blocker2_plan_assertion.txt | Plan output showing T-007 selected, T-008 excluded |
| Blocker 3 assertion | e2e_v2/v2_blocker3_assertion.txt | T-010 validate output showing empty diff detection |

## Raw command output files

| file | path | command | exit code |
|---|---|---|---|
| validate T-004 log | e2e_v2/v2_validate_T004.log | `agentos-ng validate T-004-blocked-mco` | non-zero (FAIL) |
| validate T-007 log | e2e_v2/v2_validate_T007.log | `agentos-ng validate T-007-schema-producer` | 0 (PASS) |
| validate T-009 log | e2e_v2/v2_validate_T009.log | `agentos-ng validate T-009-out-of-scope` | non-zero (FAIL) |
| validate T-010 log | e2e_v2/v2_validate_T010.log | `agentos-ng validate T-010-false-completion` | non-zero (FAIL) |
| plan output | e2e_v2/v2_plan_output.txt | `agentos-ng plan` | 0 |
| merge T-007 log | e2e_v2/v2_merge_T007.log | `agentos-ng merge T-007-schema-producer` | non-zero (SHA extraction failed in simulation) |
| review T-007 log | e2e_v2/v2_review_T007.log | `agentos-ng review T-007-schema-producer` | 0 |
| run T-001 log | e2e_v2/v2_run_T001.log | `agentos-ng run T-001-docs` | 0 |
| smoke tests | e2e_v2/v2_final_smoke.log | `node tests/search.test.js` | 0 |
| classifier tests | reports/agentos-ng-governance-fixes/classifier_tests.log | `python3 -m pytest tests/test_classifier.py -v` | 0 |

## Git state artifacts

| file | path | content |
|---|---|---|
| main before T-004 gate | e2e_v2/v2_git_log_main_before_T004_gate.txt | 2 commits (T-001, initial) |
| main after T-004 blocked | e2e_v2/v2_git_log_main_after_T004_blocked.txt | Same 2 commits — T-004 absent |
| main before T-009 gate | e2e_v2/v2_git_log_main_before_T009_gate.txt | 2 commits (T-001, initial) |
| main after T-009 blocked | e2e_v2/v2_git_log_main_after_T009_blocked.txt | Same 2 commits — T-009 absent |
| main after T-007 merge | e2e_v2/v2_git_log_main_after_T007.txt | 3 commits (T-007, T-001, initial) |
| integration after T-001 | e2e_v2/v2_git_log_integration_after_T001.txt | Integration branch log |
| final git status | e2e_v2/v2_final_git_status.txt | On agentos-ng-integration; only untracked: tests/check-types.js |

## Gate reports (this directory)

| file | purpose |
|---|---|
| EVIDENCE_ADEQUACY_ASSESSMENT.md | Step 01 — adequacy decision |
| TEST_AND_EVIDENCE_PLAN.md | Step 02 — evidence upgrade plan |
| CHANGE_MANIFEST.md | Formal record of all code changes (replaces git diff) |
| RTM.md | Requirement traceability matrix |
| MANIFEST.md | This file |
| PACKAGE_FILE_LISTING.txt | find output of e2e_v2 directory |
| classifier_tests.log | Raw pytest output with EXIT_CODE:0 |
| EVIDENCE_CONSISTENCY_REGISTER.md | Step 03 — consistency check |
| ENFORCEMENT_AUTHORITY_AUDIT.md | Step 14 — enforcement authority proof |
| COLD_REVIEW_REQUIREMENTS_AUDIT.md | R1 findings |
| COLD_REVIEW_ACTIVE_PROOF_AUDIT.md | R2 findings |
| COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md | R3 findings |
| COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md | R4 findings |
| COLD_REVIEW_ADJUDICATION.md | R5 adjudication + verdict |
| HANDOFF.md | Final handoff document |
| CYCLE_TRACKER.md | Gate cycle tracking |
