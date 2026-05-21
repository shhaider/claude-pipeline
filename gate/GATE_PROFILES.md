# Gate Profiles

## Gate 5.4 profile enforcement

- `D0` / `D1` plus `docs` or `tiny_test` may use `GATE_LITE`.
- `D2 normal_impl` must use at least `GATE_STANDARD`.
- `D2_HOT`, `D3`, and `D4` require `GATE_FULL` or `GATE_FULL_PLUS_DOMAIN_ADDENDUM`.
- `migration`, `runtime_state`, `merge_verification`, `release_verification`, `production_wiring`, `provider_model_routing`, `gate_change`, `prompt_authoring`, and `evidence_package` require `GATE_FULL` or stronger.
- A weaker selected profile is blocking.

## Gate 5.4 mandatory profile metadata (every package, every profile)

Every `GATE_PROFILE_SELECTION.md` — including `GATE_LITE` packages — must declare all four
of these fields. The Gate 5.2-R1 checker fires `MISSING_GATE_PROFILE_SELECTION`,
`MISSING_RISK_TIER`, `MISSING_TASK_KIND`, and `MISSING_PROFILE_REASON` if any are absent.

| Field | Allowed values |
|---|---|
| `selected_profile` (or `gate_profile`) | `GATE_LITE`, `GATE_STANDARD`, `GATE_FULL`, `GATE_FULL_PLUS_DOMAIN_ADDENDUM` |
| `risk_tier` | `D0`, `D1`, `D2`, `D2_HOT`, `D3`, `D4` |
| `task_kind` | `docs`, `tiny_test`, `normal_impl`, `hot_file`, `migration`, `runtime_state`, `merge_verification`, `release_verification`, `production_wiring`, `provider_model_routing`, `gate_change`, `prompt_authoring`, `evidence_package` |
| `reason` (or `profile_selection_rationale`) | A non-empty rationale string |

Without these four fields the WRONG_GATE_PROFILE selector cannot mechanically catch
under-selection (e.g. picking `GATE_LITE` for a `merge_verification` task), so they are
mandatory regardless of profile strength.

The gate uses four profiles to match verification depth to task risk. Profile selection occurs before any other gate state. See `18_GATE_PROFILE_SELECTION.md` for how to select the correct profile.

---

## GATE_LITE

### When to use

- D0 tasks: documentation-only changes (no code, no schema, no config)
- D1 tasks: tiny isolated changes with no shared-state impact — adding a single test helper, fixing a typo in a utility function, updating a constant in a leaf module
- Tasks that touch zero hot files (see `GATE_PROFILE_SELECTOR.md` hot files list)
- No downstream consumers can break
- No migration, no schema change, no runtime state change

### Required states

| State | Required? |
|---|---|
| `GATE_PROFILE_SELECTION_COMPLETE` | YES |
| `EVIDENCE_ADEQUACY_IN_PROGRESS` | YES |
| `EVIDENCE_CONSISTENCY_IN_PROGRESS` | YES |
| `ENFORCEMENT_AUDIT_*` | NO — skip if not applicable |
| `PANEL_ENTRY_VERIFIED` | YES |
| `R1_IN_PROGRESS` through `R5_COMPLETE` | YES (all five reviewers) |
| `GATE_VERDICT_ISSUED` | YES |
| `FINAL_PACKAGE_AUDIT_IN_PROGRESS` | YES |
| `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS` | YES |
| `EXECUTION_CONTEXT_AUDIT_*` | Conditional (run if context claims present) |

### Required proof files

- `CURRENT_STATE.yaml`
- `CYCLE_TRACKER.md`
- `CLAIMS_LEDGER.yaml`
- `EVIDENCE_LEDGER.yaml`
- `STALE_FILE_REGISTER.yaml`
- `PACKAGE_MANIFEST.md`
- `EVIDENCE_ADEQUACY_ASSESSMENT.md`
- `EVIDENCE_CONSISTENCY_REGISTER.md`
- All five cold review reports
- `GATE_PROFILE_SELECTION.md`

### Skipped states

The following Gate 4.1 states are NOT APPLICABLE for GATE_LITE (produce `STATE_NAME_NOT_APPLICABLE.md` if the final package must be complete):
- `PROMPT_CONTRACT_REVIEW_*`
- `PRODUCTION_CALLER_AUDIT_*`
- `CONSUMER_API_PROOF_AUDIT_*`
- `WARNING_OUTPUT_AUDIT_*`
- `REQUIRED_TEST_SET_EXACTNESS_*`
- `MANIFEST_FINALIZATION_AUDIT_*`
- `MIGRATION_RUNNER_PROOF_*`
- `IMPLEMENTER_PROMPT_LINT_*`
- `STRANDED_HELPER_AUDIT_*`
- `DIRTY_WORKTREE_RECURRENCE_AUDIT_*`
- `WORK_ALLOCATION_AUDIT_*`
- `EXPORT_CHANNEL_AUDIT_*`
- `DIFF_BASE_SCOPE_AUDIT_*`
- `FLAKE_TIMEOUT_AUDIT_*`
- `CONCURRENCY_ASSUMPTIONS_AUDIT_*`
- `DOWNSTREAM_CONSUMER_READINESS_AUDIT_*`
- `NEXT_PROMPT_DECISION_*`
- `CTO_OPERATOR_INSIGHT_REVIEW_*`
- `GATE_EFFECTIVENESS_LOG_*`

### Terminal state

`GATE_LITE_PASS_HANDOFF_COMPLETE`

---

## GATE_STANDARD

### When to use

- D2 tasks: normal implementation slices
- New features in non-hot modules
- Test coverage improvements
- Refactors within a bounded scope with no hot-file touches
- No migrations, no runtime state changes, no shared config changes
- Not touching gate files, branch governance, or provider/model routing

### Required states (all GATE_LITE states plus)

| State | Required? |
|---|---|
| All GATE_LITE states | YES |
| `PROMPT_CONTRACT_REVIEW_*` | Conditional — required if task prompt is complex or has lifecycle timing |
| `PRODUCTION_CALLER_AUDIT_*` | YES — required if task claims wired live behavior |
| `CONSUMER_API_PROOF_AUDIT_*` | YES — required if task adds repository/helper APIs |
| `WARNING_OUTPUT_AUDIT_*` | YES — required for any task with raw test output |
| `REQUIRED_TEST_SET_EXACTNESS_*` | YES |
| `MANIFEST_FINALIZATION_AUDIT_*` | YES |
| `STRANDED_HELPER_AUDIT_*` | YES — required if task adds new helpers or exports |
| `EXPORT_CHANNEL_AUDIT_*` | YES |
| `DIFF_BASE_SCOPE_AUDIT_*` | YES |
| `NEXT_PROMPT_DECISION_*` | YES |

### Skipped states for GATE_STANDARD

- `IMPLEMENTER_PROMPT_LINT_*` — optional unless package includes implementation prompts
- `MIGRATION_RUNNER_PROOF_*` — skip if no DB/schema changes
- `DIRTY_WORKTREE_RECURRENCE_AUDIT_*` — skip unless same path has dirtied twice
- `WORK_ALLOCATION_AUDIT_*` — skip unless multi-agent or hot-file conflict
- `FLAKE_TIMEOUT_AUDIT_*` — skip unless tests show timing sensitivity
- `CONCURRENCY_ASSUMPTIONS_AUDIT_*` — skip unless touching shared state/queue
- `DOWNSTREAM_CONSUMER_READINESS_AUDIT_*` — skip unless declaring next phase ready
- `CTO_OPERATOR_INSIGHT_REVIEW_*` — optional for D2, mandatory for D2-hot+
- `GATE_EFFECTIVENESS_LOG_*` — recommended but not blocking

### Terminal state

`GATE_STANDARD_PASS_HANDOFF_COMPLETE`

---

## GATE_FULL

### When to use

- D2-hot tasks: touching any hot file (see `GATE_PROFILE_SELECTOR.md` hot files list)
- D3 tasks: migrations, runtime state, gate logic, handoff packages, merge verification, branch governance
- D4 tasks: provider/model routing, cross-system evidence packages, multi-agent coordination, repeated correction loops (cycle 3+)
- Any task that claims live behavior is fixed, production wiring is complete, or crash recovery is in place
- Any task involving multiple agents working on the same files simultaneously

### Required states (all GATE_STANDARD states plus)

| State | Required? |
|---|---|
| All GATE_STANDARD states | YES |
| `PROMPT_CONTRACT_REVIEW_*` | YES — mandatory |
| `ARTIFACT_LIFECYCLE_TIMING_AUDIT_*` | YES |
| `PRODUCTION_CALLER_AUDIT_*` | YES — mandatory |
| `CONSUMER_API_PROOF_AUDIT_*` | YES — mandatory |
| `WARNING_OUTPUT_AUDIT_*` | YES — mandatory |
| `MIGRATION_RUNNER_PROOF_*` | YES if any migration present |
| `IMPLEMENTER_PROMPT_LINT_*` | YES if package includes implementation prompts |
| `STRANDED_HELPER_AUDIT_*` | YES — mandatory |
| `DIRTY_WORKTREE_RECURRENCE_AUDIT_*` | YES |
| `WORK_ALLOCATION_AUDIT_*` | YES if multi-agent or hot-file conflict |
| `EXPORT_CHANNEL_AUDIT_*` | YES — mandatory |
| `DIFF_BASE_SCOPE_AUDIT_*` | YES — mandatory |
| `FLAKE_TIMEOUT_AUDIT_*` | YES |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_*` | YES if state/persistence/queue/multi-agent |
| `DOWNSTREAM_CONSUMER_READINESS_AUDIT_*` | YES |
| `NEXT_PROMPT_DECISION_*` | YES — mandatory |
| `CTO_OPERATOR_INSIGHT_REVIEW_*` | YES — mandatory |
| `GATE_EFFECTIVENESS_LOG_*` | YES |

### Terminal state

`GATE_FULL_PASS_HANDOFF_COMPLETE`

---

## GATE_FULL_PLUS_DOMAIN_ADDENDUM

### When to use

Same as GATE_FULL but the task domain requires additional checks not covered by the base gate. Examples:
- Medical/safety-critical systems (additional safety check addendum)
- Financial/billing systems (additional audit trail addendum)
- Multi-tenant isolation (additional data boundary addendum)
- Security-sensitive operations (additional threat model addendum)
- Regulatory compliance work (additional compliance mapping addendum)
- LLM routing / provider model selection (additional model ID validation addendum)

### Required states

All GATE_FULL states plus one or more domain addenda specified at profile selection time. Domain addenda are listed in the `domain_addenda` field of the GATE_PROFILE_SELECTION.yaml output.

### How domain addenda work

1. At profile selection, the agent or operator specifies which domain addenda apply.
2. Under Gate 5.4, `GATE_FULL_PLUS_DOMAIN_ADDENDUM` fails if `domain_addenda` is empty, any addendum name is invalid, the source definition is missing under `domain_addenda/`, or the exact package proof file is missing.
2. Each addendum is a named checklist or state that must complete before the gate can pass.
3. Addendum files live under `gate/domain_addenda/<name>.md`.
4. If an addendum file does not exist for the named domain, the gate must halt and report `GATE_PROFILE_SELECTION_BLOCKED`.

### Terminal state

`GATE_FULL_PASS_HANDOFF_COMPLETE` (same as GATE_FULL — addenda are part of the Full path)

---

## Profile comparison table

| Capability | GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS |
|---|---|---|---|---|
| Five cold-review panel | YES | YES | YES | YES |
| Evidence adequacy + consistency | YES | YES | YES | YES |
| Enforcement authority audit | Conditional | Conditional | YES | YES |
| Prompt contract review | NO | Conditional | YES | YES |
| Artifact lifecycle timing audit | NO | NO | YES | YES |
| Production caller audit | NO | YES (if wired) | YES | YES |
| Consumer API proof audit | NO | YES (if API added) | YES | YES |
| Warning output contradiction audit | NO | YES | YES | YES |
| Required test set exactness | NO | YES | YES | YES |
| Manifest stat/hash check | NO | YES | YES | YES |
| Migration runner proof | NO | Conditional | YES (if migration) | YES |
| Implementer prompt lint | NO | Conditional | YES (if prompts) | YES |
| Stranded helper audit | NO | YES (if new symbols) | YES | YES |
| Dirty worktree recurrence | NO | Conditional | YES | YES |
| Work allocation audit | NO | Conditional | YES (multi-agent) | YES |
| Export channel audit | NO | YES | YES | YES |
| Diff base/scope audit | NO | YES | YES | YES |
| Flake/timeout audit | NO | Conditional | YES | YES |
| Concurrency assumptions audit | NO | Conditional | YES (state/queue) | YES |
| Downstream consumer readiness | NO | Conditional | YES | YES |
| Next prompt decision | NO | YES | YES | YES |
| CTO/operator insight review | NO | Optional | YES | YES |
| Gate effectiveness log | NO | Recommended | YES | YES |
| Domain addenda | NO | NO | NO | YES |
| Final Packet Auditor (Gate 5.3, state 37) | Required-on-export (NA-allowed for non-export) | YES (mandatory) | YES (mandatory) | YES (mandatory) |
