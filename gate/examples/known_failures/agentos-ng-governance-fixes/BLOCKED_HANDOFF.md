# Blocked Handoff — AgentOS-NG Governance Fixes

**Condition triggering this handoff:** Reviewer 5 (Cycle 2) returned `BLOCKED` — one HUMAN_BLOCKED finding remains after 2 cycles.
**Sent here from:** `09_R5_ADJUDICATION.md` (Cycle 2) → `10_GATE_VERDICT.md` → `13_BLOCKED_HANDOFF.md`

---

## Why blocked

Reviewer 5 Cycle 2 issued verdict `BLOCKED`. All AUTOFIX_REQUIRED blockers were resolved in Cycle 1. One HUMAN_BLOCKED blocker remains: the `cmd_merge` integration path (cherry-pick to main or SHA-not-found block) has not been exercised with real ORCH agent proof data. This cannot be fixed by writing code — it requires running a real ORCH agent task.

---

## All remaining blockers

```
BLOCKER: BLOCKER-CHERRY-C2
Source: Reviewer 2 (Cycle 2) — R2-BK-1-C2, R2-BK-2 (same root cause, deduplicated)
Classification: HUMAN_BLOCKED
Evidence: v2_merge_T007.log shows "[merge] WARNING: could not extract task commit SHA — skipping 
cherry-pick to main". The E2E simulation does not populate ORCH proof data 
(agent_summary/branch fields in .orchestry/task/<id>/proof/ directory), which is the 
data source for _extract_task_commit_sha(). In simulation, SHA extraction always returns None.
The Cycle 2 fix (BLOCKER-SPLITBRAIN) made the SHA-not-found path a hard block 
instead of WARNING+continue, but neither the cherry-pick positive path nor the new 
explicit block path has been exercised with real ORCH agent data.
Why it cannot be autofixed: Verifying _extract_task_commit_sha() + _cherry_pick_to_main() 
end-to-end requires ORCH to have run a real agent (not a simulation), which generates 
the proof data the SHA extraction reads. This is outside the current task scope.
```

---

## Fixes already attempted

```
Cycle 1:
- Blockers found: BLOCKER-DIFF (no git diff), BLOCKER-SPLITBRAIN (SHA-not-found allows split-brain), BLOCKER-CHERRY (cherry-pick not demonstrated)
- Fixes applied:
  * BLOCKER-DIFF: Created implementation.patch (structured patch of all 8 changes)
  * BLOCKER-SPLITBRAIN: Changed cmd_merge() SHA-not-found branch from WARNING+continue to _block()
  * BLOCKER-CHERRY: Classified as HUMAN_BLOCKED — no fix possible without live ORCH run
- Outcome: AUTOFIX blockers resolved; HUMAN_BLOCKED blocker (BLOCKER-CHERRY) remains

Cycle 2:
- Blockers found: BLOCKER-CHERRY-C2 (HUMAN_BLOCKED — same root cause as Cycle 1 BLOCKER-CHERRY)
- Fixes applied: None (HUMAN_BLOCKED, no autofixable blockers)
- Outcome: BLOCKED — no AUTOFIX_REQUIRED blockers, 1 HUMAN_BLOCKED
```

---

## Current package state

- Final branch: `agentos-ng-integration` (E2E sandbox at /tmp/agentos-ng-e2e-v2)
- Final HEAD SHA (main): `7cc5517` (task: T-007-schema-producer)
- Final HEAD SHA (integration): `098a26c` (Merge orchestry/tsk_IW_wsUt/add-confidence-field)
- git status: On branch agentos-ng-integration; untracked: tests/check-types.js; tracked files clean

### What IS complete and evidenced

1. **BLOCKER 1 (merge prevention)**: Integration branch architecture proven via git log before/after for T-004 and T-009. Blocked commits absent from main. AUTHORITATIVE gate.
2. **BLOCKER 2 (producer-before-consumer)**: Scheduler logic proven via plan output. T-008 excluded with named reason when T-007 not yet selected.
3. **BLOCKER 3 (false completion)**: validate() false completion detection proven via T-010 validate output. T-010 absent from main.
4. **BLOCKER 4 (clean repo state)**: Tracked files clean. .gitignore covers .agentos-ng/.
5. **BLOCKER-SPLITBRAIN fix**: cmd_merge() SHA-not-found now returns _block() (code-verified by grep at line 1724).
6. **17/17 classifier unit tests passing** (classifier_tests_cycle2.log, EXIT_CODE:0).
7. **3/3 E2E smoke tests passing**.
8. **Enforcement authority audit**: PASS — all authoritative gates proven via negative side-effect tests with git log main inspection.

### What is NOT complete or evidenced

1. **cmd_merge() end-to-end path**: The production flow SHA extraction → cherry-pick → ORCH approve has not been exercised with real ORCH agent data. The E2E simulation cannot populate ORCH proof data.
2. **tests/check-types.js**: Untracked in E2E sandbox (test helper, not committed).
3. **Branch protection on main**: Out of scope — would prevent human bypass.

---

## Next allowed human instruction

The user must take ONE of the following actions before this blocked handoff can be promoted to `PASS_FOR_HANDOFF`:

**Option A (Recommended — production verification):**
> Run one real ORCH agent task to completion in a project where the root is checked out to `agentos-ng-integration`. Then call `agentos-ng merge <task_id>`. Verify either:
> - (a) SHA extracted → `_cherry_pick_to_main()` runs → commit appears on `git log main`, OR
> - (b) SHA extraction fails → `cmd_merge` returns "BLOCKED — could not extract task commit SHA" → ORCH task stays in `review` state (not approved to done)

**Option B (Scope reduction acceptance):**
> Accept the known gap. The 5 governance behaviors are proven. The cherry-pick automation path is code-correct but not live-demonstrated. Explicitly accept the package as "CONTROLLED-USE READY with known verification gap: cherry-pick path not live-proven." This is a formal acceptance of the HUMAN_BLOCKED status with explicit acknowledgment.

**Option C (Alternative demonstration):**
> Provide a way to populate ORCH proof data without a live ORCH agent run (e.g., manually write the proof data to `.orchestry/task/<id>/proof/` in the format `_extract_task_commit_sha()` reads). Then re-run `agentos-ng merge <task_id>` in the E2E sandbox to demonstrate the automated cherry-pick path.

---

## Gate summary

```
closed_loop_adversarial_verdict   = FAIL_BLOCKED_REQUIRES_HUMAN
adversarial_cycles_run            = 2
reviewer_5_cycle1_verdict         = NEEDS_CORRECTION
reviewer_5_cycle2_verdict         = BLOCKED
autofix_blockers_corrected        = 2 (BLOCKER-DIFF, BLOCKER-SPLITBRAIN)
human_blocked_remaining           = 1 (BLOCKER-CHERRY-C2)
autofix_required_remaining        = 0
governance_behaviors_proven       = 5/5 (all 5 blockers evidenced via E2E)
cherry_pick_path_live_proven      = NO (code-verified only)
final_readiness_status            = BLOCKED — production demonstration required
```

---

## Blocked package includes

- `CYCLE_TRACKER.md`
- `CYCLE2_COLD_REVIEW_ADJUDICATION.md` (most recent cycle adjudication)
- `COLD_REVIEW_ADJUDICATION.md` (Cycle 1 adjudication)
- `EVIDENCE_ADEQUACY_ASSESSMENT.md`
- `EVIDENCE_CONSISTENCY_REGISTER.md`
- `ENFORCEMENT_AUTHORITY_AUDIT.md`
- `CYCLE2_COLD_REVIEW_REQUIREMENTS_AUDIT.md`
- `CYCLE2_COLD_REVIEW_ACTIVE_PROOF_AUDIT.md`
- `CYCLE2_COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md`
- `CYCLE2_COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md`
- `implementation.patch`
- `CHANGE_MANIFEST.md`
- `RTM.md`
- `MANIFEST.md`
- `HANDOFF.md`
- `classifier_tests_cycle2.log`
- `PACKAGE_FILE_LISTING.txt`
- e2e_v2 directory (all acceptance test artifacts)
