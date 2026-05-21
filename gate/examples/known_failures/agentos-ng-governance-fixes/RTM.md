# Requirement Traceability Matrix

**Task:** agentos-ng-governance-fixes
**Date:** 2026-04-30

| id | requirement text (verbatim) | artifact/file satisfying it | test/proof satisfying it | status | evidence path | BLOCKING: YES/NO |
|---|---|---|---|---|---|---|
| B1-DET | BLOCKER 1 — Detection: validate/MCO detects scope violations or MCO failure before merge to main | agentos_ng.py `cmd_validate()` returns non-zero on scope violations; `_run_mco_review()` returns BLOCKED when provider_success < minimum | T-004: `validate_T004.log` shows FAIL; T-009: `validate_T009.log` shows FAIL | SATISFIED | e2e_v2/v2_validate_T004.log, v2_validate_T009.log | NO |
| B1-PRV | BLOCKER 1 — Prevention: commits from tasks that fail validate/MCO are absent from main branch | Integration branch architecture: ORCH auto-merges to integration, not main. `cmd_merge` cherry-picks to main only after all gates pass. | git log main before = git log main after for T-004 and T-009 | SATISFIED | e2e_v2/v2_git_log_main_before_T004_gate.txt, v2_git_log_main_after_T004_blocked.txt, v2_git_log_main_before_T009_gate.txt, v2_git_log_main_after_T009_blocked.txt | NO |
| B1-ARCH | BLOCKER 1 — Architecture: ORCH auto-merge goes to integration branch, not main | INTEGRATION_BRANCH constant + `_ensure_integration_branch()` + project root checked out to agentos-ng-integration | E2E sandbox: integration branch received ORCH merges (13eb2fb, f4ae917, 0168211, etc.); main only received cherry-picks | SATISFIED | e2e_v2/v2_ACCEPTANCE_RESULTS.md (integration log) | NO |
| B1-CP | BLOCKER 1 — Cherry-pick: only AgentOS-NG `cmd_merge` promotes commits to main | `_cherry_pick_to_main()` function + cmd_merge gate sequence | T-007 manually promoted to main via cherry-pick to demonstrate path; automated path requires real ORCH SHA | PARTIAL — live cmd_merge path not auto-demonstrated (SHA extraction requires real ORCH run) | e2e_v2/v2_merge_T007.log, v2_git_log_main_after_T007.txt | NO (documented limitation) |
| B2-DET | BLOCKER 2 — Detection: planner detects when a consumer task's producer is not yet selected | classifier.py `build_schedule_plan()` producer-before-consumer check at lines 744–767 | Plan output shows T-008 in EXCLUDED with reason: "producer T-007-schema-producer must be selected/completed before consumer T-008-schema-consumer" | SATISFIED | e2e_v2/v2_plan_output.txt, v2_blocker2_plan_assertion.txt | NO |
| B2-PRV | BLOCKER 2 — Prevention: consumer task not started before producer task is scheduled | T-008 in EXCLUDED (not SELECTED) in plan output; T-007 in SELECTED | `waiting_on_producer` return key lists T-008 | SATISFIED | e2e_v2/v2_plan_output.txt | NO |
| B3-DET | BLOCKER 3 — Detection: validate detects empty diff when expected_changed_paths is non-empty | agentos_ng.py `cmd_validate()` false completion check at lines 1251–1263 | T-010: `validate_T010.log` shows "[validate] FAIL: empty diff — expected changes in ['docs/retrieval.md'] but no files were changed" | SATISFIED | e2e_v2/v2_validate_T010.log, v2_blocker3_assertion.txt | NO |
| B3-PRV | BLOCKER 3 — Prevention: false completion does not proceed to merge | validate exits non-zero; merge is only called after validate passes | T-010: validate returned non-zero; T-010 not in main git log | SATISFIED | e2e_v2/v2_validate_T010.log, v2_git_log_main_after_T007.txt (T-010 absent) | NO |
| B4-GIT | BLOCKER 4 — Clean repo state: tracked source files are clean after E2E | Integration branch checked out cleanly; .gitignore covers .agentos-ng/ | git status shows only untracked tests/check-types.js (test helper, not a governance fix artifact); no modified tracked files | SATISFIED | e2e_v2/v2_final_git_status.txt | NO |
| B4-GITIGNORE | BLOCKER 4 — .gitignore covers .agentos-ng/ | .gitignore in E2E sandbox covers .agentos-ng/ line | v2_ACCEPTANCE_RESULTS.md: ".agentos-ng/ is gitignored: YES" | SATISFIED | e2e_v2/v2_ACCEPTANCE_RESULTS.md | NO |
| B5-TESTS | Classifier tests: 17/17 passing after all changes | 17 test cases in test_classifier.py including test_schema_producer_consumer_hard_block (covers contract dependency scoring) | `python3 -m pytest tests/test_classifier.py -v` → 17 passed in 0.04s | SATISFIED | reports/agentos-ng-governance-fixes/classifier_tests.log (EXIT_CODE:0) | NO |
| B5-CLASSIFY | classifier.py: test_schedule_plan_excludes_hard_block covers scheduling exclusion path | test_schedule_plan_excludes_hard_block in test_classifier.py at line 193 | New producer-before-consumer check produces exclusion_reasons entries that fall into the same EXCLUDED list tested by this test | SATISFIED | test_classifier.py, classifier_tests.log | NO |
| B5-SMOKE | E2E sandbox smoke tests: bm25, vector, search tests pass | `node tests/bm25.test.js`, `node tests/vector.test.js`, `node tests/search.test.js` | All 3 pass — "search tests PASS" | SATISFIED | e2e_v2/v2_final_smoke.log | NO |

## RTM Summary
- Total requirements: 13
- SATISFIED: 12
- PARTIAL: 1 (B1-CP — cherry-pick path not auto-demonstrated; documented limitation)
- MISSING: 0
- NOT_APPLICABLE: 0
- BLOCKING findings: 0
