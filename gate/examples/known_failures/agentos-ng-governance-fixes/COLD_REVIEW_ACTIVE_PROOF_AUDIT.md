# Reviewer 2 — Active Proof Audit

**Cycle:** 1
**Date:** 2026-04-30

I am Reviewer 2. I produce findings only. No verdict.

---

## Source material reviewed

- v2_ACCEPTANCE_RESULTS.md
- v2_validate_T004.log, v2_validate_T007.log, v2_validate_T009.log, v2_validate_T010.log
- v2_plan_output.txt
- v2_blocker1_T004_assertion.txt, v2_blocker1_T009_assertion.txt
- v2_blocker2_plan_assertion.txt, v2_blocker3_assertion.txt
- v2_git_log_main_before_T004_gate.txt, v2_git_log_main_after_T004_blocked.txt
- v2_git_log_main_before_T009_gate.txt, v2_git_log_main_after_T009_blocked.txt
- v2_git_log_main_after_T007.txt
- v2_merge_T007.log
- v2_final_git_status.txt
- v2_final_smoke.log
- classifier_tests.log
- EVIDENCE_CONSISTENCY_REGISTER.md
- ENFORCEMENT_AUTHORITY_AUDIT.md

---

## Behavior-by-behavior active proof assessment

| behavior | proof type | proof artifact | active path? | sufficient? | BLOCKING: YES/NO |
|---|---|---|---|---|---|
| T-004 scope violations detected by validate | Active command output | v2_validate_T004.log: "FAIL — scope violations: ['.gitignore', 'docs/retrieval.md', 'package.json']" | YES — `agentos-ng validate T-004-blocked-mco` run against real task artifacts | YES | NO |
| T-004 commit absent from main after gate | Git source-of-truth inspection | v2_git_log_main_before_T004_gate.txt = v2_git_log_main_after_T004_blocked.txt | YES — actual `git log main` before and after; logs identical | YES — strongest possible proof | NO |
| T-009 scope violations detected by validate | Active command output | v2_validate_T009.log: "FAIL — scope violations: ['src/retrieval/bm25.js']" | YES — `agentos-ng validate` run against real task artifacts | YES | NO |
| T-009 commit absent from main after gate | Git source-of-truth inspection | v2_git_log_main_before_T009_gate.txt = v2_git_log_main_after_T009_blocked.txt | YES — actual `git log main` before and after; logs identical | YES | NO |
| T-008 consumer excluded when T-007 producer not yet selected | Active plan output | v2_plan_output.txt: "EXCLUDED (1): - T-008-schema-consumer: producer T-007-schema-producer must be selected/completed..." | YES — `agentos-ng plan` run with real task packets | YES — plan output is active, not source-string | NO |
| T-010 false completion detected by validate | Active command output | v2_validate_T010.log: "[validate] FAIL: empty diff — expected changes in ['docs/retrieval.md'] but no files were changed" | YES — `agentos-ng validate` run against T-010 with zero changed files | YES | NO |
| T-010 false completion does not reach merge | Absence from git log | T-010 absent from v2_git_log_main_after_T007.txt | YES — main git log inspected; only T-001 and T-007 present | YES | NO |
| T-001 (positive test) validated and merged | Active command output + git log | v2_run_T001.log + v2_git_log_main_after_T001.txt | YES — T-001 commit (48d6f30) appears in main | YES | NO |
| T-007 (positive test) validated | Active command output | v2_validate_T007.log: "PASS — task tsk_IW_wsUt validated" (EXIT_CODE:0 from v2 verify run) | YES | YES | NO |
| T-007 promoted to main | Git log + manual cherry-pick | v2_git_log_main_after_T007.txt: 7cc5517 on main | PARTIAL — cherry-pick was manual (SHA extraction failed in simulation); production path not auto-demonstrated | PARTIAL | YES — see R2-BK-1 |
| 17/17 classifier tests passing | Active pytest run | classifier_tests.log: "17 passed in 0.04s, EXIT_CODE:0" | YES — real pytest execution against production test file | YES | NO |
| E2E sandbox smoke tests passing | Active test run | v2_final_smoke.log: "search tests PASS" | YES — node test runner executed | YES | NO |
| Integration branch architecture (ORCH auto-merge to integration not main) | Indirect: git log of integration shows ORCH merge commits; git log of main shows only cherry-picked commits | v2_ACCEPTANCE_RESULTS.md integration log vs main log | YES — git log is authoritative | YES — structural proof: integration has ORCH merge commits, main only has approved commits | NO |

---

## Enforcement-specific active proof checks

### 1. Final side-effect verification

For T-004 and T-009: raw evidence includes `git log main` BEFORE and AFTER the blocked attempt. Blocked commit SHAs are absent from main. ✓

For T-010: main git log inspected after full E2E run; T-010 (tsk_PSLTT2F) absent from main. ✓

### 2. Git log inspection for merge blocks

T-004: before [48d6f30, 3e864d4], after [48d6f30, 3e864d4]. Identical. T-004 commit (`13eb2fb` on integration) absent from main. ✓
T-009: before [48d6f30, 3e864d4], after [48d6f30, 3e864d4]. Identical. T-009 commit (`73c1ba3` on integration) absent from main. ✓

### 3. Task runner state for task-launch blocks

For T-008: planner excludes T-008 from `selected_tasks`. However, the underlying ORCH runner was NOT checked to confirm it did NOT start T-008. The plan output is from AgentOS-NG's scheduler, which is advisory. ORCH could still launch T-008 directly.

**This is an advisory vs authoritative gap** — the planner output proves detection and scheduling exclusion, but does NOT prove ORCH task runner did not start T-008. The Enforcement Authority Audit classifies the scheduler as advisory.

BLOCKING: NO — the scheduler advisory nature is documented. The fix scope was to correct the scheduler logic, not to make it authoritative. The behavior claimed (planner excludes T-008) is fully proven.

### 4. Release/merge prevention for gate failures

Proven: T-004, T-009 validate failures prevent merge. T-010 validate failure prevents merge. Evidence: git log main. ✓

### 5. Detection-only proof concern

T-004: Detection (validate FAIL) AND prevention (git log main unchanged) both proven. NOT detection-only. ✓
T-009: Same as T-004. ✓
T-010: Detection (validate FAIL) AND prevention (absent from main git log) both proven. ✓
T-008: Detection (excluded from selected_tasks) proven. Prevention (task runner not started) NOT independently proven. But scope of fix was scheduling logic, not task runner control.

---

## Specifically looked for

**Evidence adequacy items skipped without justification:** None. EVIDENCE_ADEQUACY_ASSESSMENT documents the cherry-pick gap as a known limitation with root cause.

**Tests that don't exercise the critical runtime path:** The classifier tests exercise the classification logic directly. The schedule plan test (`test_schedule_plan_excludes_hard_block`) tests scheduling exclusion, which is the same code path as producer-before-consumer exclusion. No source-string-only tests found.

**Manual runs used as substitute for automated regression tests:** The E2E tests are manual orchestration of `agentos-ng` commands. The BLOCKER checks are not automated regression tests in a test file — they are one-time manual E2E probes. This is a weakness but acceptable for this type of behavioral governance change (the alternative would be a Playwright-style E2E harness for git+ORCH, which is beyond task scope).

**Raw outputs with missing exit codes:** 
- v2_validate_T004.log, v2_validate_T009.log, v2_validate_T010.log: Do not have "EXIT_CODE:" prefix. The exit codes are documented in the assertion files but not in the raw logs themselves.
- classifier_tests.log: Has `EXIT_CODE:0`. ✓
- This is a non-blocking gap per consistency register.

**Test-count claims disagreeing with raw output:** classifier_tests.log says 17 passed. HANDOFF says 17. RTM says 17. Consistent. ✓

---

## Findings

### R2-BK-1 — cmd_merge cherry-pick path not active-path proven

The automated cherry-pick path (`_cherry_pick_to_main()` called from `cmd_merge`) was not exercised. In the E2E, SHA extraction failed and the cherry-pick was performed manually. The production path from `cmd_merge` to `main` requires ORCH proof data (set only by real ORCH agent runs) that was not available in simulation.

**What is proven:** The integration branch architecture prevents T-004 and T-009 from reaching main. The cherry-pick is the positive-path mechanism (how approved tasks reach main).

**What is NOT proven:** That `cmd_merge` correctly calls `_cherry_pick_to_main()` end-to-end and that T-007 was promoted via this automated path.

**Impact:** An outside reviewer cannot confirm the production cherry-pick wiring is correct and tested. The merge log shows it fell through to the warning branch.

BLOCKING: YES

**Note:** This same gap appeared in the prior closed-loop gate (the agentos-ng-classifier gate also had the SHA extraction limitation noted). The issue is structural — it requires a live ORCH agent run, not a code fix.

### R2-NB-1 — E2E evidence is one-time manual probes, not automated regression tests

The BLOCKER acceptance tests are one-time manual command runs. They correctly prove the behaviors at the time of the E2E run but would not catch regressions in a CI/CD context.

BLOCKING: NO (appropriate for a governance behavior fix; regression coverage via classifier unit tests is the primary automated safety net)

### R2-NB-2 — Raw validate logs lack EXIT_CODE: prefix

v2_validate_T004.log, T009, T010 do not have "EXIT_CODE:" prefix. Exit codes are documented in assertion files. Reviewers must cross-reference.

BLOCKING: NO (exit codes documented in assertion files; behavior is unambiguous from output text)

---

## R2 Summary
- Behaviors assessed: 13
- Active-path proven: 12
- Partial / source-string-only / manual-only: 1 (T-007 cherry-pick path)
- BLOCKING findings: 1 (R2-BK-1 — cmd_merge cherry-pick not auto-demonstrated)
- NON-BLOCKING findings: 2 (R2-NB-1, R2-NB-2)
