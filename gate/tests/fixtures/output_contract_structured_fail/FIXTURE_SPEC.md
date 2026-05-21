# Fixture: output_contract_structured_fail

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** FAIL with `STALE_MILESTONE_LABEL`

## Why this fixture exists

Gate 5.2-R1 P05: When a structured YAML verdict block declares verdict=FAIL with
listed blocking_findings, the checker must report a corresponding token flag.

## Setup

OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md contains a fenced YAML block with
`output_contract_consistency.verdict: FAIL` and
`blocking_findings: [STALE_MILESTONE_LABEL]`.
