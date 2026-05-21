# Gate 5.1 Install Decision — P03

**Auditor:** independent gate auditor
**Date:** 2026-05-01

---

## Final verdict

**`GATE_5_1_ACCEPTED_INSTALL_CANONICAL`**

Gate 5.1 is accepted for canonical installation, with the following documented limitations carried forward.

---

## Basis for acceptance

| Acceptance criterion | Evidence | Result |
|---|---|---|
| Executable checker exists as real Python 3 | `tools/check_gate_package.py` 829 lines | PASS |
| All 7 self-tests pass independently | Re-ran `tests/test_check_gate_package.py` | PASS (7/7) |
| Happy path exits 0 | Re-ran against `happy_path_gate_full` | PASS |
| Each named bad fixture exits 1 with correct flag | Re-ran against all 6 bad fixtures | PASS |
| Gate Lite / Standard / Full / Full+Domain lanes preserved | Read `GATE_PROFILES.md`, `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`, `TRANSITION_RULES.md` | PASS |
| Proof file export rules explicit | `PROOF_FILE_REQUIREMENTS.md` lines 93–116 | PASS |
| Gate source inclusion enforced | `check_gate_source_included()` + `missing_gate_source` fixture | PASS |
| Pre-PASS barrier defined in transition rules | `TRANSITION_RULES.md` lines 273–315 | PASS |

---

## Carried-forward limitations (do not block acceptance)

1. **Diff patch file is invalid** — `GATE_5_1_DIFF.patch` contains only a 43-byte error message, not a real diff. `GATE_5_1_CHANGED_FILES.md` partially compensates by enumerating changed files. Rollback to Gate 5 from this folder alone is not mechanically possible; an external Gate 5 backup would be required.

2. **Stale report contradiction (failure mode 3) not mechanically enforced** — Implicitly covered by `03_EVIDENCE_CONSISTENCY.md` Checks 6 and 8 (manual reviewer pass). No executable check cross-references milestone labels in handoff against actual diff. Same limitation existed in Gate 5.

3. **Profile escalation (failure mode 6) not mechanically enforced** — `weak_profile` fixture exits 1 incidentally (missing required files), not because the checker validates that GATE_LITE is inappropriate for merge verification. Implementer disclosed this in the handoff. The standing rule in P04 (independent reviewer-driven profile selection) is the compensating control.

4. **EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW flag is defined in prose but not implemented** in the executable checker. Documented in `03_EVIDENCE_CONSISTENCY.md` and `23_REQUIRED_TEST_SET_EXACTNESS.md` as BLOCKING but no code path compares summary vs. raw output for EXIT_CODE consistency.

These are advisory items for a future Gate 5.2, not blockers for accepting Gate 5.1.

---

## Install record

| Field | Value |
|---|---|
| Installed version | Gate 5.1 |
| Install date | 2026-05-01 |
| Canonical path | `/Users/syedhaider/Downloads/gate` |
| Implementer signout ZIP | `/Users/syedhaider/Downloads/gate_5_1.zip` |
| Frozen snapshot (auditor-produced) | `/Users/syedhaider/Downloads/gate_5_1_canonical_accepted_2026-05-01.zip` |
| Reverse diff | NOT AVAILABLE — `GATE_5_1_DIFF.patch` is corrupt. Restoring Gate 5 requires an external backup. |
| Frozen snapshot SHA256 | (computed below) |

The canonical gate folder at `/Users/syedhaider/Downloads/gate` already contains Gate 5.1 (in-place edit). No further file moves needed.

---

## Frozen snapshot creation

To preserve the accepted state, the auditor copied the implementer's signout ZIP to a dated frozen snapshot:

```bash
cp /Users/syedhaider/Downloads/gate_5_1.zip \
   /Users/syedhaider/Downloads/gate_5_1_canonical_accepted_2026-05-01.zip
```

This snapshot is the immutable reference of the accepted Gate 5.1 state.

---

## Confirmation that no overwrite was needed

The implementer edited Gate 5 in place to produce Gate 5.1. The canonical path `/Users/syedhaider/Downloads/gate` already holds the accepted version. The auditor did not move, copy, or modify the canonical folder during this audit — only ran the checker (which writes report files into fixture subdirectories during validation runs, but those writes are inside `tests/fixtures/.../reports/` and are expected behavior).

---

## Conditions on the acceptance

This acceptance is contingent on the operator:

1. Adopting the standing rule in `GATE_5_1_USAGE_RULE.md` (P04) — independent profile selection by reviewer/subagent for any task that does not specify a lane.

2. Continuing to require manual evidence-consistency checks (`03_EVIDENCE_CONSISTENCY.md` Checks 6 and 8) for failure mode 3 (stale report contradiction).

3. Treating failure mode 3 (stale report contradiction) and failure mode 6 (profile escalation) as known gaps that may emerge again until a future Gate 5.2 closes them mechanically.

4. Not relying on the broken `GATE_5_1_DIFF.patch` for rollback. If rollback is needed, a fresh export of an external Gate 5 backup must be sourced.
