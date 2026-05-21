# Step 25 — Implementer Prompt Lint

**Task ID:** GATE-SM-UPGRADE-2026-05-01
**Audited at:** 2026-05-01T00:35:00Z
**Profile:** GATE_FULL — applicable (SKILL.md is a prompt artifact)

## The prompt artifact

SKILL.md at `~/.claude/skills/gate/SKILL.md` is the user-facing prompt for invoking the gate.

## Lint checks

| Check | Result |
|---|---|
| References to non-existent step files | PASS — all referenced files (01-17, 00_START.md) exist on disk |
| References to non-existent states | PASS — all states in step table exist in STATE_MACHINE.md |
| Undeclared variables or undefined terms | PASS — all terms defined within SKILL.md or in referenced files |
| Impossible imports or circular references | NOT_APPLICABLE — Markdown prompt, no code imports |
| Invalid file paths | PARTIAL — gate folder path is hardcoded (/Users/syedhaider/Downloads/gate/) but by design for personal skill |
| Stale references (steps that no longer exist as described) | PARTIAL — Step 18 not mentioned in SKILL.md; Steps 19-36 not mentioned |

## Verdict

**PASS** — The SKILL.md prompt is valid for its described scope (Steps 01-17). The stale references (Steps 18-36 not listed) are a documentation gap (R1-NB-03), not an invalid prompt — the gate is still invokable via SKILL.md.
