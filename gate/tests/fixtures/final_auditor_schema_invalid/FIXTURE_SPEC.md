# Fixture: final_auditor_schema_invalid

FINAL_PACKET_AUDITOR_REPORT.md is missing RERUN_FROM (only four of five required fields present).

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification

## Expected
FAIL with `FINAL_PACKET_AUDITOR_SCHEMA_INVALID`.

## Why
All five fields (VERDICT, REASON, BLOCKERS, REQUIRED_FIX, RERUN_FROM) are mandatory. Missing any one is a schema violation regardless of verdict.
