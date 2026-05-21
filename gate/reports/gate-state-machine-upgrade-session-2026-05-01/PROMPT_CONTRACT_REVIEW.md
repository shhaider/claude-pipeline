# Step 19 — Prompt Contract Review

**Task ID:** GATE-SM-UPGRADE-2026-05-01
**Audited at:** 2026-05-01T00:35:00Z
**Profile:** GATE_FULL — mandatory

## The prompt being reviewed

The task prompt for session 1: "Build a 15-part gate state machine upgrade delivering STATE_MACHINE.md (35+ states), TRANSITION_RULES.md, STATE_SCHEMA.md, templates, STALE_FILE_POLICY, step files 15-17, SKILL.md registration, and fixtures. Also add Step 17 Execution Context Audit to catch right-command/wrong-context failures."

The consumer-facing prompt contract is SKILL.md at `~/.claude/skills/gate/SKILL.md`.

## Check 1 — Ambiguous terms

- "Upgrade" — clearly meant creation of new files + updating existing files. No ambiguity in practice (task was explicit about each deliverable).
- "Step 17" — clearly defined as EXECUTION_CONTEXT_AUDIT step. No ambiguity.
- "35+ named states" — clear minimum. STATE_MACHINE.md delivered 111 state-pattern rows.

**Result:** No blocking ambiguity found.

## Check 2 — SKILL.md contract completeness

SKILL.md as consumer-facing prompt:
- Correctly identifies the gate entry point (00_START.md)
- Correctly lists Steps 01-17
- MISSING: Steps 18-36 (Gate 4.1 profile system) — known staleness (R1-NB-03)
- MISSING: GATE_FULL/GATE_LITE profile descriptions
- Gate folder path is hardcoded (R3 finding — by design)

**Result:** SKILL.md is a valid prompt contract for the 17-step gate as it existed at session 1 time. Staleness is documented and non-blocking.

## Check 3 — Lifecycle timing issues

No lifecycle timing issues found. The task was a doc-only creation task with no temporal dependencies (no "run after migration" or "run before merge" conditions).

## Check 4 — Overclaim risk

Main overclaim risk identified: "enforcement" language. The gate says "impossible" to reach PASS_HANDOFF_COMPLETE without Step 17. This overstates enforcement strength.

This was caught by EAA-1 and is a documented non-blocking finding.

## Verdict

**PROMPT_CONTRACT_PASS** — with R1-NB-03 (SKILL.md staleness) as the only non-blocking gap. Prompt was clear, scope was explicit, no blocking ambiguity.
