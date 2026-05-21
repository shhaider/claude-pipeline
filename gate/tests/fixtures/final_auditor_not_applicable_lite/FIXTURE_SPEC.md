# Fixture: final_auditor_not_applicable_lite

GATE_LITE docs-only package. FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md present with substantive reason.

**Profile:** GATE_LITE
**Risk tier:** D0
**Task kind:** docs

## Expected
PASS (exit 0).

## Why
GATE_LITE allows NOT_APPLICABLE for the final packet auditor when the package is not being returned to operator as signout. The NOT_APPLICABLE file must contain a substantive reason (per the Gate 5.2-R1 NA-substantive-reason rule).

## Test invocation
The test runs with `--profile GATE_LITE --risk-tier D0 --task-kind docs`.
