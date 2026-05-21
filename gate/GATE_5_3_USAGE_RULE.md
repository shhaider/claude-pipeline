# Gate 5.3 — Standing Usage Rule

**Status:** Active as of 2026-05-01
**Authority:** Gate 5.3 acceptance audit
**Supersedes:** Nothing — Gate 5.3 ADDS to Gate 5.2-R1. `GATE_5_2_USAGE_RULE.md` remains canonical for everything 5.2-R1 enforces. This file documents only the 5.3 additions.

---

## What is new in Gate 5.3

1. **`FINAL_PACKET_AUDITOR` state (state 37, file `37_FINAL_PACKET_AUDITOR.md`).** A simple, independent, context-light final review that runs AFTER the structured gate has already passed. Sits between `16_CANONICAL_HANDOFF_AUDIT.md` (state 16) and `12_PASS_HANDOFF.md` (state 12).

2. **Mechanical enforcement.** `tools/check_gate_package.py` now requires a valid `FINAL_PACKET_AUDITOR_REPORT.md` for GATE_STANDARD, GATE_FULL, and GATE_FULL_PLUS_DOMAIN_ADDENDUM signouts. GATE_LITE accepts a `FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md` with a substantive reason for non-export packages only.

3. **Rerun policy.** Final auditor FAIL routes to `11_FIX_CYCLE.md`. The fix triggers a profile-dependent rerun strategy (full restart for GATE_FULL / GATE_FULL_PLUS, conditional for GATE_STANDARD, targeted for GATE_LITE docs-only).

4. **Telemetry block.** New `final_packet_auditor:` block in `GATE_EFFECTIVENESS_LOG_TEMPLATE.md` and `36_GATE_EFFECTIVENESS_LOG.md` for measuring auditor effectiveness.

5. **New flags emitted by the checker:**
   - `FINAL_PACKET_AUDITOR_MISSING`
   - `FINAL_PACKET_AUDITOR_FAIL`
   - `FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED`
   - `FINAL_PACKET_AUDITOR_SCHEMA_INVALID`
   - `FINAL_PACKET_AUDITOR_RERUN_REQUIRED`

---

## Intentional simplicity of the auditor prompt

The reviewer prompt is intentionally short and decision-oriented:

- Decide PASS / FAIL / HUMAN_DECISION_REQUIRED.
- Output exactly five fields: VERDICT, REASON, BLOCKERS, REQUIRED_FIX, RERUN_FROM.
- Do not praise. Do not summarize everything.

This matters because every prior bolt-on (R1, R2, R3, R4, R5, output-contract audit, canonical-handoff audit) accumulated checks until the prompt sprawled. The auditor is designed to escape that gravity. Keep it simple. Do not add new bullet points. Do not over-specify.

If a class of issue is recurring, fix the upstream reviewer (R1–R5) — not the auditor.

---

## Independence requirements

When at all possible, run the auditor as:

- a fresh subagent (recommended for any GATE_FULL or stronger run),
- a fresh session,
- a fresh model (not the model that produced the package),
- with no prior context from this gate run,
- using a Tier 3 / high-effort model when available for high-risk profiles.

If no isolated session is available, the main agent may run it — but the report MUST explicitly state that independence was not achieved (in the "Independence" section of the report). Without that disclosure, the report is suspect.

The `FINAL_PACKET_AUDITOR_REPORT_TEMPLATE.md` includes the Independence section as a leading block.

---

## Cannot be skipped

For GATE_FULL and GATE_FULL_PLUS_DOMAIN_ADDENDUM:
- The auditor is mandatory.
- `FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md` is NEVER acceptable in place of the report.
- Skipping the auditor is a state machine violation.

For GATE_STANDARD:
- The auditor is mandatory.
- NA only allowed when explicitly specified by an upgraded operator policy (out of scope for the current rule).

For GATE_LITE:
- The auditor is required for any package being returned to operator as signout/export.
- For internal docs-only packages not returned to operator, `FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md` with a substantive reason is acceptable.

---

## Failure restarts the full gate (FULL / FULL_PLUS)

Per `TRANSITION_RULES.md` and `11_FIX_CYCLE.md`, a FAIL verdict from the final auditor on GATE_FULL / GATE_FULL_PLUS_DOMAIN_ADDENDUM forces a full restart from Evidence Adequacy. The reasoning:

> A fix can change evidence, scope, tests, package contents, or report consistency. A surface-only re-check is unsafe.

GATE_STANDARD allows targeted reruns for non-authoritative typo fixes only.

GATE_LITE allows targeted reruns for docs-only / report-only fixes; if the fix touches source/test/runtime artifacts, the profile must be upgraded.

If the same package fails the final auditor twice, escalate one profile level and require a CTO / Operator Insight Review.

---

## How the checker enforces the auditor

```bash
python3 "/Users/syedhaider/Downloads/gate/tools/check_gate_package.py" \
  --package <your-export-package-folder-or-zip> \
  --profile GATE_FULL \
  --task-area <task_area> \
  --risk-tier <risk> \
  --task-kind <kind> \
  --gate-dir "/Users/syedhaider/Downloads/gate" \
  --final
```

The checker verifies (in order):

1. `reports/<task_area>/FINAL_PACKET_AUDITOR_REPORT.md` exists (or, for GATE_LITE only, the NA file with substantive reason exists).
2. All five required fields appear in the body: `FINAL_PACKET_AUDITOR_VERDICT:`, `REASON:`, `BLOCKERS:`, `REQUIRED_FIX:`, `RERUN_FROM:`.
3. `FINAL_PACKET_AUDITOR_VERDICT` matches `PASS | FAIL | HUMAN_DECISION_REQUIRED`.
4. `RERUN_FROM` matches `BEGINNING | TARGETED_STATE:<name> | HUMAN_DECISION`.
5. If verdict = FAIL: emit `FINAL_PACKET_AUDITOR_FAIL`.
6. If verdict = HUMAN_DECISION_REQUIRED but the handoff claims READY/MERGED/VERIFIED: emit `FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED`.
7. If RERUN_FROM = BEGINNING but the handoff claims READY/MERGED/VERIFIED: emit `FINAL_PACKET_AUDITOR_RERUN_REQUIRED`.

A schema problem at any of those steps emits `FINAL_PACKET_AUDITOR_SCHEMA_INVALID`.

---

## Operator checklist before declaring PASS (Gate 5.3 additions)

In addition to the Gate 5.2-R1 operator checklist:

```
[ ] FINAL_PACKET_AUDITOR_REPORT.md exists at reports/<task_area>/
[ ] All five fields present: VERDICT, REASON, BLOCKERS, REQUIRED_FIX, RERUN_FROM
[ ] FINAL_PACKET_AUDITOR_VERDICT is PASS
[ ] Auditor was a fresh subagent (or independence-not-achieved is explicitly declared)
[ ] For GATE_FULL/GATE_FULL_PLUS: Tier 3 / high-effort model used
[ ] If verdict was FAIL on a prior cycle, the rerun policy was followed (full restart for FULL)
[ ] tools/check_gate_package.py --final exits 0 under Gate 5.3
[ ] Effectiveness log includes the final_packet_auditor: telemetry block
```

If any item is unchecked, do not declare PASS.

---

## Standing limitations

1. **Independence is policy-enforced**, not mechanically verifiable. The checker reads the "Independence achieved" line as plain text — it cannot prove a fresh subagent actually ran. Operator vigilance required.
2. **Schema validation is regex-based** with markdown-bullet tolerance. A structurally valid but semantically empty report could pass (e.g., `REASON:\n- ` with no actual prose). Upstream reviewers — not the schema check — catch that.
3. **Lane D and other prior packages** built before Gate 5.3 will fail the new auditor check until they include a FINAL_PACKET_AUDITOR_REPORT.md. This is the new check working as intended, not a regression.
4. **Gate 5.4 follow-on hardening closed the major known backlog items** in a separate rule file: `GATE_5_4_USAGE_RULE.md`.
