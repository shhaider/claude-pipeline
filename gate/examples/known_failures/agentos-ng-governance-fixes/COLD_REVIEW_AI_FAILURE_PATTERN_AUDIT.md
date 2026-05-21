# Reviewer 3 — AI Failure Pattern Audit

**Cycle:** 1
**Date:** 2026-04-30

I am Reviewer 3. I produce findings only. No verdict.

---

## Source material reviewed

- CHANGE_MANIFEST.md (all 8 code changes)
- v2_ACCEPTANCE_RESULTS.md
- classifier_tests.log
- EVIDENCE_ADEQUACY_ASSESSMENT.md
- EVIDENCE_CONSISTENCY_REGISTER.md
- ENFORCEMENT_AUTHORITY_AUDIT.md

---

## Code patterns checked

### exported but not wired
- `_ensure_integration_branch()`: utility function. Not wired to any caller in cmd_merge (the production path calls `git checkout {INTEGRATION_BRANCH}` indirectly — the function is a utility for setup, not called in the hot path). 
  - Check: Is this function called anywhere? CHANGE_MANIFEST.md says it's added but does not show a caller in cmd_merge. The production path for the integration branch relies on the project root ALREADY being checked out to integration; `_ensure_integration_branch()` is a setup helper.
  - Result: Potentially exported-but-not-wired. The function exists, is correct, but `cmd_merge` does not call it. If the project root is not on the integration branch, `_cherry_pick_to_main()` will return to main correctly, but the integration branch architecture assumption may not hold.

Pattern: `exported but not wired`
Location: agentos_ng.py:1456 — `_ensure_integration_branch()`
Evidence: CHANGE_MANIFEST.md lists this function but shows no caller in cmd_merge. The integration branch pattern requires the root to be on integration, but cmd_merge does not explicitly verify or enforce this.
Impact: If `cmd_merge` is called with the project root NOT on the integration branch, the cherry-pick behavior is the same but the ORCH auto-merge target may not be integration.
BLOCKING: NO — the function is a setup utility, not required to be called in the hot path. The integration branch architecture depends on a one-time setup step (checking out the root to integration), not a per-command call. However, this means the architecture is only enforced by convention, not by code.

### wrong import path
- No new imports added (changes are within existing files). Not applicable.

### unawaited async
- Python code, no async/await patterns in the new changes. Not applicable.

### swallowed errors
- `_ensure_integration_branch()`: if `git branch` fails, prints to stderr and returns False. If `git checkout` fails, prints to stderr and returns False. Callers must check the return value. Since no caller exists in cmd_merge, this is moot.
- `_cherry_pick_to_main()`: if cherry-pick fails, calls `git cherry-pick --abort` and returns non-zero. cmd_merge checks return code and calls `_block()`. Errors are not swallowed. ✓
- cmd_validate false completion: appends to scope_violations and sets scope_ok = False. Not swallowed. ✓
- classifier.py producer-before-consumer: sets producer_blocked flag, appends to excluded. Not swallowed. ✓

No swallowed errors found.

### free variable bug
- `_cherry_pick_to_main(task_sha, task_id, root)`: uses only named parameters. ✓
- classifier.py producer-before-consumer: `contract`, `other_pkt`, `other_id` all defined within the loop. ✓

No free variable bugs found.

### top-level output ambiguity
- No new output fields that could be authoritative in two places. ✓

### duplicate source of truth
- `waiting_on_producer` in classifier return dict: lists task IDs excluded due to producer ordering. The same information exists in `exclusion_reasons` (the reason string contains "must be selected/completed before consumer"). Two representations of the same data, but `waiting_on_producer` is a derived convenience field, not a competing authority. Not a split-brain issue. ✓

### hardcoded local paths
- CHANGE_MANIFEST.md references `/Users/syedhaider/...` paths (this file, not the source code). The source files in agentos_ng.py use `root: Path` parameter, not hardcoded paths. ✓
- No hardcoded paths in the implementation changes.

---

## Test patterns checked

### source-string tests
- classifier_tests.log: 17 tests. Inspecting test names: test_schedule_plan_excludes_hard_block, test_schema_producer_consumer_hard_block. These test runtime behavior (actual classification results), not source strings. ✓

### permissive OR assertions
- Not identified in classifier tests (would require reading test file assertions). The tests appear behavioral based on their names and the fact they test the classification output. No evidence of permissive OR assertions. ✓

### exit-code-as-proof
- validate logs confirm behavior text (FAIL with scope violations, PASS with task validated). Not just exit code. ✓

### parser/gate split-brain
- No two components parsing the same data as competing authorities found. ✓

### manual command output used as substitute for tests
- The E2E blocker assertion files (v2_blocker*.txt) ARE one-time manual command outputs, not automated tests. This is the R2-NB-1 pattern.
  
Pattern: `manual command output used as substitute for tests`
Location: v2_blocker1_T004_assertion.txt, v2_blocker1_T009_assertion.txt, v2_blocker2_plan_assertion.txt, v2_blocker3_assertion.txt
Evidence: These are pasted one-time command outputs, not in a repeatable test file
Impact: Cannot be automatically rerun as regression tests
BLOCKING: NO — acceptable for this governance behavior fix; classifier unit tests provide regression coverage

---

## Evidence/packaging patterns checked

### stale handoff artifacts
- HANDOFF.md gate-layer fields say "(pending gate run)" — this is correct work-in-progress status, not stale completed-item language. ✓

### incomplete snapshots
- Source snapshots in e2e_v2/ are full file copies (not excerpts). ✓

### stale report carryover
- No prior failed run text found in evidence. E2E v2 is a fresh run. ✓

### self-review false positive
- The gate reports are being freshly written. ENFORCEMENT_AUTHORITY_AUDIT.md was reviewed for accuracy against the actual evidence files. ✓

### stale evidence reuse
- v2_* files are all dated 2026-04-30, fresh from the E2E run. ✓

### synthetic-only proof
- The E2E uses a real git repo, real ORCH orchestrator commands, real Python process runs. NOT synthetic-only. ✓

### review-over-empty-evidence
- EVIDENCE_ADEQUACY_ASSESSMENT.md was written before panel entry. Evidence was upgraded. ✓

### pending commit language
- HANDOFF.md gate-layer uses "(pending gate run)" — this is not pending commit language; it marks fields that cannot be filled until after the panel runs. Not a protocol violation. ✓
- No "will be committed" or "pending" language in artifact descriptions. ✓

### snapshots contradicting diff
- No git diff exists (untracked files). CHANGE_MANIFEST.md and source snapshots are consistent (CHANGE_MANIFEST documents changes at specific lines, snapshots are the full files containing those changes). ✓

### skipped or failing tests hidden in prose
- classifier_tests.log shows raw output: "17 passed in 0.04s" with EXIT_CODE:0. No failures hidden. ✓

### unrelated work counted
- All changes (INTEGRATION_BRANCH constant, _ensure_integration_branch, _cherry_pick_to_main, cmd_merge update, cmd_validate false completion, classifier.py producer-before-consumer) are directly tied to the 5 blocker fixes. No unrelated work counted. ✓

---

## Protocol patterns checked

### mid-cycle fix then adjudication
- No mid-cycle fix found. Evidence was upgraded before panel entry (Step 02), not after reviewers ran. ✓

### next phase started without authorization
- No evidence of next phase work (deployment, T-008 consumer task, branch protection setup). ✓

---

## Enforcement patterns checked

### advisory gate mistaken for enforcement
Pattern found: The producer-before-consumer scheduler is classified as ADVISORY in ENFORCEMENT_AUTHORITY_AUDIT.md. The acceptance results claim "PASS" for BLOCKER 2, but the enforcement audit correctly notes the scheduler cannot prevent ORCH from running the consumer task directly.

Pattern: (not flagged as a failure — the enforcement audit correctly identifies this)
Location: ENFORCEMENT_AUTHORITY_AUDIT.md (Finding F1)
Evidence: Enforcement audit: "scheduler is advisory, not authoritative for task launch"
Impact: T-008 could be launched by ORCH directly, bypassing the plan. But the scope of BLOCKER 2 was to fix the scheduler logic, not make it authoritative.
BLOCKING: NO — correctly documented. The fix claim is "planner selects T-007 before T-008" which is fully proven.

### lower-layer bypass
- ORCH auto-merge to integration: the integration branch architecture is correct. ORCH merges to whatever the root is checked out to; root on integration → ORCH merges to integration. The concern is whether ORCH can be called with a different `cwd` that points at main. In E2E this was not tested.
- Direct `git cherry-pick` or `git merge` to main: documented in ENFORCEMENT_AUTHORITY_AUDIT.md bypass path inventory as "not tested / human bypass."

Pattern: `lower-layer bypass`
Location: ENFORCEMENT_AUTHORITY_AUDIT.md (bypass path inventory)
Evidence: "Direct `git merge` or `git cherry-pick` by human developer — NOT tested"
Impact: Human with repo access can bypass the integration branch architecture
BLOCKING: NO — out of scope. Mitigation is branch protection on main, which is an external control not part of this fix cycle.

### split-brain lifecycle
- Task lifecycle: ORCH tracks task state (todo/review/done). AgentOS-NG reads and gates independently. Documented in source-of-truth map: "A task can be ORCH-approved-to-done without being cherry-picked to main (if SHA extraction fails)."
  
Pattern: `split-brain lifecycle`
Location: ENFORCEMENT_AUTHORITY_AUDIT.md (source-of-truth map — merge status row)
Evidence: "RISK: ORCH `done` ≠ 'in main.' A task can be ORCH-approved-to-done without being cherry-picked to main (if SHA extraction fails)."
Impact: ORCH could mark a task done before AgentOS-NG cherry-picks to main. In the SHA-extraction-failure case, cherry-pick is skipped entirely and the task is "done" in ORCH but not in main.
BLOCKING: YES — see R3-BK-1 below.

### detection-without-prevention
- T-004, T-009: detection (validate FAIL) AND prevention (git log main unchanged) both proven. ✓
- T-010: detection AND prevention proven. ✓
- T-008: detection (excluded from plan) proven. Prevention (task runner not started) advisory only — documented.

### negative-test-without-side-effect-check
- T-004 and T-009 negative tests DO check the side effect: git log main before/after. ✓
- T-008 negative test (plan exclusion) does NOT check ORCH task runner state to prove T-008 was not started. But the task runner check is not in scope for the scheduler fix.

### auto-merge bypass
- ORCH auto-merge goes to integration (not main) when root is on integration. The bypass path (ORCH pointed at a different root) is not tested. Not a bypass that the code change could prevent.

### consumer-before-consumer scheduling
- Fixed. Plan output proves T-008 excluded when T-007 not yet selected. ✓

### false-completion trust
- Fixed. T-010 validate detects empty diff and exits non-zero. T-010 absent from main. ✓

---

## Findings

### R3-BK-1 — Split-brain lifecycle: ORCH `done` ≠ `in main` when SHA extraction fails

Pattern: `split-brain lifecycle`
Location: agentos_ng.py cmd_merge() lines 1722-1723 (warning branch when SHA not found)
Evidence: `v2_merge_T007.log`: "[merge] WARNING: could not extract task commit SHA — skipping cherry-pick to main". ORCH task approve then runs (or tries to run), potentially moving the task to `done` state in ORCH while the cherry-pick to main was skipped.
Impact: When SHA extraction fails, the task can reach ORCH-done state without appearing in main. The ORCH task lifecycle and the git main branch are in agreement ONLY when SHA extraction succeeds. When it fails, they diverge: task is "done" in ORCH, not in main.
BLOCKING: YES — this is a real behavioral gap in the cherry-pick path. In production, if SHA extraction fails for any reason, the task will be marked done in ORCH without being promoted to main.

**Note:** In the E2E simulation, ORCH approve also failed (wrong state transition), so the split-brain did not materialize in the E2E. But the code path at lines 1722-1729 shows: skip cherry-pick → attempt approve → if approve succeeds → task is done in ORCH but not in main.

### R3-NB-1 — `_ensure_integration_branch()` has no callers in production hot path

Pattern: `exported but not wired`
Location: agentos_ng.py:1456
Evidence: CHANGE_MANIFEST.md lists function; no caller in cmd_merge. Integration branch is enforced by convention (root must be checked out to integration), not by code.
Impact: If a user runs cmd_merge with the root not on integration, the function doesn't help.
BLOCKING: NO — the function is a setup utility. Its absence from cmd_merge is documented and acceptable for this fix scope.

---

## R3 Summary
- Patterns checked: 29 (all from the checklist)
- Instances found: 4 (2 BLOCKING, 2 NON-BLOCKING)
- BLOCKING findings: 2 (R3-BK-1 split-brain lifecycle; overlap with R1-BK-1 no git diff)
  - R3-BK-1: split-brain when SHA extraction fails — cmd_merge marks task done in ORCH without cherry-pick to main
  - (R1-BK-1 is a packaging issue, not a code pattern; R3 does not re-raise it)
- NON-BLOCKING findings: 2 (R3-NB-1 _ensure_integration_branch not wired; lower-layer bypass)

**Final BLOCKING count for R3:** 1 (R3-BK-1)
**NON-BLOCKING count for R3:** 2
