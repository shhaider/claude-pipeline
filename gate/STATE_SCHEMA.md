# CURRENT_STATE.yaml — Schema Reference

Every gate run maintains exactly one `reports/<task_area>/CURRENT_STATE.yaml` file.
This file is the single source of truth for the current state of the gate run.

## Top-level fields

```yaml
# Identity
task_id: string                    # Unique task identifier (e.g., "ORCH-FIXES-001")
task_area: string                  # Directory name under reports/ (e.g., "agentos-ng-governance-fixes")
gate_run_id: string                # Unique run ID (e.g., "gate-2026-04-30T14:22:00")
gate_started_at: ISO-8601          # When the gate was first entered
last_updated_at: ISO-8601          # Timestamp of most recent state write

# Current state (one of the named states in STATE_MACHINE.md)
current_state: STATE_NAME

# Gate 4.1 — Profile selection (written at GATE_PROFILE_SELECTION_COMPLETE)
gate_profile: GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS_DOMAIN_ADDENDUM | null
risk_tier: D0 | D1 | D2 | D2-hot | D2_HOT | D3 | D4 | null
task_kind: docs | tiny_test | normal_impl | hot_file | migration | runtime_state | merge_verification | release_verification | production_wiring | provider_model_routing | gate_change | prompt_authoring | evidence_package | null
domain_addenda: list[string] | null          # List of addendum names, e.g. ["model_id_validation"]
profile_override_required: boolean | null    # true if operator specified weaker profile than selector recommends
profile_selection_rationale: string | null   # One sentence explaining the selection

# Cycle tracking
cycle_count: integer               # Current cycle number (1–5)
max_cycles: 5                      # Always 5
gate_completed: boolean            # true only when in a terminal state

# Artifact paths (set at CYCLE_TRACKER_INITIALIZED, do not change)
claims_ledger_path: string         # e.g., reports/<task_area>/CLAIMS_LEDGER.yaml
evidence_ledger_path: string       # e.g., reports/<task_area>/EVIDENCE_LEDGER.yaml
package_manifest_path: string      # e.g., reports/<task_area>/PACKAGE_MANIFEST.md
stale_file_register_path: string   # e.g., reports/<task_area>/STALE_FILE_REGISTER.yaml
cycle_tracker_path: string         # e.g., reports/<task_area>/CYCLE_TRACKER.md

# State history (append-only log of all states entered)
state_history:
  - state: STATE_NAME
    entered_at: ISO-8601
    exited_at: ISO-8601 | null      # null if currently in this state

# Per-cycle results
cycles:
  <cycle_number>:                  # integer key: 1, 2, 3, 4, 5
    started_at: ISO-8601
    completed_at: ISO-8601 | null

    # Evidence Adequacy (Step 01)
    evidence_adequacy_decision: EVIDENCE_ALREADY_ADEQUATE | EVIDENCE_UPGRADE_REQUIRED | EVIDENCE_BLOCKED_REQUIRES_HUMAN | null

    # Evidence Consistency (Step 03)
    consistency_result: PASS | BLOCKING_CONTRADICTIONS_FOUND | null
    consistency_contradictions_found: integer | null

    # Enforcement Audit (Step 14)
    enforcement_audit_applicable: boolean | null
    enforcement_audit_result: PASS | FAIL_AUTOFIX_REQUIRED | FAIL_BLOCKED_REQUIRES_HUMAN | NOT_APPLICABLE | null

    # Panel (Steps 05–09) — null until that reviewer completes
    r1_blocking: integer | null
    r1_nonblocking: integer | null
    r2_blocking: integer | null
    r2_nonblocking: integer | null
    r3_blocking: integer | null
    r3_nonblocking: integer | null
    r4_blocking: integer | null
    r4_nonblocking: integer | null

    # R5 verdict (Step 09)
    r5_verdict: READY_FOR_REVIEW | NEEDS_CORRECTION | BLOCKED | STOP_AND_REDESIGN | null

    # Gate verdict (Step 10)
    gate_verdict: PASS_FOR_HANDOFF | FAIL_AUTOFIX_REQUIRED | FAIL_BLOCKED_REQUIRES_HUMAN | null
    blockers_autofix: integer | null
    blockers_human_blocked: integer | null

    # Fixes applied (Step 11)
    fixes_applied: list[string] | null   # One entry per AUTOFIX_REQUIRED blocker addressed

    # Execution context audit (Step 17)
    execution_context_audit_applicable: boolean | null
    execution_context_audit_result: PASS | FAIL_AUTOFIX_REQUIRED | FAIL_BLOCKED_REQUIRES_HUMAN | NOT_APPLICABLE | null

    # Gate 4.1 additional audit results (null when not applicable for selected profile)
    prompt_contract_review_result: PROMPT_CONTRACT_PASS | PROMPT_CONTRACT_NEEDS_REVISION | PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY | NOT_APPLICABLE | null
    production_caller_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    consumer_api_proof_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    warning_output_audit_result: PASS | BLOCKING_FOUND | NOT_APPLICABLE | null
    required_test_set_exactness_result: PASS | FAIL | NOT_APPLICABLE | null
    manifest_finalization_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    migration_runner_proof_result: MIGRATION_RUNNER_PROVEN | SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN | MIGRATION_BLOCKED | NOT_APPLICABLE | null
    implementer_prompt_lint_result: PASS | FAIL | NOT_APPLICABLE | null
    stranded_helper_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    dirty_worktree_recurrence_result: PASS | BLOCKER | NOT_APPLICABLE | null
    work_allocation_audit_result: WORK_ALLOCATION_CLEAR | WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE | WORK_ALLOCATION_BLOCKED_BY_CONFLICT | WORK_ALLOCATION_NEEDS_HUMAN | NOT_APPLICABLE | null
    export_channel_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    diff_base_scope_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    flake_timeout_audit_result: TEST_STABILITY_OK | TEST_STABILITY_WARNING_FOLLOWUP | TEST_STABILITY_BLOCKING | NOT_APPLICABLE | null
    concurrency_assumptions_audit_result: PASS | FAIL | NOT_APPLICABLE | null
    downstream_consumer_readiness_result: DOWNSTREAM_READY | DOWNSTREAM_READY_WITH_CAVEAT | DOWNSTREAM_NOT_READY | NOT_APPLICABLE | null
    next_prompt_decision_result: COMPLETE | NOT_APPLICABLE | null
    cto_operator_insight_review_result: COMPLETE | NOT_APPLICABLE | null
    gate_effectiveness_log_result: COMPLETE | NOT_APPLICABLE | null

    # Gate 4.1 final outcome label (overclaim taxonomy — P22)
    final_outcome_label: LIVE_BEHAVIOR_FIXED | INFRASTRUCTURE_READY_NOT_WIRED | TEST_HELPER_ONLY | DOCS_ONLY | MERGE_VERIFIED | MERGE_NOT_VERIFIED | PREPLANNING_READY | PREPLANNING_BLOCKED | PACKAGE_READY_FOR_REVIEW | PACKAGE_BLOCKED | null

# Package and handoff audit results
final_package_audit_result: PASS | FAIL | null
canonical_handoff_audit_result: PASS | FAIL | null
execution_context_audit_result: PASS | FAIL | NOT_APPLICABLE | null

# Gate 5.3 — Final Packet Auditor
final_packet_auditor_verdict: PASS | FAIL | HUMAN_DECISION_REQUIRED | null
rerun_from: BEGINNING | TARGETED_STATE:<name> | HUMAN_DECISION | null

# Terminal state fields
final_gate_verdict: PASS_FOR_HANDOFF | FAIL_BLOCKED_REQUIRES_HUMAN | null
final_r5_verdict: string | null
handoff_type: PASS | BLOCKED | null
handoff_completed_at: ISO-8601 | null
remaining_human_blocked_blockers: list[string] | null
```

---

## Gate 4.1 — Overclaim Taxonomy

The `final_outcome_label` field in per-cycle results must be set to one of the following at handoff time. It is **not** sufficient to write "READY_FOR_HANDOFF" — the label must specify what kind of ready.

| Label | Meaning |
|---|---|
| `LIVE_BEHAVIOR_FIXED` | A production system behavior is repaired and a production caller is proven |
| `INFRASTRUCTURE_READY_NOT_WIRED` | Code is correct and tested, but no production caller exists yet |
| `TEST_HELPER_ONLY` | New code is used only by test infrastructure, not production code |
| `DOCS_ONLY` | No code changed; only documentation, comments, or non-executable files |
| `MERGE_VERIFIED` | Branch has been merged and merge proof (git log) is present |
| `MERGE_NOT_VERIFIED` | Branch was submitted for merge but merge proof is not in this package |
| `PREPLANNING_READY` | A preplanning package is complete and ready for an implementer |
| `PREPLANNING_BLOCKED` | A preplanning package is incomplete; human decision required |
| `PACKAGE_READY_FOR_REVIEW` | A work package is ready for human or AI review |
| `PACKAGE_BLOCKED` | A work package cannot proceed without human resolution |

**Hard rule:** The `final_outcome_label` must match the actual state of the work. If no production caller is proven, the label cannot be `LIVE_BEHAVIOR_FIXED`. If tests use only raw DB inspection, the label cannot include any claim of consumer-API-level proof.

---

## Validation rules

The following must be true every time `CURRENT_STATE.yaml` is written:

1. `current_state` is one of the named states in `STATE_MACHINE.md`
2. The transition from the previous state to `current_state` is allowed per `TRANSITION_RULES.md`
3. `cycle_count` is between 1 and 5
4. `cycle_count` matches the highest key in `cycles`
5. `state_history` is append-only — no prior entries may be modified or removed
6. If `gate_completed: true`, then `current_state` is a terminal state
7. If `current_state` is `PASS_HANDOFF_COMPLETE`, then `final_package_audit_result: PASS`, `canonical_handoff_audit_result: PASS`, and `execution_context_audit_result: PASS or NOT_APPLICABLE` must all be recorded in this file
8. If `current_state` is `GATE_PASS_FOR_HANDOFF` or later, the current cycle's `enforcement_audit_result` must be `PASS` or `NOT_APPLICABLE`
9. If `gate_profile` is set (not null), `current_state` must not be a terminal PASS state unless all required states for that profile have been recorded in `state_history` (Gate 4.1)
10. If `current_state` is `GATE_LITE_PASS_HANDOFF_COMPLETE`, then `gate_profile` must be `GATE_LITE`
11. If `current_state` is `GATE_STANDARD_PASS_HANDOFF_COMPLETE`, then `gate_profile` must be `GATE_STANDARD`
12. If `current_state` is `GATE_FULL_PASS_HANDOFF_COMPLETE`, then `gate_profile` must be `GATE_FULL` or `GATE_FULL_PLUS_DOMAIN_ADDENDUM`
13. `final_outcome_label` must be set (not null) before any terminal PASS state is written (Gate 4.1)
14. (Gate 5.3) If `current_state` is `PASS_HANDOFF_COMPLETE` (or any profile-specific terminal PASS), `final_packet_auditor_verdict` must be `PASS` and `rerun_from` must be set. Verdict `FAIL` or `HUMAN_DECISION_REQUIRED`, or any null value, blocks terminal PASS.

## Gate 5.3 — Valid state names added

- `FINAL_PACKET_AUDITOR` is a valid `current_state` value, exited via PASS / FAIL / HUMAN_DECISION_REQUIRED.

---

## Write protocol

When writing CURRENT_STATE.yaml:

1. Read the current file
2. Append the completed state to `state_history` (set `exited_at`)
3. Set `current_state` to the new state
4. Append the new state to `state_history` with `entered_at` = now, `exited_at` = null
5. Update `last_updated_at`
6. Write any per-cycle fields that are now known
7. If entering a terminal state, set `gate_completed: true`
