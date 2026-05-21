# State Machine Examples

---

## Example 1 — The Governance-Fixes Failure

This example shows exactly what failed in the `agentos-ng-governance-fixes` package, and at which step the new state machine would have caught each failure.

### What happened (the failure)

The gate ran 3 cycles and reached what appeared to be PASS_FOR_HANDOFF. The package was shipped with:

1. **Missing files**: CYCLE3_GATE_VERDICT.md claimed e2e_v2 tests were run and e2e_v2 output files were present — but the zip did not contain them.
2. **Local-path-only manifest**: MANIFEST.md entries referenced paths like `/Users/agent/project/reports/...` — not portable paths. Any agent on a different machine following the manifest would find nothing.
3. **Contradictory handoff state**: HANDOFF.md said `Readiness: PENDING`. CYCLE3_GATE_VERDICT.md said `PASS`. These contradicted each other; no single file authoritatively resolved the state.
4. **Unlabeled stale document**: BLOCKED_HANDOFF.md from Cycle 2 remained in the package root without a HISTORICAL banner. An agent reading the package could not tell whether this was the active handoff or a historical artifact.

### How the new gate catches each failure

**Failure 1 — Missing files in zip**

At `15_FINAL_PACKAGE_AUDIT.md` Step 3 (Manifest audit):
- Package contents listed via `zipinfo -1` would not show the e2e_v2 output files
- Manifest entries for those files would fail the `Present in package` check
- Result: **BLOCKER — file claimed in manifest not present in package**
- Gate cannot proceed to `12_PASS_HANDOFF.md`

At `15_FINAL_PACKAGE_AUDIT.md` Step 4 (Claims ledger audit):
- CLAIMS_LEDGER.yaml entry: `claim_text: "e2e_v2 tests ran successfully"`, `evidence_artifact_path: "reports/agentos-ng-governance-fixes/e2e_v2_output.log"`
- Check: is `e2e_v2_output.log` in the package? → NO
- Result: `verification_result: NOT_IN_PACKAGE`, `hard_fact_verified: false`
- Result: **BLOCKER**

**Failure 2 — Local-path-only manifest entries**

At `15_FINAL_PACKAGE_AUDIT.md` Step 3:
- Path `/Users/agent/project/reports/...` detected as local-machine prefix
- Result: `verification_result: LOCAL_PATH_ONLY`
- Result: **BLOCKER — path is not portable**
- Fix required: replace with relative path `reports/<task_area>/...`

**Failure 3 — Contradictory handoff state**

At `15_FINAL_PACKAGE_AUDIT.md` Step 7 (Handoff status pre-check):
- HANDOFF.md `Final readiness status: PENDING` detected
- Result: **BLOCKER — HANDOFF.md must say READY, not PENDING**

At `16_CANONICAL_HANDOFF_AUDIT.md` Step 4 (Unregistered stale file scan):
- HANDOFF.md says PENDING; CURRENT_STATE.yaml `final_gate_verdict: PASS_FOR_HANDOFF`
- Status is inconsistent → **BLOCKER — unregistered stale status**

**Failure 4 — Unlabeled BLOCKED_HANDOFF.md**

At `16_CANONICAL_HANDOFF_AUDIT.md` Step 3 (Stale file register audit):
- BLOCKED_HANDOFF.md present in package
- `STALE_FILE_REGISTER.yaml` entry: `banner_added: false`
- Result: **BLOCKER — HISTORICAL banner not added to BLOCKED_HANDOFF.md**

At `16_CANONICAL_HANDOFF_AUDIT.md` Step 5 (Exactly-one-active-handoff check):
- Un-labeled BLOCKED_HANDOFF.md counts as "active" → two active handoffs detected
- `final_gate_verdict: PASS_FOR_HANDOFF` but BLOCKED_HANDOFF.md is unlabeled
- Result: **BLOCKER — more than one active handoff document**

### What the CURRENT_STATE.yaml would show at the point of failure

```yaml
current_state: FINAL_PACKAGE_AUDIT_FAIL
final_package_audit_result: FAIL
cycles:
  3:
    r5_verdict: READY_FOR_REVIEW
    gate_verdict: PASS_FOR_HANDOFF
final_gate_verdict: null    # NOT written — audit failed, no pass issued
```

The gate would have remained in `FINAL_PACKAGE_AUDIT_FAIL` state. No pass handoff would have been issued. The agent would have been required to fix:
1. Include the missing e2e_v2 files in the zip
2. Replace local paths with relative paths in MANIFEST.md
3. Update HANDOFF.md status from PENDING to READY
4. Add HISTORICAL banner to BLOCKED_HANDOFF.md and register it in STALE_FILE_REGISTER.yaml

---

## Example 2 — Clean Single-Cycle Run

### What happens

Task: Add a new CLI flag to a tool. No enforcement scope.

| Step | State written | Note |
|---|---|---|
| Gate entry | `CYCLE_TRACKER_INITIALIZED` | Created CYCLE_TRACKER.md, CLAIMS_LEDGER.yaml, EVIDENCE_LEDGER.yaml, STALE_FILE_REGISTER.yaml |
| Evidence adequacy | `EVIDENCE_ALREADY_ADEQUATE` | Diff, test log, snapshot all present |
| Consistency preflight | `EVIDENCE_CONSISTENCY_PASS` | 8 checks passed |
| Enforcement audit | `ENFORCEMENT_AUDIT_NOT_APPLICABLE` | No enforcement/gating scope |
| Panel entry | `PANEL_ENTRY_VERIFIED` | Pre-panel gate check passed |
| R1 | `R1_COMPLETE` | 0 blocking, 1 non-blocking |
| R2 | `R2_COMPLETE` | 0 blocking |
| R3 | `R3_COMPLETE` | 0 blocking |
| R4 | `R4_COMPLETE` | 0 blocking |
| R5 | `R5_COMPLETE` | READY_FOR_REVIEW |
| Gate verdict | `GATE_PASS_FOR_HANDOFF` | Enforcement NOT_APPLICABLE, R5 READY |
| Package audit | `FINAL_PACKAGE_AUDIT_PASS` | All files in zip confirmed |
| Handoff audit | `CANONICAL_HANDOFF_AUDIT_PASS` | One active HANDOFF.md, READY status |
| Terminal | `PASS_HANDOFF_COMPLETE` | Handoff returned |

### CURRENT_STATE.yaml at terminal state

```yaml
current_state: PASS_HANDOFF_COMPLETE
gate_completed: true
cycle_count: 1
final_gate_verdict: PASS_FOR_HANDOFF
final_r5_verdict: READY_FOR_REVIEW
handoff_type: PASS
final_package_audit_result: PASS
canonical_handoff_audit_result: PASS
cycles:
  1:
    evidence_adequacy_decision: EVIDENCE_ALREADY_ADEQUATE
    consistency_result: PASS
    enforcement_audit_result: NOT_APPLICABLE
    r1_blocking: 0
    r2_blocking: 0
    r3_blocking: 0
    r4_blocking: 0
    r5_verdict: READY_FOR_REVIEW
    gate_verdict: PASS_FOR_HANDOFF
    blockers_autofix: 0
    blockers_human_blocked: 0
```

---

## Example 3 — Multi-Cycle Run with Fix

### What happens

Task: Implement a new database migration. Test evidence needed upgrade in cycle 1.

| Cycle | Gate verdict | Fix applied |
|---|---|---|
| Cycle 1 | `FAIL_AUTOFIX_REQUIRED` | R2: missing rollback test output. Added test, saved output. |
| Cycle 2 | `PASS_FOR_HANDOFF` | All reviewers passed. Package audit passed. |

### STALE_FILE_REGISTER.yaml after completion

```yaml
stale_files:
  - file_path: "reports/<task_area>/COLD_REVIEW_ADJUDICATION.md"
    classification: HISTORICAL_PRIOR_CYCLE
    became_stale_at: "2026-04-30T15:00:00Z"
    became_stale_reason: "Cycle 1 gate failed. Superseded by cycle 2 COLD_REVIEW_ADJUDICATION.md"
    cycle_produced: 1
    superseded_by: "reports/<task_area>/CYCLE2_COLD_REVIEW_ADJUDICATION.md"
    banner_added: true
    include_in_package: true
    package_location: "<task_area>/prior_cycles/CYCLE1_COLD_REVIEW_ADJUDICATION.md"
```

The cycle 1 adjudication file gets the HISTORICAL banner and moves to `prior_cycles/`. The cycle 2 adjudication file lives in the root. The canonical handoff audit passes because there is exactly one un-labeled HANDOFF.md.
