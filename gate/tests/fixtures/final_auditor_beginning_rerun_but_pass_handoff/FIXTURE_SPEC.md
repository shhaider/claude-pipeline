# Fixture: final_auditor_beginning_rerun_but_pass_handoff

Auditor verdict PASS but RERUN_FROM is BEGINNING — internally inconsistent.
HANDOFF.md says READY/MERGED/VERIFIED.

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification

## Expected
FAIL with `FINAL_PACKET_AUDITOR_RERUN_REQUIRED`.

## Why
RERUN_FROM=BEGINNING means the auditor wants the full gate restarted; the handoff cannot simultaneously claim READY/MERGED/VERIFIED. This catches packages where the auditor "passed" but flagged a need for a full rerun that the operator ignored.
