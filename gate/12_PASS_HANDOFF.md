# Step 12 — Pass: Final Handoff

You are here because:
- Reviewer 5 returned `READY_FOR_REVIEW`
- The gate returned `GATE_PASS_FOR_HANDOFF`
- `15_FINAL_PACKAGE_AUDIT.md` returned `FINAL_PACKAGE_AUDIT_PASS`
- `16_CANONICAL_HANDOFF_AUDIT.md` returned `CANONICAL_HANDOFF_AUDIT_PASS`
- `17_EXECUTION_CONTEXT_AUDIT.md` returned `EXECUTION_CONTEXT_AUDIT_PASS` or `NOT_APPLICABLE`

All five conditions are required. If you arrived here without all five, stop — go back to the step that is incomplete.

## Step 1 — Verify CURRENT_STATE.yaml

`current_state` must be `EXECUTION_CONTEXT_AUDIT_PASS` or `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE`. All three of the following must be set:
- `final_package_audit_result: PASS`
- `canonical_handoff_audit_result: PASS`
- `execution_context_audit_result: PASS or NOT_APPLICABLE`

If any is missing or not set correctly, you are here prematurely. Return to the appropriate step.

## Step 2 — Verify the completion standard

A package is not ready because:
- the implementation looks correct
- tests appear to pass in prose
- the handoff says ready
- the manifest lists the expected files
- the adversarial report says pass

A package is ready only when direct inspection proves:
- the repo state is recorded accurately
- all claimed files are physically present in the package (confirmed by Step 15)
- all required artifacts are included
- all raw outputs support the claimed pass status
- all SHAs/HEAD claims are reconciled
- all diffs/snapshots/manifests agree
- all required behaviors have adequate real-world evidence or justified non-applicability
- all required behaviors have active proof
- all five reviewers' findings are synthesized by Reviewer 5
- the final gate verdict is `PASS_FOR_HANDOFF`
- no stale files are unlabeled in the package (confirmed by Step 16)
- HANDOFF.md status is READY — not PENDING (confirmed by Step 15)

---

## Required final handoff fields

The handoff must include all of the following. Mark anything not applicable as `N/A — [reason]`.

**State machine layer:**
- CURRENT_STATE.yaml path: `reports/<task_area>/CURRENT_STATE.yaml`
- Final state: `PASS_HANDOFF_COMPLETE`
- CLAIMS_LEDGER.yaml path and audit verdict
- EVIDENCE_LEDGER.yaml path and audit verdict
- PACKAGE_MANIFEST.md path and status: VERIFIED

**Evidence layer:**
- Evidence Adequacy Assessment path
- Test and Evidence Plan path, if created
- Evidence created/upgraded/skipped summary

**Git state:**
- Final branch
- Final HEAD SHA
- Implementation commit SHA, if different from final HEAD
- Evidence/report commit SHA, if different
- Final `git status --short` exact output

**Artifacts:**
- Changed files list
- Complete diff path (as a file path, not inline)
- Final changed-file snapshot paths
- Package file listing path

**Commands and results:**
- Exact commands run
- Exit codes for every command
- Final test commands and exit codes
- Final test counts
- Raw output file paths (not inline pastes)

**Gate layer:**
- Closed-loop adversarial gate verdict: `PASS_FOR_HANDOFF`
- Number of closed-loop cycles run
- Reviewer 5 adjudication verdict from the final cycle
- Whether all AUTOFIX_REQUIRED blockers were corrected
- Whether any HUMAN_BLOCKED blockers remain
- Final Package Audit result: PASS
- Canonical Handoff Audit result: PASS
- Execution Context Audit result: PASS / NOT_APPLICABLE

**Enforcement Authority Audit (include if applicable, mark N/A if not):**
- Enforcement Authority Audit path: `reports/<task_area>/ENFORCEMENT_AUTHORITY_AUDIT.md`
- Enforcement audit verdict: PASS / NOT_APPLICABLE
- Protected actions tested: [list each protected action and result]
- Bypass paths tested: [list each bypass path, whether it was blocked or not, evidence path]
- Negative side-effect tests: [list each test, unsafe action attempted, final source-of-truth result]
- Final source-of-truth proof: [list each source inspected — git log, task runner, artifact listing — and what it showed]

**Risk and scope:**
- Known risks
- Not-tested items
- Next allowed phase
- Forbidden phases not started

**Final status:**
- Final readiness status: READY_FOR_HANDOFF
- **Final outcome label (Gate 4.1 — required):** `LIVE_BEHAVIOR_FIXED` / `INFRASTRUCTURE_READY_NOT_WIRED` / `TEST_HELPER_ONLY` / `DOCS_ONLY` / `MERGE_VERIFIED` / `MERGE_NOT_VERIFIED` / `PREPLANNING_READY` / `PREPLANNING_BLOCKED` / `PACKAGE_READY_FOR_REVIEW` / `PACKAGE_BLOCKED`

> **Hard rule:** "READY_FOR_HANDOFF" alone is insufficient for Gate 4.1. The final outcome label must specify what kind of ready. Select exactly one label from the list above. If no production caller is proven, do not use `LIVE_BEHAVIOR_FIXED`.

---

## Do not claim READY, COMPLETE, or READY_FOR_NEXT_PHASE unless

```
current_state in CURRENT_STATE.yaml = PASS_HANDOFF_COMPLETE
final_package_audit_result = PASS
canonical_handoff_audit_result = PASS
execution_context_audit_result = PASS or NOT_APPLICABLE
final_packet_auditor_verdict = PASS   (Gate 5.3 — required)
```

---

## Include in the package (Gate 5.1 — complete list)

Core files:
- `CURRENT_STATE.yaml`
- `CLAIMS_LEDGER.yaml`
- `EVIDENCE_LEDGER.yaml`
- `PACKAGE_MANIFEST.md` (status: VERIFIED)
- `STALE_FILE_REGISTER.yaml`
- All five cold review reports from the final cycle
- `EVIDENCE_ADEQUACY_ASSESSMENT.md`
- `EVIDENCE_CONSISTENCY_REGISTER.md`
- `ENFORCEMENT_AUTHORITY_AUDIT.md` (if applicable)
- `CYCLE_TRACKER.md`
- `COLD_REVIEW_ADJUDICATION.md`
- BLOCKED_HANDOFF.md from prior cycles (if any) — labeled HISTORICAL, in `prior_cycles/`

Required proof files for selected profile:
- All required proof files listed under the selected profile in `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`
- All NOT_APPLICABLE proof files for skipped states

Raw outputs (Gate 5.1 — mandatory):
- All raw test outputs registered in EVIDENCE_LEDGER.yaml with `artifact_type: raw_test_output`
- These must be the actual output files, not references or descriptions

Warning and exactness audits:
- `WARNING_OUTPUT_AUDIT.md` (if raw outputs present; or `WARNING_OUTPUT_AUDIT_NOT_APPLICABLE.md`)
- `REQUIRED_TEST_SET_EXACTNESS.md` (if raw outputs present; or `REQUIRED_TEST_SET_EXACTNESS_NOT_APPLICABLE.md`)

Package integrity files:
- `package_file_sizes.txt`
- `package_file_hashes.txt` (Gate Full)
- `GATE_PACKAGE_VALIDATION_REPORT.md` (Gate Full — from checker run)

Final git status proof:
- A file containing `git status --short` output (may be inline in EVIDENCE_CONSISTENCY_REGISTER.md or a standalone file named `git_status_final.txt` or similar)

Gate source proof:
- `gate_used/` directory (copy of gate folder used) OR `gate_hash.txt` (SHA256 of gate folder)
- A local path to `/Users/syedhaider/Downloads/gate` is NOT acceptable as proof

Gate 5.3 — Final Packet Auditor:
- `FINAL_PACKET_AUDITOR_REPORT.md` produced by an independent context-light auditor (state 37)
- All five required fields present (VERDICT, REASON, BLOCKERS, REQUIRED_FIX, RERUN_FROM)
- Verdict must be PASS for PASS_HANDOFF_COMPLETE — FAIL routes to FIX_CYCLE; HUMAN_DECISION_REQUIRED routes to BLOCKED_HANDOFF

**Missing any mandatory item above is a BLOCKER — do not issue PASS_HANDOFF_COMPLETE.**

---

## Final step

1. Write to CURRENT_STATE.yaml:
   ```yaml
   current_state: PASS_HANDOFF_COMPLETE
   gate_completed: true
   final_gate_verdict: PASS_FOR_HANDOFF
   handoff_type: PASS
   handoff_completed_at: <ISO timestamp>
   ```

2. Update `reports/<task_area>/CYCLE_TRACKER.md` final outcome section with all fields filled (no placeholders).

3. Return the handoff to the user.
