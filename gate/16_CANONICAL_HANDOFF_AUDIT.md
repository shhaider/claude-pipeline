# Step 16 — Canonical Handoff Audit

> **Gate 5.3 ordering note:** After this audit returns CANONICAL_HANDOFF_AUDIT_PASS, the Final Packet Auditor (state 37, file `37_FINAL_PACKET_AUDITOR.md`) runs as the last independent gate before PASS_HANDOFF_COMPLETE. This step is not the last barrier under Gate 5.3.

## Gate 5.4 canonical handoff barrier

Do not certify canonical PASS unless the exported package includes the final checker report and the executable checker passed in `--final` mode.

You are here because `15_FINAL_PACKAGE_AUDIT.md` returned `FINAL_PACKAGE_AUDIT_PASS` and `CURRENT_STATE.yaml` is now in state `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS`.

This is the last gate before `12_PASS_HANDOFF.md`. It verifies that the handoff package has exactly one canonical, non-contradictory state — and that state matches the gate's final verdict.

**Why this step exists:** The governance-fixes failure included three contradictory documents: HANDOFF.md said PENDING, CYCLE3_GATE_VERDICT.md said PASS, and BLOCKED_HANDOFF.md was unlabeled. A downstream agent reading any of these three files would have reached a different conclusion about the package state. This audit catches that.

---

## Step 1 — Write CURRENT_STATE.yaml

```yaml
current_state: CANONICAL_HANDOFF_AUDIT_IN_PROGRESS
```

---

## Step 2 — Identify all status-bearing documents

List every file in the package that contains a status claim (PASS, FAIL, BLOCKED, PENDING, READY, COMPLETE, etc.):

```
Status-bearing documents found:
- [filename]: claims [status]
- [filename]: claims [status]
...
```

Common status-bearing documents to check:
- HANDOFF.md → Final readiness status
- BLOCKED_HANDOFF.md → Overall status
- CYCLE_TRACKER.md → Final outcome section
- COLD_REVIEW_ADJUDICATION.md (final cycle) → R5 verdict
- CURRENT_STATE.yaml → `current_state`
- PACKAGE_MANIFEST.md → Manifest status

---

## Step 3 — Stale file register audit

Open `reports/<task_area>/STALE_FILE_REGISTER.yaml`.

For every entry:
1. Does the file exist in the package?
2. Does it have the HISTORICAL banner at the very top?

If any registered stale file is missing the banner: **blocker**.

---

## Step 4 — Unregistered stale file scan

For every status-bearing document identified in Step 2:
1. Is this file in `STALE_FILE_REGISTER.yaml` (registered as stale)?
2. If NOT registered: is the status consistent with the gate's final verdict?
3. If inconsistent: this file is an **unregistered stale file** — **blocker**

Examples of inconsistency to catch:
- BLOCKED_HANDOFF.md exists with status = BLOCKED, but `final_gate_verdict` in CURRENT_STATE.yaml = PASS_FOR_HANDOFF → must be labeled HISTORICAL
- HANDOFF.md `Final readiness status` = PENDING, but R5 verdict = READY_FOR_REVIEW → must be updated to READY
- Prior cycle COLD_REVIEW_ADJUDICATION.md says NEEDS_CORRECTION, but current cycle says READY_FOR_REVIEW, and prior cycle file is not labeled → must be labeled HISTORICAL

---

## Step 5 — Exactly-one-active-handoff check

After accounting for HISTORICAL-labeled files:
1. How many un-labeled HANDOFF.md files exist? → Must be exactly 1
2. How many un-labeled BLOCKED_HANDOFF.md files exist? → Must be exactly 0 (if gate passed) or exactly 1 (if gate blocked)
3. Does the active handoff's status match `final_gate_verdict` in CURRENT_STATE.yaml?

| `final_gate_verdict` | Expected active handoff | Expected BLOCKED_HANDOFF |
|---|---|---|
| `PASS_FOR_HANDOFF` | HANDOFF.md with READY status | Must be labeled HISTORICAL or absent |
| `FAIL_BLOCKED_REQUIRES_HUMAN` | BLOCKED_HANDOFF.md with active status | Must be the active handoff |

If count or status is wrong: **blocker**.

---

## Step 6 — Five reviewer reports from final cycle

The final package must contain all 5 reviewer reports from the most recent cycle:
- `COLD_REVIEW_REQUIREMENTS_AUDIT.md` (or `CYCLE{N}_COLD_REVIEW_REQUIREMENTS_AUDIT.md`)
- `COLD_REVIEW_ACTIVE_PROOF_AUDIT.md`
- `COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md`
- `COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md`
- `COLD_REVIEW_ADJUDICATION.md`

For multi-cycle runs: the most recent cycle's reports should be in the root of the task area folder. Prior cycle reports should be labeled HISTORICAL and moved to `prior_cycles/`.

Missing final-cycle reviewer report: **blocker**.

---

## Step 7 — CYCLE_TRACKER.md final outcome

Open CYCLE_TRACKER.md. Navigate to the "Final outcome" section.

Verify:
- `Total cycles run`: matches `cycle_count` in CURRENT_STATE.yaml
- `Final gate verdict`: matches `final_gate_verdict` in CURRENT_STATE.yaml
- `Handoff allowed`: YES (if gate passed)
- The final outcome section is filled — not `[N]` placeholders

Any placeholder remaining in the final outcome section: **blocker**.

---

## Step 8 — Verdict and routing

### If zero blockers

Update CURRENT_STATE.yaml:
```yaml
current_state: CANONICAL_HANDOFF_AUDIT_PASS
canonical_handoff_audit_result: PASS
```

Update STALE_FILE_REGISTER.yaml `audit_verdict: PASS`.

Route to: `17_EXECUTION_CONTEXT_AUDIT.md`

### If one or more blockers

Fix each blocker (within scope):
- Missing HISTORICAL banner → add it
- HANDOFF.md PENDING → update to READY
- Prior cycle report unlabeled → add HISTORICAL banner and register in STALE_FILE_REGISTER.yaml
- CYCLE_TRACKER.md placeholder → fill it
- Missing reviewer report → cannot be autofixed → route to `13_BLOCKED_HANDOFF.md`

After fixing all autofixable blockers, re-run this step from Step 2.

If a blocker cannot be fixed within scope:
```yaml
current_state: CANONICAL_HANDOFF_AUDIT_FAIL
canonical_handoff_audit_result: FAIL
```
Route to: `13_BLOCKED_HANDOFF.md`

---

## Step 8b — Execution context claim detection

Before finalizing the verdict, scan every status-bearing document for execution-context claims:
- "tested on main"
- "post-merge tests ran on main"
- "main stayed unchanged"
- "ORCH merged only into integration"
- "package listing generated from export"
- "final git status was clean"
- "smoke test ran after merge"

If any such claim exists, record it in CURRENT_STATE.yaml:
```yaml
cycles:
  <N>:
    execution_context_audit_applicable: true
```

This flag ensures routing proceeds to Step 17 rather than directly to Step 12.

---

## Routing summary

| Outcome | Next file |
|---|---|
| Zero blockers, no execution-context claims | `17_EXECUTION_CONTEXT_AUDIT.md` (will return NOT_APPLICABLE) |
| Zero blockers, execution-context claims present | `17_EXECUTION_CONTEXT_AUDIT.md` |
| Blockers fixed within scope | Re-run `16_CANONICAL_HANDOFF_AUDIT.md` from Step 2 |
| Blocker cannot be fixed | `13_BLOCKED_HANDOFF.md` |

**Note:** Step 16 always routes to Step 17. Step 17 determines its own applicability. The reason: Step 16 does not perform the full context audit — it only detects whether claims exist. The audit work happens in Step 17.

---

## Gate 4.1 — Overclaim taxonomy verification (append)

Before issuing `CANONICAL_HANDOFF_AUDIT_PASS`, verify that the handoff uses the correct outcome label from the Gate 4.1 overclaim taxonomy.

**Scan the handoff for the final outcome label:**

The handoff must include exactly one of:
- `LIVE_BEHAVIOR_FIXED`
- `INFRASTRUCTURE_READY_NOT_WIRED`
- `TEST_HELPER_ONLY`
- `DOCS_ONLY`
- `MERGE_VERIFIED`
- `MERGE_NOT_VERIFIED`
- `PREPLANNING_READY`
- `PREPLANNING_BLOCKED`
- `PACKAGE_READY_FOR_REVIEW`
- `PACKAGE_BLOCKED`

If the handoff only says "READY_FOR_HANDOFF" without a specific outcome label: **blocker** — add the correct label before issuing PASS.

If the handoff says `LIVE_BEHAVIOR_FIXED` but the Production Caller Audit found no production caller: **blocker** — label must be `INFRASTRUCTURE_READY_NOT_WIRED` or `TEST_HELPER_ONLY`.

If the handoff says `MERGE_VERIFIED` but no `git log` proof of merge is in the package: **blocker** — must be `MERGE_NOT_VERIFIED`.

---

## Gate 5.2-R1 — Output-Contract structured verdict reference (append)

The canonical-handoff audit relies on `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` to detect
cross-surface label drift. Under Gate 5.2-R1, that audit should declare its verdict in a
fenced YAML block:

````markdown
```yaml
output_contract_consistency:
  verdict: PASS  # or FAIL or UNCERTAIN
  blocking_findings: []
  checked_surfaces:
    - HANDOFF
    - RUNTIME_SCOPE_CHECK
    - RTM
    - MANIFEST
    - source snapshots
    - tests
    - diff
```
````

The structured form lets the checker accept negated prose like "No STALE_MILESTONE_LABEL
found" without firing a false-positive token detection. See
`OUTPUT_CONTRACT_CONSISTENCY_AUDIT_TEMPLATE.md` for the copyable template and
`15_FINAL_PACKAGE_AUDIT.md` for the full Gate 5.2-R1 enforcement spec.
