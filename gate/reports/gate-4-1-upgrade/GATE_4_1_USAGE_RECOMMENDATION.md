# Gate 4.1 — Usage Recommendation

**Date:** 2026-05-01

---

## Immediate recommendation

**Start using Gate 4.1 now for all new gate runs.**

Gate 4.1 is backward-compatible with Gate 4. The profile selection step (Step 18) is the only new required first step. All existing Gate 4 states, templates, and reviewer files are preserved and unchanged.

---

## Rollout sequence

### Phase 1 — GATE_LITE and GATE_STANDARD (today)

These profiles require no new files to be created (no domain addenda, no global registers). They can be used immediately.

Recommended for: all D0/D1/D2 tasks starting today.

### Phase 2 — GATE_FULL (after domain addendum files are created)

GATE_FULL requires domain addendum files to exist before tasks that need them can proceed. Create `gate/domain_addenda/model_id_validation.md` as the first priority (see Open Questions Q2).

Recommended for: all D2-hot/D3/D4 tasks after domain addendum files exist.

### Phase 3 — GATE_EFFECTIVENESS_LOG (after first GATE_FULL run)

The effectiveness register is created on first use. No pre-creation needed.

---

## Compatibility notes with Gate 4

1. **Existing Gate 4 packages remain valid.** `PASS_HANDOFF_COMPLETE` is preserved as a legacy terminal state. No retroactive migration needed.

2. **Existing Gate 4 runs do not need `GATE_PROFILE_SELECTION.md`.** If a package was gated before Gate 4.1, it is a Gate 4 package and does not need the new state. Gate 4.1 applies only to new runs.

3. **The five-reviewer cold panel is unchanged.** R1–R5 remain exactly as in Gate 4. Gate 4.1 adds checks before (Steps 18–19), during (Steps 21–26 in reviewer sequence), and after (Steps 27–36) the panel.

4. **All existing templates remain valid.** New templates are additive. Existing templates (`CLAIMS_LEDGER_TEMPLATE.yaml`, `EVIDENCE_LEDGER_TEMPLATE.yaml`, etc.) are unchanged.

---

## How to tell which gate version a package used

Check the package for:
- `GATE_PROFILE_SELECTION.md` → Gate 4.1
- Absence of `GATE_PROFILE_SELECTION.md` → Gate 4 (legacy)
- `CURRENT_STATE.yaml` field `gate_profile: null` → Gate 4 (legacy)
- `CURRENT_STATE.yaml` field `gate_profile: GATE_LITE/STANDARD/FULL` → Gate 4.1

---

## Most impactful new checks (priority order)

1. **Production Caller Audit** — catches the most common overclaim (LIVE_BEHAVIOR_FIXED without a production caller)
2. **Warning Output Contradiction Audit** — catches silent fallbacks that pass tests but indicate non-functional behavior
3. **Export Channel Audit** — catches "file exists on host but not in zip" failures
4. **Profile Selection** — prevents under-scrutiny of hot-file tasks run through GATE_LITE
5. **Required Test Set Exactness** — catches broad patterns that skip required tests

If running GATE_STANDARD for the first time, focus on verifying these five checks are correctly completed before moving to the less commonly-triggered checks.
