# Gate 4.1 — Final Handoff

**Date:** 2026-05-01
**Final status:** `GATE_4_1_READY_FOR_REVIEW`

---

## Summary

Gate 4.1 adds risk-tiered profile selection and 18 new optional/conditional audit states to the existing Gate 4 state machine. All Gate 4 files are preserved and extended — nothing was deleted or replaced.

---

## Files changed

See `GATE_4_1_CHANGED_FILES.md` for the complete list.

**New files created:** 49 (step files, template files, fixture specs, report files)
**Existing files modified:** 16 (all by appending new sections, not replacing)
**Existing files untouched:** 18

---

## New profiles

| Profile | Risk tier | When to use |
|---|---|---|
| `GATE_LITE` | D0/D1 | Docs-only, tiny isolated leaf changes |
| `GATE_STANDARD` | D2 | Normal implementation slices |
| `GATE_FULL` | D2-hot/D3/D4 | Hot files, migrations, live behavior claims, multi-agent |
| `GATE_FULL_PLUS_DOMAIN_ADDENDUM` | D2-hot+ | Same as Full plus domain-specific checks |

---

## New states (18–36)

| Step | State group | New states |
|---|---|---|
| 18 | Gate Profile Selection | `GATE_PROFILE_SELECTION_IN_PROGRESS`, `GATE_PROFILE_SELECTION_COMPLETE`, `GATE_PROFILE_SELECTION_BLOCKED` |
| 19 | Prompt Contract Review | `PROMPT_CONTRACT_REVIEW_IN_PROGRESS`, `PROMPT_CONTRACT_PASS`, `PROMPT_CONTRACT_NEEDS_REVISION`, `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY` |
| 20 | Production Caller Audit | `PRODUCTION_CALLER_AUDIT_IN_PROGRESS`, `PRODUCTION_CALLER_AUDIT_PASS`, `PRODUCTION_CALLER_AUDIT_FAIL` |
| 21 | Consumer API Proof | `CONSUMER_API_PROOF_AUDIT_IN_PROGRESS`, `CONSUMER_API_PROOF_AUDIT_PASS`, `CONSUMER_API_PROOF_AUDIT_FAIL` |
| 22 | Warning Output Audit | `WARNING_OUTPUT_AUDIT_IN_PROGRESS`, `WARNING_OUTPUT_AUDIT_PASS`, `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` |
| 23 | Test Set Exactness | `REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS`, `REQUIRED_TEST_SET_EXACTNESS_PASS`, `REQUIRED_TEST_SET_EXACTNESS_FAIL` |
| 24 | Migration Runner | `MIGRATION_RUNNER_PROOF_IN_PROGRESS`, `MIGRATION_RUNNER_PROVEN`, `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN`, `MIGRATION_BLOCKED` |
| 25 | Prompt Lint | `IMPLEMENTER_PROMPT_LINT_IN_PROGRESS`, `IMPLEMENTER_PROMPT_LINT_PASS`, `IMPLEMENTER_PROMPT_LINT_FAIL` |
| 26 | Stranded Helper | `STRANDED_HELPER_AUDIT_IN_PROGRESS`, `STRANDED_HELPER_AUDIT_PASS`, `STRANDED_HELPER_AUDIT_FAIL` |
| 27 | Dirty Worktree | `DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS`, `DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS`, `DIRTY_WORKTREE_RECURRENCE_BLOCKER` |
| 28 | Work Allocation | `WORK_ALLOCATION_AUDIT_IN_PROGRESS`, `WORK_ALLOCATION_CLEAR`, `WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE`, `WORK_ALLOCATION_BLOCKED_BY_CONFLICT`, `WORK_ALLOCATION_NEEDS_HUMAN` |
| 29 | Export Channel | `EXPORT_CHANNEL_AUDIT_IN_PROGRESS`, `EXPORT_CHANNEL_AUDIT_PASS`, `EXPORT_CHANNEL_AUDIT_FAIL` |
| 30 | Diff Base Scope | `DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS`, `DIFF_BASE_SCOPE_AUDIT_PASS`, `DIFF_BASE_SCOPE_AUDIT_FAIL` |
| 31 | Flake/Timeout | `FLAKE_TIMEOUT_AUDIT_IN_PROGRESS`, `TEST_STABILITY_OK`, `TEST_STABILITY_WARNING_FOLLOWUP`, `TEST_STABILITY_BLOCKING` |
| 32 | Concurrency | `CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS`, `CONCURRENCY_ASSUMPTIONS_AUDIT_PASS`, `CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL` |
| 33 | Downstream Readiness | `DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS`, `DOWNSTREAM_READY`, `DOWNSTREAM_READY_WITH_CAVEAT`, `DOWNSTREAM_NOT_READY` |
| 34 | Next Prompt Decision | `NEXT_PROMPT_DECISION_IN_PROGRESS`, `NEXT_PROMPT_DECISION_COMPLETE` |
| 35 | CTO Insight | `CTO_OPERATOR_INSIGHT_REVIEW_IN_PROGRESS`, `CTO_OPERATOR_INSIGHT_REVIEW_COMPLETE` |
| 36 | Effectiveness Log | `GATE_EFFECTIVENESS_LOG_IN_PROGRESS`, `GATE_EFFECTIVENESS_LOG_COMPLETE` |

**New profile-specific terminal states:**
- `GATE_LITE_PASS_HANDOFF_COMPLETE`
- `GATE_STANDARD_PASS_HANDOFF_COMPLETE`
- `GATE_FULL_PASS_HANDOFF_COMPLETE`
- `GATE_BLOCKED_REQUIRES_HUMAN`
- `GATE_PROFILE_SELECTION_BLOCKED`

---

## New proof requirements

Every gate run now requires a `GATE_PROFILE_SELECTION.md` proof file (Step 18). The `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` file defines which additional proof files are required per profile. For GATE_FULL, 20+ proof files are required.

---

## How routing works

1. Gate entry: `GATE_NOT_STARTED` → `CYCLE_TRACKER_INITIALIZED`
2. Profile selection: `GATE_PROFILE_SELECTION_IN_PROGRESS` → `GATE_PROFILE_SELECTION_COMPLETE`
3. Profile determines required states for this run
4. For GATE_FULL: run Steps 19–36 at appropriate points in the review sequence
5. For GATE_LITE: skip Steps 19–36; produce NOT_APPLICABLE proof files
6. Terminal state matches profile: `GATE_LITE_PASS_*` / `GATE_STANDARD_PASS_*` / `GATE_FULL_PASS_*`

---

## What remains manual

The following has NOT been automated and requires agent/human execution:
- Profile selection (Step 18) — agent runs it, but no automated pre-check
- All new audit steps (19–36) — agent-run only; no CI equivalent yet
- `check_gate_package.py` Gate 4.1 additions — specced but not implemented (see Open Questions Q6)
- Domain addendum files — specced but not created (see Open Questions Q2)
- `GATE_EFFECTIVENESS_REGISTER.md` — specced but not created (see Open Questions Q4/Q5)

---

## How to use Lite/Standard/Full

See `GATE_4_1_USAGE_GUIDE.md` for complete usage instructions.

Quick reference:
- D0/D1 → `Gate: GATE_LITE`
- D2, no hot files → `Gate: GATE_STANDARD`
- D2-hot/D3/D4, or any hot file → `Gate: GATE_FULL`
- With domain addendum → `Gate: GATE_FULL_PLUS_DOMAIN_ADDENDUM — addenda: [name]`

---

## Compatibility notes with Gate 4

- All Gate 4 states are preserved and unchanged
- `PASS_HANDOFF_COMPLETE` remains valid as a legacy terminal state
- All Gate 4 templates are unchanged
- The five-reviewer cold panel (R1–R5) is unchanged
- Existing Gate 4 packages do not need migration

---

## Open questions needing human decision

See `GATE_4_1_OPEN_QUESTIONS.md` for 7 open questions. The most urgent:
1. Create domain addendum files (Q2) — blocks GATE_FULL_PLUS use
2. Create `GATE_EFFECTIVENESS_REGISTER.md` seed (Q4/Q5)
3. Implement `check_gate_package.py` Gate 4.1 additions (Q6)
4. Update `STATE_MACHINE_EXAMPLES.md` with Gate 4.1 examples (Q1)

---

## Final status

```
GATE_4_1_READY_FOR_REVIEW
```

The documentation, state machine design, and test fixtures are complete. Gate 4.1 can be used immediately for GATE_LITE and GATE_STANDARD. GATE_FULL requires domain addendum file creation before full use. No product or runtime code was modified.
