# Gate 4.1 — Changed Files Manifest

**Date:** 2026-05-01

---

## Files created (new)

| File | Purpose | P-task |
|---|---|---|
| `gate/GATE_PROFILES.md` | Four profile definitions with required states | P01 |
| `gate/GATE_PROFILE_SELECTOR.md` | Risk tier definitions, hot files list, escalation triggers | P01 |
| `gate/18_GATE_PROFILE_SELECTION.md` | Step 18 — Profile selection (first step of every run) | P02 |
| `gate/GATE_PROFILE_SELECTION_TEMPLATE.md` | Template for GATE_PROFILE_SELECTION.md | P02 |
| `gate/19_PROMPT_CONTRACT_REVIEW.md` | Step 19 — Prompt contract review | P03 |
| `gate/PROMPT_CONTRACT_REVIEW_TEMPLATE.md` | Template for prompt contract review | P03 |
| `gate/ARTIFACT_LIFECYCLE_TIMING_AUDIT_TEMPLATE.md` | Template for artifact lifecycle timing audit | P04 |
| `gate/20_PRODUCTION_CALLER_ACTIVE_PATH_AUDIT.md` | Step 20 — Production caller audit | P05 |
| `gate/PRODUCTION_CALLER_ACTIVE_PATH_AUDIT_TEMPLATE.md` | Template for production caller audit | P05 |
| `gate/21_CONSUMER_API_PROOF_AUDIT.md` | Step 21 — Consumer API proof audit | P06 |
| `gate/CONSUMER_API_PROOF_AUDIT_TEMPLATE.md` | Template for consumer API audit | P06 |
| `gate/22_WARNING_OUTPUT_AUDIT.md` | Step 22 — Warning output contradiction audit | P07 |
| `gate/WARNING_OUTPUT_AUDIT_TEMPLATE.md` | Template for warning output audit | P07 |
| `gate/23_REQUIRED_TEST_SET_EXACTNESS.md` | Step 23 — Required test set exactness | P08 |
| `gate/REQUIRED_TEST_SET_EXACTNESS_TEMPLATE.md` | Template for test set exactness | P08 |
| `gate/MANIFEST_FINALIZATION_AUDIT_TEMPLATE.md` | Template for manifest stat/hash check | P09 |
| `gate/24_MIGRATION_RUNNER_PROOF.md` | Step 24 — Migration runner proof | P10 |
| `gate/MIGRATION_RUNNER_PROOF_TEMPLATE.md` | Template for migration runner proof | P10 |
| `gate/25_IMPLEMENTER_PROMPT_LINT.md` | Step 25 — Implementer prompt lint | P11 |
| `gate/IMPLEMENTER_PROMPT_LINT_TEMPLATE.md` | Template for prompt lint | P11 |
| `gate/26_STRANDED_HELPER_UNUSED_EXPORT_AUDIT.md` | Step 26 — Stranded helper audit | P12 |
| `gate/STRANDED_HELPER_UNUSED_EXPORT_AUDIT_TEMPLATE.md` | Template for stranded helper audit | P12 |
| `gate/27_DIRTY_WORKTREE_RECURRENCE_AUDIT.md` | Step 27 — Dirty worktree recurrence audit | P13 |
| `gate/DIRTY_WORKTREE_RECURRENCE_TEMPLATE.md` | Template for dirty worktree recurrence register | P13 |
| `gate/28_WORK_ALLOCATION_AUDIT.md` | Step 28 — Work allocation / hot file conflict audit | P14 |
| `gate/WORK_ALLOCATION_AUDIT_TEMPLATE.md` | Template for work allocation audit | P14 |
| `gate/29_EXPORT_CHANNEL_AUDIT.md` | Step 29 — Export channel audit | P15 |
| `gate/EXPORT_CHANNEL_AUDIT_TEMPLATE.md` | Template for export channel audit | P15 |
| `gate/30_DIFF_BASE_SCOPE_AUDIT.md` | Step 30 — Diff base / scope audit | P16 |
| `gate/DIFF_BASE_SCOPE_AUDIT_TEMPLATE.md` | Template for diff base scope audit | P16 |
| `gate/31_FLAKE_TIMEOUT_LOAD_AUDIT.md` | Step 31 — Flake / timeout / load sensitivity audit | P17 |
| `gate/FLAKE_TIMEOUT_LOAD_AUDIT_TEMPLATE.md` | Template for flake/timeout audit | P17 |
| `gate/32_CONCURRENCY_ASSUMPTIONS_AUDIT.md` | Step 32 — Concurrency assumptions audit | P18 |
| `gate/CONCURRENCY_ASSUMPTIONS_AUDIT_TEMPLATE.md` | Template for concurrency audit | P18 |
| `gate/33_DOWNSTREAM_CONSUMER_READINESS_AUDIT.md` | Step 33 — Downstream consumer readiness | P19 |
| `gate/DOWNSTREAM_CONSUMER_READINESS_TEMPLATE.md` | Template for downstream readiness | P19 |
| `gate/34_NEXT_PROMPT_DECISION.md` | Step 34 — Next prompt decision | P20 |
| `gate/NEXT_PROMPT_DECISION_TEMPLATE.md` | Template for next prompt decision | P20 |
| `gate/35_CTO_OPERATOR_INSIGHT_REVIEW.md` | Step 35 — CTO / operator insight review | P21 |
| `gate/CTO_OPERATOR_INSIGHT_REVIEW_TEMPLATE.md` | Template for CTO insight review | P21 |
| `gate/36_GATE_EFFECTIVENESS_LOG.md` | Step 36 — Gate effectiveness log | P23 |
| `gate/GATE_EFFECTIVENESS_LOG_TEMPLATE.md` | Template for effectiveness log | P23 |
| `gate/PROOF_FILE_REQUIREMENTS.md` | Rules for required proof files | P24 |
| `gate/REQUIRED_PROOF_FILES_BY_PROFILE.yaml` | Machine-readable proof file list per profile | P24 |
| `gate/GATE_4_1_USAGE_GUIDE.md` | Operator/agent usage guide | P28 |
| `gate/reports/gate-4-1-upgrade/GATE_4_1_BASELINE.md` | Pre-upgrade baseline | P00 |
| `gate/reports/gate-4-1-upgrade/GATE_4_1_CHANGED_FILES.md` | This file | P29 |
| `gate/reports/gate-4-1-upgrade/GATE_4_1_HANDOFF.md` | Final handoff | P29 |
| `gate/reports/gate-4-1-upgrade/GATE_4_1_OPEN_QUESTIONS.md` | Open questions | P29 |
| `gate/reports/gate-4-1-upgrade/GATE_4_1_USAGE_RECOMMENDATION.md` | Usage recommendation | P29 |

**New fixture specs:**

| Fixture | Failure mode | P-task |
|---|---|---|
| `tests/gate_state_machine/fixtures/wrong_gate_profile_too_weak/FIXTURE_SPEC.md` | Gate profile too weak for hot file | P27 |
| `tests/gate_state_machine/fixtures/production_caller_overclaim/FIXTURE_SPEC.md` | Production caller overclaim | P27 |
| `tests/gate_state_machine/fixtures/consumer_api_bypass/FIXTURE_SPEC.md` | Consumer API bypass | P27 |
| `tests/gate_state_machine/fixtures/warning_contradicts_success/FIXTURE_SPEC.md` | Warning contradicts success | P27 |
| `tests/gate_state_machine/fixtures/wrong_required_test_set/FIXTURE_SPEC.md` | Wrong required test set | P27 |
| `tests/gate_state_machine/fixtures/manifest_self_size_stale/FIXTURE_SPEC.md` | Manifest self-size stale | P27 |
| `tests/gate_state_machine/fixtures/migration_sql_only_runner_not_proven/FIXTURE_SPEC.md` | Migration SQL only, runner not proven | P27 |
| `tests/gate_state_machine/fixtures/prompt_invalid_js_snippet/FIXTURE_SPEC.md` | Prompt invalid JS snippet | P27 |
| `tests/gate_state_machine/fixtures/helper_test_only_claiming_production/FIXTURE_SPEC.md` | Helper test-only claiming production | P27 |
| `tests/gate_state_machine/fixtures/file_exists_on_host_missing_from_export/FIXTURE_SPEC.md` | File exists on host but missing from export | P27 |

---

## Files modified (existing, extended — not replaced)

| File | What was added | P-task |
|---|---|---|
| `gate/00_START.md` | Profile selection as first step; updated navigation map | P02, P25 |
| `gate/STATE_MACHINE.md` | Profile selection states; states 19–36; new terminal states | P02, P25 |
| `gate/TRANSITION_RULES.md` | Profile selection transitions; all new state transitions | P02, P25 |
| `gate/STATE_SCHEMA.md` | Gate 4.1 profile fields; per-cycle Gate 4.1 audit results; overclaim taxonomy | P02, P22, P25 |
| `gate/STATE_FILE_TEMPLATE.yaml` | Gate 4.1 profile fields; per-cycle Gate 4.1 audit result fields | P25 |
| `gate/CYCLE_TRACKER_TEMPLATE.md` | Profile selection header; Gate 4.1 final outcome fields | P25 |
| `gate/06_R2_ACTIVE_PROOF.md` | Artifact lifecycle timing audit section | P04 |
| `gate/07_R3_AI_PATTERNS.md` | 10 new Gate 4.1 failure patterns | P04 |
| `gate/12_PASS_HANDOFF.md` | Overclaim taxonomy requirement; outcome label hard rule | P22 |
| `gate/13_BLOCKED_HANDOFF.md` | Overclaim taxonomy for blocked handoffs | P22 |
| `gate/15_FINAL_PACKAGE_AUDIT.md` | Manifest stat/hash check; warning output findings section | P09 |
| `gate/16_CANONICAL_HANDOFF_AUDIT.md` | Overclaim taxonomy verification | P22 |
| `gate/03_EVIDENCE_CONSISTENCY.md` | Diff base verification section | P16 |
| `gate/PACKAGE_MANIFEST_TEMPLATE.md` | Profile proof files section; integrity section | P24 |
| `gate/SCRIPT_SPEC_check_gate_package.md` | 9 new Gate 4.1 check functions; updated main() | P26 |
| `gate/SELF_TEST_GATE_STATE_MACHINE.md` | Questions 15–24; updated overall assessment | P27 |

---

## Files NOT modified (explicitly preserved)

| File | Reason untouched |
|---|---|
| `gate/01_EVIDENCE_ADEQUACY.md` | No changes required |
| `gate/04_PANEL_ENTRY.md` | No changes required |
| `gate/05_R1_REQUIREMENTS.md` | No changes required |
| `gate/08_R4_HANDOFF.md` | No changes required |
| `gate/09_R5_ADJUDICATION.md` | No changes required |
| `gate/10_GATE_VERDICT.md` | No changes required |
| `gate/11_FIX_CYCLE.md` | No changes required |
| `gate/14_ENFORCEMENT_AUTHORITY_AUDIT.md` | No changes required |
| `gate/17_EXECUTION_CONTEXT_AUDIT.md` | No changes required |
| `gate/CLAIMS_LEDGER_TEMPLATE.yaml` | No changes required |
| `gate/EVIDENCE_LEDGER_TEMPLATE.yaml` | No changes required |
| `gate/STALE_FILE_REGISTER_TEMPLATE.yaml` | No changes required |
| `gate/STALE_FILE_POLICY.md` | No changes required |
| `gate/STATE_MACHINE_EXAMPLES.md` | Preserved; update in a follow-up sprint |
| `gate/ENFORCEMENT_EXAMPLES.md` | Preserved; no changes required |
| `gate/reports/gate-state-machine-upgrade-2026-04-30/` | Prior upgrade artifacts, preserved |
| `gate/examples/known_failures/` | Prior examples, preserved |
