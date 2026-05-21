# Gate 4.1 — Open Questions

**Date:** 2026-05-01

These questions require human decision before they can be resolved.

---

## Q1 — STATE_MACHINE_EXAMPLES.md needs updating

`STATE_MACHINE_EXAMPLES.md` was not updated in this sprint. It contains examples using the old linear flow without profile selection. Downstream agents reading examples will see a Gate 4 flow, not Gate 4.1.

**Decision required:** Should `STATE_MACHINE_EXAMPLES.md` be updated in a follow-up sprint, or should the existing examples be labeled as "Gate 4 examples" to distinguish them from Gate 4.1?

**Recommendation:** Label existing examples as "Gate 4 (legacy)" and add a Gate 4.1 example in a follow-up sprint.

---

## Q2 — Domain addendum files do not yet exist

`GATE_PROFILE_SELECTOR.md` references domain addenda (`model_id_validation`, `data_boundary`, `threat_model`, `financial_audit_trail`, `safety_critical`). None of these addendum files have been created under `gate/domain_addenda/`.

**Impact:** Any task that requires a domain addendum will receive `GATE_PROFILE_SELECTION_BLOCKED` because the addendum file is missing.

**Decision required:** Should a follow-up sprint create the domain addendum files? Which addenda are highest priority?

**Recommendation:** Create `model_id_validation.md` first (most frequently needed for LLM routing tasks). Others can follow.

---

## Q3 — Backward compatibility: `PASS_HANDOFF_COMPLETE` vs profile-specific terminal states

Gate 4 packages (existing runs in `reports/`) use `PASS_HANDOFF_COMPLETE`. Gate 4.1 introduces `GATE_LITE_PASS_HANDOFF_COMPLETE`, `GATE_STANDARD_PASS_HANDOFF_COMPLETE`, and `GATE_FULL_PASS_HANDOFF_COMPLETE`.

`check_gate_package.py` currently accepts `PASS_HANDOFF_COMPLETE` as a valid terminal state. If updated to require profile-specific terminal states, all Gate 4 packages will fail validation.

**Decision required:** Should Gate 4 packages be retroactively migrated, or should `PASS_HANDOFF_COMPLETE` remain valid as a legacy terminal state indefinitely?

**Recommendation:** Keep `PASS_HANDOFF_COMPLETE` as a valid legacy terminal state. New runs from Gate 4.1 onward use profile-specific terminal states. No retroactive migration needed.

---

## Q4 — GATE_EFFECTIVENESS_REGISTER.md doesn't exist yet

`36_GATE_EFFECTIVENESS_LOG.md` instructs agents to append to `gate/GATE_EFFECTIVENESS_REGISTER.md`. This file does not exist and is not created by this sprint.

**Decision required:** Should the first agent to run Step 36 create this file, or should it be created as part of Gate 4.1 initialization?

**Recommendation:** The first Gate 4.1 GATE_FULL run creates it. Document this as a one-time initialization step in Step 36.

---

## Q5 — `DIRTY_WORKTREE_RECURRENCE_REGISTER.md` global vs per-task-area

`27_DIRTY_WORKTREE_RECURRENCE_AUDIT.md` references `gate/DIRTY_WORKTREE_RECURRENCE_REGISTER.md` as the global register. This file does not exist.

**Decision required:** Is the recurrence register global (one file, cross-task) or per-task-area?

**Recommendation:** Global is more useful (cross-task recurrence detection). Create `gate/DIRTY_WORKTREE_RECURRENCE_REGISTER.md` with the seeded common paths as the initial content.

---

## Q6 — check_gate_package.py is specced but not implemented

`SCRIPT_SPEC_check_gate_package.md` now has the Gate 4.1 function specs but the actual Python script has not been written.

**Decision required:** Should the script be implemented in this sprint or a follow-up?

**Recommendation:** Implement in a follow-up sprint. The spec is the authoritative definition; manual gate steps perform the equivalent checks for now.

---

## Q7 — Profile selector "hot files list" needs project-specific review

The hot files list in `GATE_PROFILE_SELECTOR.md` was written for the Scribblios/MetaBuilder project. Other projects using this gate framework will need to customize it.

**Decision required:** Should the hot files list be parameterized (via a project-specific config file) or kept as a static list in `GATE_PROFILE_SELECTOR.md`?

**Recommendation:** Keep as a static list for now, with a clear instruction to update it when new hot files are identified. Parameterization is a Gate 4.2 concern.
