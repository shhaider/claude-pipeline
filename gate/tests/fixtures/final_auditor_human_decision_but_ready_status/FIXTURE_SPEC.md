# Fixture: final_auditor_human_decision_but_ready_status

Auditor verdict HUMAN_DECISION_REQUIRED but HANDOFF.md says READY (inconsistent — package claims ready despite human decision needed).

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification

## Expected
FAIL with `FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED`.

## Why
HUMAN_DECISION_REQUIRED only allowed when the package routes itself to BLOCKED. A package with verdict=HUMAN_DECISION_REQUIRED that still claims READY/MERGED/VERIFIED is a self-contradiction.
