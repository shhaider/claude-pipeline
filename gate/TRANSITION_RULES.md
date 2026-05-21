# Transition Rules

This file defines every allowed state transition in the gate state machine.
A transition not listed here is **forbidden**. If you are about to write a state
to CURRENT_STATE.yaml that is not in the `allowed_from` list for that state,
stop — you have a state machine violation. Record it as a blocker.

## Gate 5.2 final transition barrier

Do not transition into any final PASS handoff state when:
- the selected gate profile is weaker than the mechanically required profile
- the final package fails exact-path proof validation
- raw outputs do not prove `EXIT_CODE:0`
- the final checker report is missing in `--final` mode

---

## How to use this file

Before writing a new state to CURRENT_STATE.yaml:
1. Find the new state in the table below
2. Confirm `current_state` appears in that state's `allowed_from` list
3. If yes: proceed with the write
4. If no: you are attempting a forbidden transition — record the violation in CYCLE_TRACKER.md and stop

---

## Allowed transitions

### Initialization

| New state | Allowed from |
|---|---|
| `CYCLE_TRACKER_INITIALIZED` | `GATE_NOT_STARTED` |
| `GATE_PROFILE_SELECTION_IN_PROGRESS` | `CYCLE_TRACKER_INITIALIZED` |

### Gate Profile Selection (Step 18) — Gate 4.1

| New state | Allowed from | Additional constraint |
|---|---|---|
| `GATE_PROFILE_SELECTION_COMPLETE` | `GATE_PROFILE_SELECTION_IN_PROGRESS` | Profile and risk tier must be recorded |
| `GATE_PROFILE_SELECTION_BLOCKED` | `GATE_PROFILE_SELECTION_IN_PROGRESS` | Reason for block must be stated |
| `EVIDENCE_ADEQUACY_IN_PROGRESS` | `GATE_PROFILE_SELECTION_COMPLETE`, `FIX_CYCLE_COMPLETE` | Profile selection must be COMPLETE, not BLOCKED |

### Evidence Adequacy Assessment (Step 01)

| New state | Allowed from |
|---|---|
| `EVIDENCE_ALREADY_ADEQUATE` | `EVIDENCE_ADEQUACY_IN_PROGRESS` |
| `EVIDENCE_UPGRADE_REQUIRED` | `EVIDENCE_ADEQUACY_IN_PROGRESS` |
| `EVIDENCE_BLOCKED_REQUIRES_HUMAN` | `EVIDENCE_ADEQUACY_IN_PROGRESS` |

### Test and Evidence Plan (Step 02)

| New state | Allowed from |
|---|---|
| `TEST_PLAN_IN_PROGRESS` | `EVIDENCE_UPGRADE_REQUIRED` |
| `TEST_PLAN_COMPLETE` | `TEST_PLAN_IN_PROGRESS` |

### Evidence Consistency Preflight (Step 03)

| New state | Allowed from |
|---|---|
| `EVIDENCE_CONSISTENCY_IN_PROGRESS` | `EVIDENCE_ALREADY_ADEQUATE`, `TEST_PLAN_COMPLETE` |
| `EVIDENCE_CONSISTENCY_PASS` | `EVIDENCE_CONSISTENCY_IN_PROGRESS` |
| `EVIDENCE_CONSISTENCY_BLOCKED` | `EVIDENCE_CONSISTENCY_IN_PROGRESS` |

### Enforcement Authority Audit (Step 14)

| New state | Allowed from |
|---|---|
| `ENFORCEMENT_AUDIT_NOT_APPLICABLE` | `EVIDENCE_CONSISTENCY_PASS` |
| `ENFORCEMENT_AUDIT_IN_PROGRESS` | `EVIDENCE_CONSISTENCY_PASS`, `ENFORCEMENT_AUDIT_FAIL_AUTOFIX` |
| `ENFORCEMENT_AUDIT_PASS` | `ENFORCEMENT_AUDIT_IN_PROGRESS` |
| `ENFORCEMENT_AUDIT_FAIL_AUTOFIX` | `ENFORCEMENT_AUDIT_IN_PROGRESS` |
| `ENFORCEMENT_AUDIT_FAIL_BLOCKED` | `ENFORCEMENT_AUDIT_IN_PROGRESS` |

### Panel Entry (Step 04)

| New state | Allowed from |
|---|---|
| `PANEL_ENTRY_VERIFIED` | `ENFORCEMENT_AUDIT_NOT_APPLICABLE`, `ENFORCEMENT_AUDIT_PASS` |

### Reviewer states (Steps 05–09)

| New state | Allowed from |
|---|---|
| `R1_IN_PROGRESS` | `PANEL_ENTRY_VERIFIED` |
| `R1_COMPLETE` | `R1_IN_PROGRESS` |
| `R2_IN_PROGRESS` | `R1_COMPLETE` |
| `R2_COMPLETE` | `R2_IN_PROGRESS` |
| `R3_IN_PROGRESS` | `R2_COMPLETE` |
| `R3_COMPLETE` | `R3_IN_PROGRESS` |
| `R4_IN_PROGRESS` | `R3_COMPLETE` |
| `R4_COMPLETE` | `R4_IN_PROGRESS` |
| `R5_IN_PROGRESS` | `R4_COMPLETE` |
| `R5_COMPLETE` | `R5_IN_PROGRESS` |

### Gate Verdict (Step 10)

| New state | Allowed from | Additional constraint |
|---|---|---|
| `GATE_VERDICT_ISSUED` | `R5_COMPLETE` | — |
| `GATE_PASS_FOR_HANDOFF` | `GATE_VERDICT_ISSUED` | `enforcement_audit_result` must be `PASS` or `NOT_APPLICABLE` in this cycle |
| `GATE_FAIL_AUTOFIX_REQUIRED` | `GATE_VERDICT_ISSUED` | — |
| `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` | `GATE_VERDICT_ISSUED` | — |

### Fix Cycle (Step 11)

| New state | Allowed from | Additional constraint |
|---|---|---|
| `FIX_CYCLE_IN_PROGRESS` | `GATE_FAIL_AUTOFIX_REQUIRED`, `FINAL_PACKAGE_AUDIT_FAIL`, `CANONICAL_HANDOFF_AUDIT_FAIL` | — |
| `FIX_CYCLE_COMPLETE` | `FIX_CYCLE_IN_PROGRESS` | `cycle_count` must be < 5 |
| `MAX_CYCLES_REACHED` | `GATE_FAIL_AUTOFIX_REQUIRED`, `FIX_CYCLE_IN_PROGRESS` | `cycle_count` must be = 5 |

### Package and Handoff Audit (Steps 15–16)

| New state | Allowed from |
|---|---|
| `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | `GATE_PASS_FOR_HANDOFF` |
| `FINAL_PACKAGE_AUDIT_PASS` | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` |
| `FINAL_PACKAGE_AUDIT_FAIL` | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` |
| `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` | `FINAL_PACKAGE_AUDIT_PASS` |
| `CANONICAL_HANDOFF_AUDIT_PASS` | `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` |
| `CANONICAL_HANDOFF_AUDIT_FAIL` | `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` |

### Execution Context Audit (Step 17)

| New state | Allowed from | Additional constraint |
|---|---|---|
| `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` | `CANONICAL_HANDOFF_AUDIT_PASS` | No execution-context claims detected in any document |
| `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` | `CANONICAL_HANDOFF_AUDIT_PASS` | One or more execution-context claims detected |
| `EXECUTION_CONTEXT_AUDIT_PASS` | `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` | All claims have branch/HEAD/cwd proof |
| `EXECUTION_CONTEXT_AUDIT_FAIL` | `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` | One or more claims lack required proof |

### Gate 4.1 Additional Transitions (Steps 19–36)

#### Prompt Contract Review (Step 19)
| New state | Allowed from |
|---|---|
| `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` | `GATE_PROFILE_SELECTION_COMPLETE` |
| `PROMPT_CONTRACT_PASS` | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` |
| `PROMPT_CONTRACT_NEEDS_REVISION` | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` |
| `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY` | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` |

#### Production Caller Audit (Step 20)
| New state | Allowed from |
|---|---|
| `PRODUCTION_CALLER_AUDIT_IN_PROGRESS` | `R5_COMPLETE`, `PANEL_ENTRY_VERIFIED` |
| `PRODUCTION_CALLER_AUDIT_PASS` | `PRODUCTION_CALLER_AUDIT_IN_PROGRESS` |
| `PRODUCTION_CALLER_AUDIT_FAIL` | `PRODUCTION_CALLER_AUDIT_IN_PROGRESS` |

#### Consumer API Proof Audit (Step 21)
| New state | Allowed from |
|---|---|
| `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` | `R2_COMPLETE` |
| `CONSUMER_API_PROOF_AUDIT_PASS` | `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` |
| `CONSUMER_API_PROOF_AUDIT_FAIL` | `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` |

#### Warning Output Audit (Step 22)
| New state | Allowed from |
|---|---|
| `WARNING_OUTPUT_AUDIT_IN_PROGRESS` | `R2_COMPLETE` |
| `WARNING_OUTPUT_AUDIT_PASS` | `WARNING_OUTPUT_AUDIT_IN_PROGRESS` |
| `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` | `WARNING_OUTPUT_AUDIT_IN_PROGRESS` |

#### Required Test Set Exactness (Step 23)
| New state | Allowed from |
|---|---|
| `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` | `PANEL_ENTRY_VERIFIED` |
| `REQUIRED_TEST_SET_EXACTNESS_PASS` | `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` |
| `REQUIRED_TEST_SET_EXACTNESS_FAIL` | `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` |

#### Migration Runner Proof (Step 24)
| New state | Allowed from |
|---|---|
| `MIGRATION_RUNNER_PROOF_IN_PROGRESS` | `EVIDENCE_ADEQUACY_IN_PROGRESS` |
| `MIGRATION_RUNNER_PROVEN` | `MIGRATION_RUNNER_PROOF_IN_PROGRESS` |
| `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN` | `MIGRATION_RUNNER_PROOF_IN_PROGRESS` |
| `MIGRATION_BLOCKED` | `MIGRATION_RUNNER_PROOF_IN_PROGRESS` |

#### Implementer Prompt Lint (Step 25)
| New state | Allowed from |
|---|---|
| `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` | `GATE_PROFILE_SELECTION_COMPLETE` |
| `IMPLEMENTER_PROMPT_LINT_PASS` | `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` |
| `IMPLEMENTER_PROMPT_LINT_FAIL` | `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` |

#### Stranded Helper Audit (Step 26)
| New state | Allowed from |
|---|---|
| `STRANDED_HELPER_AUDIT_IN_PROGRESS` | `R3_COMPLETE` |
| `STRANDED_HELPER_AUDIT_PASS` | `STRANDED_HELPER_AUDIT_IN_PROGRESS` |
| `STRANDED_HELPER_AUDIT_FAIL` | `STRANDED_HELPER_AUDIT_IN_PROGRESS` |

#### Dirty Worktree Recurrence Audit (Step 27)
| New state | Allowed from |
|---|---|
| `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` | `EVIDENCE_CONSISTENCY_IN_PROGRESS` |
| `DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS` | `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` |
| `DIRTY_WORKTREE_RECURRENCE_BLOCKER` | `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` |

#### Work Allocation Audit (Step 28)
| New state | Allowed from |
|---|---|
| `WORK_ALLOCATION_AUDIT_IN_PROGRESS` | `GATE_PROFILE_SELECTION_COMPLETE` |
| `WORK_ALLOCATION_CLEAR` | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` |
| `WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE` | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` |
| `WORK_ALLOCATION_BLOCKED_BY_CONFLICT` | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` |
| `WORK_ALLOCATION_NEEDS_HUMAN` | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` |

#### Export Channel Audit (Step 29)
| New state | Allowed from |
|---|---|
| `EXPORT_CHANNEL_AUDIT_IN_PROGRESS` | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` |
| `EXPORT_CHANNEL_AUDIT_PASS` | `EXPORT_CHANNEL_AUDIT_IN_PROGRESS` |
| `EXPORT_CHANNEL_AUDIT_FAIL` | `EXPORT_CHANNEL_AUDIT_IN_PROGRESS` |

#### Diff Base / Scope Audit (Step 30)
| New state | Allowed from |
|---|---|
| `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` | `EVIDENCE_CONSISTENCY_IN_PROGRESS` |
| `DIFF_BASE_SCOPE_AUDIT_PASS` | `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` |
| `DIFF_BASE_SCOPE_AUDIT_FAIL` | `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` |

#### Flake / Timeout Audit (Step 31)
| New state | Allowed from |
|---|---|
| `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` | `TEST_PLAN_COMPLETE` |
| `TEST_STABILITY_OK` | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` |
| `TEST_STABILITY_WARNING_FOLLOWUP` | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` |
| `TEST_STABILITY_BLOCKING` | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` |

#### Concurrency Assumptions Audit (Step 32)
| New state | Allowed from |
|---|---|
| `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` | `R2_COMPLETE` |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_PASS` | `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL` | `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` |

#### Downstream Consumer Readiness Audit (Step 33)
| New state | Allowed from |
|---|---|
| `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` | `R4_COMPLETE` |
| `DOWNSTREAM_READY` | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` |
| `DOWNSTREAM_READY_WITH_CAVEAT` | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` |
| `DOWNSTREAM_NOT_READY` | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` |

#### Next Prompt Decision (Step 34)
| New state | Allowed from |
|---|---|
| `NEXT_PROMPT_DECISION_IN_PROGRESS` | `R5_COMPLETE` |
| `NEXT_PROMPT_DECISION_COMPLETE` | `NEXT_PROMPT_DECISION_IN_PROGRESS` |

#### CTO / Operator Insight Review (Step 35)
| New state | Allowed from |
|---|---|
| `CTO_OPERATOR_INSIGHT_REVIEW_IN_PROGRESS` | `R5_COMPLETE` |
| `CTO_OPERATOR_INSIGHT_REVIEW_COMPLETE` | `CTO_OPERATOR_INSIGHT_REVIEW_IN_PROGRESS` |

#### Gate Effectiveness Log (Step 36)
| New state | Allowed from |
|---|---|
| `GATE_EFFECTIVENESS_LOG_IN_PROGRESS` | `PASS_HANDOFF_COMPLETE`, `GATE_LITE_PASS_HANDOFF_COMPLETE`, `GATE_STANDARD_PASS_HANDOFF_COMPLETE`, `GATE_FULL_PASS_HANDOFF_COMPLETE`, `BLOCKED_HANDOFF_COMPLETE` |
| `GATE_EFFECTIVENESS_LOG_COMPLETE` | `GATE_EFFECTIVENESS_LOG_IN_PROGRESS` |

### Final Packet Auditor (Step 37 — Gate 5.3)

| New state | Allowed from | Additional constraint |
|---|---|---|
| `FINAL_PACKET_AUDITOR` | `CANONICAL_HANDOFF_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` | Auditor session is fresh / independent when possible; report file written to `reports/<task_area>/FINAL_PACKET_AUDITOR_REPORT.md` |

## FINAL_PACKET_AUDITOR Transitions (Gate 5.3)

Required transition:
- CANONICAL_HANDOFF_AUDIT_PASS → FINAL_PACKET_AUDITOR

Verdict-driven exits:
- FINAL_PACKET_AUDITOR PASS → PASS_HANDOFF
- FINAL_PACKET_AUDITOR FAIL → FIX_CYCLE_IN_PROGRESS
- FINAL_PACKET_AUDITOR HUMAN_DECISION_REQUIRED → BLOCKED_HANDOFF_COMPLETE / GATE_BLOCKED_REQUIRES_HUMAN

Hard rule: PASS_HANDOFF_COMPLETE is BLOCKED while FINAL_PACKET_AUDITOR_VERDICT is missing, FAIL, HUMAN_DECISION_REQUIRED, or schema-invalid.

## Final Auditor Failure Rerun Policy (Gate 5.3)

### GATE_FULL and GATE_FULL_PLUS_DOMAIN_ADDENDUM
- Any FINAL_PACKET_AUDITOR_VERDICT: FAIL → fix the issues, then RESTART the gate from Evidence Adequacy.
- Re-run all required reviewers and audits.
- Reason: a fix can change evidence, scope, tests, package contents, or report consistency. A surface-only re-check is unsafe.

### GATE_STANDARD
- If the fix changes source, tests, runtime behavior, package contents, or status claims → restart from Evidence Adequacy.
- If the fix is only a typo in a non-authoritative report and no proof artifacts changed → targeted rerun allowed:
  RERUN_FROM: TARGETED_STATE:<state name>
  followed by FINAL_PACKET_AUDITOR again.

### GATE_LITE
- Targeted rerun allowed for docs-only / report-only fixes.
- If source/test/runtime artifacts changed → upgrade profile to GATE_STANDARD or GATE_FULL based on profile selection.

### Repeated failure
If the same package fails FINAL_PACKET_AUDITOR twice:
- Escalate one profile level (Lite → Standard, Standard → Full, Full → Full+Domain) if possible.
- Require CTO / Operator Insight Review.
- Record in Gate Effectiveness Log with `repeated_final_auditor_failure: true`.

### Terminal states

| New state | Allowed from | Additional constraint |
|---|---|---|
| `GATE_LITE_PASS_HANDOFF_COMPLETE` | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE`, `FINAL_PACKET_AUDITOR` (when verdict PASS) | Profile must be GATE_LITE; `final_package_audit_result: PASS`, `canonical_handoff_audit_result: PASS` must be recorded; if signout/export, `final_packet_auditor_verdict: PASS` recorded |
| `GATE_STANDARD_PASS_HANDOFF_COMPLETE` | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE`, `FINAL_PACKET_AUDITOR` (when verdict PASS) | Profile must be GATE_STANDARD; all required STANDARD states must be recorded; `final_packet_auditor_verdict: PASS` recorded |
| `GATE_FULL_PASS_HANDOFF_COMPLETE` | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE`, `FINAL_PACKET_AUDITOR` (when verdict PASS) | Profile must be GATE_FULL or GATE_FULL_PLUS; all required FULL states must be recorded; `final_packet_auditor_verdict: PASS` recorded |
| `PASS_HANDOFF_COMPLETE` | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE`, `FINAL_PACKET_AUDITOR` (when verdict PASS) | Legacy; use profile-specific terminal states for Gate 4.1 runs; `final_package_audit_result: PASS`, `canonical_handoff_audit_result: PASS`, `execution_context_audit_result: PASS or NOT_APPLICABLE`, and (Gate 5.3) `final_packet_auditor_verdict: PASS` must be recorded |
| `BLOCKED_HANDOFF_COMPLETE` | `EVIDENCE_BLOCKED_REQUIRES_HUMAN`, `EVIDENCE_CONSISTENCY_BLOCKED`, `ENFORCEMENT_AUDIT_FAIL_BLOCKED`, `GATE_FAIL_BLOCKED_REQUIRES_HUMAN`, `MAX_CYCLES_REACHED`, `EXECUTION_CONTEXT_AUDIT_FAIL` (when HUMAN_BLOCKED), `DOWNSTREAM_NOT_READY`, `WORK_ALLOCATION_BLOCKED_BY_CONFLICT`, `MIGRATION_BLOCKED` | — |
| `GATE_BLOCKED_REQUIRES_HUMAN` | `GATE_PROFILE_SELECTION_BLOCKED`, `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY`, `WORK_ALLOCATION_NEEDS_HUMAN` | Operator must resolve before gate can proceed |
| `GATE_PROFILE_SELECTION_BLOCKED` | `GATE_PROFILE_SELECTION_IN_PROGRESS` | Reason for block must be stated in GATE_PROFILE_SELECTION.md |

---

## Pre-PASS Barrier — REQUIRED_PROFILE_AUDITS_VERIFIED (Gate 5.1)

**GATE_VERDICT cannot issue PASS unless ALL of the following are true:**

1. Every required profile state is present in CURRENT_STATE.yaml
2. Every required profile state is in PASS or OK or NOT_APPLICABLE (with documented reason) status
3. No required extra audit state is FAIL, BLOCKING, UNCERTAIN, or missing

Required routing for each blocking state when attempting to issue PASS:

| Blocking state | Required routing |
|---|---|
| `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` | → `FIX_CYCLE_IN_PROGRESS` |
| `REQUIRED_TEST_SET_EXACTNESS_FAIL` | → `FIX_CYCLE_IN_PROGRESS` |
| `PRODUCTION_CALLER_AUDIT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` (if fixable) or `GATE_BLOCKED_REQUIRES_HUMAN` |
| `CONSUMER_API_PROOF_AUDIT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` (if fixable) or `GATE_BLOCKED_REQUIRES_HUMAN` |
| `MIGRATION_BLOCKED` | → `GATE_BLOCKED_REQUIRES_HUMAN` |
| `IMPLEMENTER_PROMPT_LINT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` |
| `STRANDED_HELPER_AUDIT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` |
| `DIRTY_WORKTREE_RECURRENCE_BLOCKER` | → `GATE_BLOCKED_REQUIRES_HUMAN` |
| `EXPORT_CHANNEL_AUDIT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` |
| `DIFF_BASE_SCOPE_AUDIT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` (if trimming scope) or `GATE_BLOCKED_REQUIRES_HUMAN` |
| `TEST_STABILITY_BLOCKING` | → `FIX_CYCLE_IN_PROGRESS` |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL` | → `FIX_CYCLE_IN_PROGRESS` |
| `DOWNSTREAM_NOT_READY` | → `GATE_BLOCKED_REQUIRES_HUMAN` |
| `EXIT_CODE_BLANK` | → `FIX_CYCLE_IN_PROGRESS` |
| `EXIT_CODE_MISSING` | → `FIX_CYCLE_IN_PROGRESS` |
| `EXIT_CODE_NONZERO` | → `FIX_CYCLE_IN_PROGRESS` |
| `EXIT_CODE_CONFLICTING` | → `FIX_CYCLE_IN_PROGRESS` |
| `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` | → `FIX_CYCLE_IN_PROGRESS` |
| `POST_PASS_UNCAUGHT_ERROR` | → `FIX_CYCLE_IN_PROGRESS` |

**Terminal PASS is BLOCKED while any required audit state is:**
- missing from CURRENT_STATE.yaml
- `FAIL`
- `BLOCKING`
- `UNCERTAIN`
- `NOT_APPLICABLE` without a documented reason

This barrier is checked at two points:
1. In `10_GATE_VERDICT.md` before issuing `GATE_PASS_FOR_HANDOFF`
2. In `15_FINAL_PACKAGE_AUDIT.md` before issuing `FINAL_PACKAGE_AUDIT_PASS`

---

## Forbidden transitions (examples of common violations)

These are transitions that look plausible but are explicitly forbidden:

| From | To (FORBIDDEN) | Why |
|---|---|---|
| `R5_COMPLETE` | `PASS_HANDOFF_COMPLETE` | Must go through GATE_PASS_FOR_HANDOFF → FINAL_PACKAGE_AUDIT → CANONICAL_HANDOFF_AUDIT → EXECUTION_CONTEXT_AUDIT first |
| `GATE_PASS_FOR_HANDOFF` | `PASS_HANDOFF_COMPLETE` | Steps 15, 16, and 17 are all mandatory |
| `CANONICAL_HANDOFF_AUDIT_PASS` | `PASS_HANDOFF_COMPLETE` | Step 17 (execution context audit) must run first |
| `R4_COMPLETE` | `GATE_VERDICT_ISSUED` | R5 must run; R5 is the sole verdict producer |
| `EVIDENCE_CONSISTENCY_PASS` | `PANEL_ENTRY_VERIFIED` | Enforcement audit step is mandatory between them |
| `FIX_CYCLE_COMPLETE` | `PANEL_ENTRY_VERIFIED` | Must restart from EVIDENCE_ADEQUACY_IN_PROGRESS |
| `FIX_CYCLE_COMPLETE` | `R1_IN_PROGRESS` | Must restart from EVIDENCE_ADEQUACY_IN_PROGRESS |
| Any state | `PASS_HANDOFF_COMPLETE` when `enforcement_audit_result: FAIL*` | Pass not allowed with enforcement audit failure |

---

## State machine violation protocol

If you detect a forbidden transition:

1. Do not proceed with the transition
2. Record in CYCLE_TRACKER.md: `STATE_MACHINE_VIOLATION: attempted [from] → [to], forbidden`
3. Set `current_state` to `GATE_FAIL_BLOCKED_REQUIRES_HUMAN`
4. Route to `13_BLOCKED_HANDOFF.md` with blocker: "State machine violation detected"
