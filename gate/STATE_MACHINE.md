# Gate State Machine — Master State List

## Gate 5.2 enforcement note

Terminal PASS is invalid unless the exported package also passes `tools/check_gate_package.py --final` and includes `reports/<task_area>/GATE_PACKAGE_VALIDATION_REPORT.md`.

The gate is a strict state machine. `CURRENT_STATE.yaml` in `reports/<task_area>/` is the **single source of truth** for the current state of any gate run. Every gate step must read CURRENT_STATE.yaml at entry and write it at exit.

No step may produce a verdict, pass, or handoff without the required prior states recorded in CURRENT_STATE.yaml.

---

## State index

### Initialization states

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `GATE_NOT_STARTED` | Gate not yet entered | (initial) | `CYCLE_TRACKER_INITIALIZED` |
| `CYCLE_TRACKER_INITIALIZED` | CYCLE_TRACKER.md, CLAIMS_LEDGER.yaml, EVIDENCE_LEDGER.yaml created | `GATE_NOT_STARTED` | `GATE_PROFILE_SELECTION_IN_PROGRESS` |

### Gate Profile Selection states (Step 18) — Gate 4.1

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `GATE_PROFILE_SELECTION_IN_PROGRESS` | Running 18_GATE_PROFILE_SELECTION.md | `CYCLE_TRACKER_INITIALIZED` | `GATE_PROFILE_SELECTION_COMPLETE`, `GATE_PROFILE_SELECTION_BLOCKED` |
| `GATE_PROFILE_SELECTION_COMPLETE` | Profile selected; GATE_PROFILE_SELECTION.md written | `GATE_PROFILE_SELECTION_IN_PROGRESS` | `EVIDENCE_ADEQUACY_IN_PROGRESS` |
| `GATE_PROFILE_SELECTION_BLOCKED` | Profile cannot be determined; human decision required | `GATE_PROFILE_SELECTION_IN_PROGRESS` | (terminal — return to operator) |

### Evidence Adequacy Assessment states (Step 01)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `EVIDENCE_ADEQUACY_IN_PROGRESS` | Running 01_EVIDENCE_ADEQUACY.md | `GATE_PROFILE_SELECTION_COMPLETE`, `FIX_CYCLE_COMPLETE` | `EVIDENCE_ALREADY_ADEQUATE`, `EVIDENCE_UPGRADE_REQUIRED`, `EVIDENCE_BLOCKED_REQUIRES_HUMAN` |
| `EVIDENCE_ALREADY_ADEQUATE` | All 10 adequacy criteria met | `EVIDENCE_ADEQUACY_IN_PROGRESS` | `EVIDENCE_CONSISTENCY_IN_PROGRESS` |
| `EVIDENCE_UPGRADE_REQUIRED` | Evidence exists but needs upgrade | `EVIDENCE_ADEQUACY_IN_PROGRESS` | `TEST_PLAN_IN_PROGRESS` |
| `EVIDENCE_BLOCKED_REQUIRES_HUMAN` | Evidence cannot be obtained within scope | `EVIDENCE_ADEQUACY_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |

### Test and Evidence Plan states (Step 02)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `TEST_PLAN_IN_PROGRESS` | Running 02_TEST_AND_EVIDENCE_PLAN.md | `EVIDENCE_UPGRADE_REQUIRED` | `TEST_PLAN_COMPLETE` |
| `TEST_PLAN_COMPLETE` | Evidence upgraded per plan | `TEST_PLAN_IN_PROGRESS` | `EVIDENCE_CONSISTENCY_IN_PROGRESS` |

### Evidence Consistency Preflight states (Step 03)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `EVIDENCE_CONSISTENCY_IN_PROGRESS` | Running 03_EVIDENCE_CONSISTENCY.md | `EVIDENCE_ALREADY_ADEQUATE`, `TEST_PLAN_COMPLETE` | `EVIDENCE_CONSISTENCY_PASS`, `EVIDENCE_CONSISTENCY_BLOCKED` |
| `EVIDENCE_CONSISTENCY_PASS` | All 8 preflight checks passed | `EVIDENCE_CONSISTENCY_IN_PROGRESS` | `ENFORCEMENT_AUDIT_IN_PROGRESS`, `ENFORCEMENT_AUDIT_NOT_APPLICABLE` |
| `EVIDENCE_CONSISTENCY_BLOCKED` | Structural contradictions cannot be fixed in scope | `EVIDENCE_CONSISTENCY_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |

### Enforcement Authority Audit states (Step 14)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `ENFORCEMENT_AUDIT_NOT_APPLICABLE` | Task has no enforcement/gating/control scope | `EVIDENCE_CONSISTENCY_PASS` | `PANEL_ENTRY_VERIFIED` |
| `ENFORCEMENT_AUDIT_IN_PROGRESS` | Running 14_ENFORCEMENT_AUTHORITY_AUDIT.md | `EVIDENCE_CONSISTENCY_PASS` | `ENFORCEMENT_AUDIT_PASS`, `ENFORCEMENT_AUDIT_FAIL_AUTOFIX`, `ENFORCEMENT_AUDIT_FAIL_BLOCKED` |
| `ENFORCEMENT_AUDIT_PASS` | All enforcement checks pass | `ENFORCEMENT_AUDIT_IN_PROGRESS` | `PANEL_ENTRY_VERIFIED` |
| `ENFORCEMENT_AUDIT_FAIL_AUTOFIX` | Enforcement gaps fixable within scope | `ENFORCEMENT_AUDIT_IN_PROGRESS` | `ENFORCEMENT_AUDIT_IN_PROGRESS` (fix loop) |
| `ENFORCEMENT_AUDIT_FAIL_BLOCKED` | Enforcement gaps require human decision | `ENFORCEMENT_AUDIT_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |

### Panel Entry state (Step 04)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `PANEL_ENTRY_VERIFIED` | Pre-panel gate check passed; enforcement audit file confirmed | `ENFORCEMENT_AUDIT_NOT_APPLICABLE`, `ENFORCEMENT_AUDIT_PASS` | `R1_IN_PROGRESS` |

### Reviewer states (Steps 05–09)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `R1_IN_PROGRESS` | Running 05_R1_REQUIREMENTS.md | `PANEL_ENTRY_VERIFIED` | `R1_COMPLETE` |
| `R1_COMPLETE` | R1 findings recorded | `R1_IN_PROGRESS` | `R2_IN_PROGRESS` |
| `R2_IN_PROGRESS` | Running 06_R2_ACTIVE_PROOF.md | `R1_COMPLETE` | `R2_COMPLETE` |
| `R2_COMPLETE` | R2 findings recorded | `R2_IN_PROGRESS` | `R3_IN_PROGRESS` |
| `R3_IN_PROGRESS` | Running 07_R3_AI_PATTERNS.md | `R2_COMPLETE` | `R3_COMPLETE` |
| `R3_COMPLETE` | R3 findings recorded | `R3_IN_PROGRESS` | `R4_IN_PROGRESS` |
| `R4_IN_PROGRESS` | Running 08_R4_HANDOFF.md | `R3_COMPLETE` | `R4_COMPLETE` |
| `R4_COMPLETE` | R4 findings recorded | `R4_IN_PROGRESS` | `R5_IN_PROGRESS` |
| `R5_IN_PROGRESS` | Running 09_R5_ADJUDICATION.md | `R4_COMPLETE` | `R5_COMPLETE` |
| `R5_COMPLETE` | R5 verdict issued | `R5_IN_PROGRESS` | `GATE_VERDICT_ISSUED` |

### Gate Verdict states (Step 10)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `GATE_VERDICT_ISSUED` | Verdict mapped from R5 + enforcement audit | `R5_COMPLETE` | `GATE_PASS_FOR_HANDOFF`, `GATE_FAIL_AUTOFIX_REQUIRED`, `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` |
| `GATE_PASS_FOR_HANDOFF` | R5 = READY_FOR_REVIEW; enforcement = PASS or N/A | `GATE_VERDICT_ISSUED` | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` |
| `GATE_FAIL_AUTOFIX_REQUIRED` | Fixable blockers remain | `GATE_VERDICT_ISSUED` | `FIX_CYCLE_IN_PROGRESS`, `MAX_CYCLES_REACHED` |
| `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` | Human-blocked blockers remain | `GATE_VERDICT_ISSUED` | `BLOCKED_HANDOFF_COMPLETE` |

### Fix Cycle states (Step 11)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `FIX_CYCLE_IN_PROGRESS` | Applying AUTOFIX_REQUIRED fixes | `GATE_FAIL_AUTOFIX_REQUIRED` | `FIX_CYCLE_COMPLETE`, `MAX_CYCLES_REACHED` |
| `FIX_CYCLE_COMPLETE` | All AUTOFIX blockers addressed; artifacts regenerated | `FIX_CYCLE_IN_PROGRESS` | `EVIDENCE_ADEQUACY_IN_PROGRESS` (new cycle) |
| `MAX_CYCLES_REACHED` | Cycle 5 completed without PASS | `GATE_FAIL_AUTOFIX_REQUIRED`, `FIX_CYCLE_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |

### Package and Handoff Audit states (Steps 15–16)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | Running 15_FINAL_PACKAGE_AUDIT.md | `GATE_PASS_FOR_HANDOFF` | `FINAL_PACKAGE_AUDIT_PASS`, `FINAL_PACKAGE_AUDIT_FAIL` |
| `FINAL_PACKAGE_AUDIT_PASS` | All package contents verified present and correct | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` |
| `FINAL_PACKAGE_AUDIT_FAIL` | Package missing claimed contents or contains contradictions | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` (re-enter fix with cycle counter preserved) |
| `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` | Running 16_CANONICAL_HANDOFF_AUDIT.md | `FINAL_PACKAGE_AUDIT_PASS` | `CANONICAL_HANDOFF_AUDIT_PASS`, `CANONICAL_HANDOFF_AUDIT_FAIL` |
| `CANONICAL_HANDOFF_AUDIT_PASS` | Exactly one READY handoff; no contradictions; no stale files | `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` | `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` |
| `CANONICAL_HANDOFF_AUDIT_FAIL` | Handoff contradictions detected (e.g., PENDING vs PASS) | `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` (re-enter fix with cycle counter preserved) |

### Final Packet Auditor state (Step 37 — Gate 5.3)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `FINAL_PACKET_AUDITOR` | Independent context-light packet auditor (Gate 5.3) | `CANONICAL_HANDOFF_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` | `PASS_HANDOFF_COMPLETE` (PASS), `FIX_CYCLE_IN_PROGRESS` (FAIL), `BLOCKED_HANDOFF_COMPLETE` / `GATE_BLOCKED_REQUIRES_HUMAN` (HUMAN_DECISION_REQUIRED) |

### Execution Context Audit states (Step 17)

| State | Description | Entry from | Exits to |
|---|---|---|---|
| `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` | No execution-context claims in any document | `CANONICAL_HANDOFF_AUDIT_PASS` | `PASS_HANDOFF_COMPLETE` |
| `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` | Running 17_EXECUTION_CONTEXT_AUDIT.md | `CANONICAL_HANDOFF_AUDIT_PASS` | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_FAIL` |
| `EXECUTION_CONTEXT_AUDIT_PASS` | All context-sensitive claims have branch/HEAD/cwd proof | `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` | `PASS_HANDOFF_COMPLETE` |
| `EXECUTION_CONTEXT_AUDIT_FAIL` | One or more claims lack required context proof | `EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS`, `BLOCKED_HANDOFF_COMPLETE` |

### Gate 4.1 Additional States (Steps 19–36)

These states are required for GATE_STANDARD and GATE_FULL profiles. For GATE_LITE, produce `STATE_NAME_NOT_APPLICABLE.md` for each that does not apply.

#### Prompt Contract Review (Step 19)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` | Running 19_PROMPT_CONTRACT_REVIEW.md | `GATE_PROFILE_SELECTION_COMPLETE` (D2-hot/D3/D4) or `EVIDENCE_ADEQUACY_IN_PROGRESS` | `PROMPT_CONTRACT_PASS`, `PROMPT_CONTRACT_NEEDS_REVISION`, `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY` |
| `PROMPT_CONTRACT_PASS` | All contract checks pass | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` | `EVIDENCE_ADEQUACY_IN_PROGRESS` |
| `PROMPT_CONTRACT_NEEDS_REVISION` | Contract issues identified but fixable | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` | (return to operator for revision) |
| `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY` | Contract cannot proceed due to ambiguity | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS` | `GATE_PROFILE_SELECTION_BLOCKED` |

#### Production Caller / Active Path Audit (Step 20)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `PRODUCTION_CALLER_AUDIT_IN_PROGRESS` | Running 20_PRODUCTION_CALLER_ACTIVE_PATH_AUDIT.md | `R5_COMPLETE` or `PANEL_ENTRY_VERIFIED` | `PRODUCTION_CALLER_AUDIT_PASS`, `PRODUCTION_CALLER_AUDIT_FAIL` |
| `PRODUCTION_CALLER_AUDIT_PASS` | All live-behavior claims have production caller proof | `PRODUCTION_CALLER_AUDIT_IN_PROGRESS` | `GATE_VERDICT_ISSUED` |
| `PRODUCTION_CALLER_AUDIT_FAIL` | Live-behavior claims lack production caller proof | `PRODUCTION_CALLER_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Consumer API Proof Audit (Step 21)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` | Running 21_CONSUMER_API_PROOF_AUDIT.md | `R2_COMPLETE` | `CONSUMER_API_PROOF_AUDIT_PASS`, `CONSUMER_API_PROOF_AUDIT_FAIL` |
| `CONSUMER_API_PROOF_AUDIT_PASS` | Tests assert through consumer API | `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` | `R3_IN_PROGRESS` |
| `CONSUMER_API_PROOF_AUDIT_FAIL` | Tests bypass consumer API; raw inspection only | `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Warning Output Contradiction Audit (Step 22)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `WARNING_OUTPUT_AUDIT_IN_PROGRESS` | Running 22_WARNING_OUTPUT_AUDIT.md | `R2_COMPLETE` | `WARNING_OUTPUT_AUDIT_PASS`, `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` |
| `WARNING_OUTPUT_AUDIT_PASS` | No warnings contradict success claims | `WARNING_OUTPUT_AUDIT_IN_PROGRESS` | continue in reviewer sequence |
| `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` | Warning contradicts claimed behavior | `WARNING_OUTPUT_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Required Test Set Exactness (Step 23)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` | Running 23_REQUIRED_TEST_SET_EXACTNESS.md | `PANEL_ENTRY_VERIFIED` | `REQUIRED_TEST_SET_EXACTNESS_PASS`, `REQUIRED_TEST_SET_EXACTNESS_FAIL` |
| `REQUIRED_TEST_SET_EXACTNESS_PASS` | All required tests run and captured | `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` | continue |
| `REQUIRED_TEST_SET_EXACTNESS_FAIL` | Required test set incomplete or wrong | `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Migration Runner Proof (Step 24)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `MIGRATION_RUNNER_PROOF_IN_PROGRESS` | Running 24_MIGRATION_RUNNER_PROOF.md | `EVIDENCE_ADEQUACY_IN_PROGRESS` | `MIGRATION_RUNNER_PROVEN`, `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN`, `MIGRATION_BLOCKED` |
| `MIGRATION_RUNNER_PROVEN` | Migration applied via real runner | `MIGRATION_RUNNER_PROOF_IN_PROGRESS` | continue |
| `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN` | SQL valid but runner not proven | `MIGRATION_RUNNER_PROOF_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |
| `MIGRATION_BLOCKED` | Migration cannot be applied within scope | `MIGRATION_RUNNER_PROOF_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |

#### Implementer Prompt Lint (Step 25)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` | Running 25_IMPLEMENTER_PROMPT_LINT.md | `GATE_PROFILE_SELECTION_COMPLETE` | `IMPLEMENTER_PROMPT_LINT_PASS`, `IMPLEMENTER_PROMPT_LINT_FAIL` |
| `IMPLEMENTER_PROMPT_LINT_PASS` | All prompts pass lint | `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` | continue |
| `IMPLEMENTER_PROMPT_LINT_FAIL` | Prompts contain invalid snippets or overclaims | `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` | (return to operator) |

#### Stranded Helper / Unused Export Scan (Step 26)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `STRANDED_HELPER_AUDIT_IN_PROGRESS` | Running 26_STRANDED_HELPER_UNUSED_EXPORT_AUDIT.md | `R3_COMPLETE` | `STRANDED_HELPER_AUDIT_PASS`, `STRANDED_HELPER_AUDIT_FAIL` |
| `STRANDED_HELPER_AUDIT_PASS` | All new symbols have production callers | `STRANDED_HELPER_AUDIT_IN_PROGRESS` | `R4_IN_PROGRESS` |
| `STRANDED_HELPER_AUDIT_FAIL` | New symbols used only by tests or not at all | `STRANDED_HELPER_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Dirty Worktree Recurrence Audit (Step 27)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` | Running 27_DIRTY_WORKTREE_RECURRENCE_AUDIT.md | `EVIDENCE_CONSISTENCY_IN_PROGRESS` | `DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS`, `DIRTY_WORKTREE_RECURRENCE_BLOCKER` |
| `DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS` | No recurrent dirty paths | `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` | continue |
| `DIRTY_WORKTREE_RECURRENCE_BLOCKER` | Recurrent dirty path without hygiene issue | `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Work Allocation / Hot File Conflict Audit (Step 28)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `WORK_ALLOCATION_AUDIT_IN_PROGRESS` | Running 28_WORK_ALLOCATION_AUDIT.md | `GATE_PROFILE_SELECTION_COMPLETE` | `WORK_ALLOCATION_CLEAR`, `WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE`, `WORK_ALLOCATION_BLOCKED_BY_CONFLICT`, `WORK_ALLOCATION_NEEDS_HUMAN` |
| `WORK_ALLOCATION_CLEAR` | No conflicts; work can proceed | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` | continue |
| `WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE` | Work must proceed in task worktree | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` | continue (in worktree) |
| `WORK_ALLOCATION_BLOCKED_BY_CONFLICT` | Active conflict cannot be resolved | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |
| `WORK_ALLOCATION_NEEDS_HUMAN` | Conflict resolution requires human decision | `WORK_ALLOCATION_AUDIT_IN_PROGRESS` | (return to operator) |

#### Export Channel Audit (Step 29)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `EXPORT_CHANNEL_AUDIT_IN_PROGRESS` | Running 29_EXPORT_CHANNEL_AUDIT.md | `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | `EXPORT_CHANNEL_AUDIT_PASS`, `EXPORT_CHANNEL_AUDIT_FAIL` |
| `EXPORT_CHANNEL_AUDIT_PASS` | All required files included in export | `EXPORT_CHANNEL_AUDIT_IN_PROGRESS` | continue |
| `EXPORT_CHANNEL_AUDIT_FAIL` | Files exist on host but missing from export | `EXPORT_CHANNEL_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Diff Base / Scope Audit (Step 30)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` | Running 30_DIFF_BASE_SCOPE_AUDIT.md | `EVIDENCE_CONSISTENCY_IN_PROGRESS` | `DIFF_BASE_SCOPE_AUDIT_PASS`, `DIFF_BASE_SCOPE_AUDIT_FAIL` |
| `DIFF_BASE_SCOPE_AUDIT_PASS` | Diff base/head correct; no out-of-scope noise | `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` | continue |
| `DIFF_BASE_SCOPE_AUDIT_FAIL` | Stale or out-of-scope diff | `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Flake / Timeout / Load Sensitivity Audit (Step 31)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` | Running 31_FLAKE_TIMEOUT_LOAD_AUDIT.md | `TEST_PLAN_COMPLETE` | `TEST_STABILITY_OK`, `TEST_STABILITY_WARNING_FOLLOWUP`, `TEST_STABILITY_BLOCKING` |
| `TEST_STABILITY_OK` | Tests are stable | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` | continue |
| `TEST_STABILITY_WARNING_FOLLOWUP` | Tests have timing sensitivity — follow-up required | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` | continue (with warning) |
| `TEST_STABILITY_BLOCKING` | Test instability blocks handoff | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Concurrency Assumptions Audit (Step 32)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` | Running 32_CONCURRENCY_ASSUMPTIONS_AUDIT.md | `R2_COMPLETE` | `CONCURRENCY_ASSUMPTIONS_AUDIT_PASS`, `CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL` |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_PASS` | Concurrency assumptions documented and safe | `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` | continue |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL` | Undocumented race conditions or incorrect guarantees | `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` | `FIX_CYCLE_IN_PROGRESS` |

#### Downstream Consumer Readiness Audit (Step 33)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` | Running 33_DOWNSTREAM_CONSUMER_READINESS_AUDIT.md | `R4_COMPLETE` | `DOWNSTREAM_READY`, `DOWNSTREAM_READY_WITH_CAVEAT`, `DOWNSTREAM_NOT_READY` |
| `DOWNSTREAM_READY` | Next phase can start | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` | continue |
| `DOWNSTREAM_READY_WITH_CAVEAT` | Next phase can start with stated caveats | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` | continue |
| `DOWNSTREAM_NOT_READY` | Next phase must not start | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS` | `BLOCKED_HANDOFF_COMPLETE` |

#### Next Prompt Decision (Step 34)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `NEXT_PROMPT_DECISION_IN_PROGRESS` | Running 34_NEXT_PROMPT_DECISION.md | `R5_COMPLETE` | `NEXT_PROMPT_DECISION_COMPLETE` |
| `NEXT_PROMPT_DECISION_COMPLETE` | Next prompt decision artifact written | `NEXT_PROMPT_DECISION_IN_PROGRESS` | `GATE_VERDICT_ISSUED` |

#### CTO / Operator Insight Review (Step 35)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `CTO_OPERATOR_INSIGHT_REVIEW_IN_PROGRESS` | Running 35_CTO_OPERATOR_INSIGHT_REVIEW.md | `R5_COMPLETE` | `CTO_OPERATOR_INSIGHT_REVIEW_COMPLETE` |
| `CTO_OPERATOR_INSIGHT_REVIEW_COMPLETE` | CTO/operator insight recorded | `CTO_OPERATOR_INSIGHT_REVIEW_IN_PROGRESS` | `NEXT_PROMPT_DECISION_IN_PROGRESS` |

#### Gate Effectiveness Log (Step 36)
| State | Description | Entry from | Exits to |
|---|---|---|---|
| `GATE_EFFECTIVENESS_LOG_IN_PROGRESS` | Running 36_GATE_EFFECTIVENESS_LOG.md | `PASS_HANDOFF_COMPLETE` or `BLOCKED_HANDOFF_COMPLETE` | `GATE_EFFECTIVENESS_LOG_COMPLETE` |
| `GATE_EFFECTIVENESS_LOG_COMPLETE` | Effectiveness log written | `GATE_EFFECTIVENESS_LOG_IN_PROGRESS` | (done) |

---

### Terminal states

| State | Description | Entry from |
|---|---|---|
| `GATE_LITE_PASS_HANDOFF_COMPLETE` | Final PASS for GATE_LITE profile | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` (when profile = GATE_LITE) |
| `GATE_STANDARD_PASS_HANDOFF_COMPLETE` | Final PASS for GATE_STANDARD profile | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` (when profile = GATE_STANDARD) |
| `GATE_FULL_PASS_HANDOFF_COMPLETE` | Final PASS for GATE_FULL or GATE_FULL_PLUS_DOMAIN_ADDENDUM profile | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` (when profile = GATE_FULL or GATE_FULL_PLUS) |
| `PASS_HANDOFF_COMPLETE` | Legacy terminal state — preserved for backward compatibility; prefer profile-specific terminal states | `EXECUTION_CONTEXT_AUDIT_PASS`, `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` |
| `BLOCKED_HANDOFF_COMPLETE` | Blocked handoff returned to user with required content | `EVIDENCE_BLOCKED_REQUIRES_HUMAN`, `EVIDENCE_CONSISTENCY_BLOCKED`, `ENFORCEMENT_AUDIT_FAIL_BLOCKED`, `GATE_FAIL_BLOCKED_REQUIRES_HUMAN`, `MAX_CYCLES_REACHED`, `EXECUTION_CONTEXT_AUDIT_FAIL` (when HUMAN_BLOCKED), `DOWNSTREAM_NOT_READY`, `WORK_ALLOCATION_BLOCKED_BY_CONFLICT`, `MIGRATION_BLOCKED` |
| `GATE_BLOCKED_REQUIRES_HUMAN` | Gate cannot proceed; human decision required | `GATE_PROFILE_SELECTION_BLOCKED`, `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY`, `WORK_ALLOCATION_NEEDS_HUMAN` |
| `GATE_PROFILE_SELECTION_BLOCKED` | Profile selection halted; operator must clarify | `GATE_PROFILE_SELECTION_IN_PROGRESS` |

---

## State transition invariants

These invariants must hold at every state write. Any violation blocks the transition.

1. **No skipping states.** The new state must be a valid exit from the current state per the table above.
2. **Cycle counter constraint.** `cycle_count` may only be incremented when entering `EVIDENCE_ADEQUACY_IN_PROGRESS` from `FIX_CYCLE_COMPLETE`.
3. **R-states must be sequential.** R2 cannot enter until R1 is COMPLETE. R5 cannot enter until R4 is COMPLETE.
4. **No PASS_FOR_HANDOFF from R5 if enforcement audit recorded FAIL.** `GATE_PASS_FOR_HANDOFF` requires `enforcement_audit_result` in the current cycle to be `PASS` or `NOT_APPLICABLE`.
5. **Steps 15–17 must precede PASS_HANDOFF_COMPLETE.** `PASS_HANDOFF_COMPLETE` requires `FINAL_PACKAGE_AUDIT_PASS`, `CANONICAL_HANDOFF_AUDIT_PASS`, and either `EXECUTION_CONTEXT_AUDIT_PASS` or `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` in state history.
5a. **(Gate 5.3) FINAL_PACKET_AUDITOR must precede PASS_HANDOFF_COMPLETE.** `PASS_HANDOFF_COMPLETE` (and every profile-specific terminal PASS) additionally requires `final_packet_auditor_verdict: PASS` recorded in CURRENT_STATE.yaml. FAIL or HUMAN_DECISION_REQUIRED blocks PASS.
6. **BLOCKED_HANDOFF.md must be labeled HISTORICAL.** If BLOCKED_HANDOFF.md exists in the package and the current state is not `BLOCKED_HANDOFF_COMPLETE`, it must have a banner reading `## STATUS: HISTORICAL — NOT THE FINAL HANDOFF`.

---

## How CURRENT_STATE.yaml works

`reports/<task_area>/CURRENT_STATE.yaml` is the single active state file. There is exactly one per gate run.

- Created at: `CYCLE_TRACKER_INITIALIZED`
- Updated at: every state transition
- Read at: entry to every gate step
- Terminal states write `current_state` and set `gate_completed: true`

Template: `STATE_FILE_TEMPLATE.yaml`
Schema: `STATE_SCHEMA.md`
