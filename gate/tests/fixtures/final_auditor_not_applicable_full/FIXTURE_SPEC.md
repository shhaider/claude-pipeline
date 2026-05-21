# Fixture: final_auditor_not_applicable_full

GATE_FULL package attempting to use FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md instead of the report.

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification

## Expected
FAIL — Gate Full does not allow NOT_APPLICABLE for FINAL_PACKET_AUDITOR_REPORT.md.
The check fires `FINAL_PACKET_AUDITOR_MISSING` (since the actual report is absent) and `REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING` (since the file is on the GATE_FULL required_always list).

## Why
The auditor is mandatory for Gate Full and Gate Full Plus regardless of operator justification. Only GATE_LITE accepts NOT_APPLICABLE.

## Test invocation
The test runs with `--profile GATE_FULL`.
