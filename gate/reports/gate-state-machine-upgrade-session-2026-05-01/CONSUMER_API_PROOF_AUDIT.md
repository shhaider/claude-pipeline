# Step 21 — Consumer API Proof Audit

**Task ID:** GATE-SM-UPGRADE-2026-05-01
**Audited at:** 2026-05-01T00:35:00Z
**Profile:** GATE_FULL — mandatory

## The consumer API

The gate's consumer API is the protocol that any agent or user follows when using the gate:
1. CURRENT_STATE.yaml format (STATE_SCHEMA.md defines it)
2. The step sequence (00_START.md → numbered steps)
3. Claims and evidence ledger format (templates)
4. Terminal state requirement (PASS_HANDOFF_COMPLETE or GATE_FULL_PASS_HANDOFF_COMPLETE)

## Verification

| Consumer API surface | Defined by | Accessible to consumer? |
|---|---|---|
| CURRENT_STATE.yaml schema | STATE_SCHEMA.md | YES — file on disk |
| Step sequence | 00_START.md routing map | YES — file on disk |
| Claims format | CLAIMS_LEDGER_TEMPLATE.yaml | YES — template on disk |
| Evidence format | EVIDENCE_LEDGER_TEMPLATE.yaml | YES — template on disk |
| Gate initialization | STATE_FILE_TEMPLATE.yaml | YES — template on disk |
| Stale file policy | STALE_FILE_POLICY.md | YES — file on disk |
| Terminal state requirements | 12_PASS_HANDOFF.md | YES — file on disk |
| Step 17 context requirements | 17_EXECUTION_CONTEXT_AUDIT.md | YES — file on disk |

## Consistency check

Does the actual gate protocol (step files) match the SKILL.md description?
- Steps 01-17: YES — SKILL.md table matches step file names and purposes
- Steps 18-36: NO — SKILL.md doesn't describe them (R1-NB-03)

Does STATE_SCHEMA.md match the actual CURRENT_STATE.yaml fields used by the gate?
- YES — verified in R2 direct read (lines 60-109 of STATE_SCHEMA.md)

## Verdict

**PASS** — The consumer API is internally consistent. All consumer-facing surfaces are accessible. The SKILL.md staleness (R1-NB-03) is the only consumer-facing gap and is non-blocking.
