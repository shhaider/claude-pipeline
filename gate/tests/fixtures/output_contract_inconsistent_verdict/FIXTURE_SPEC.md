# Fixture: output_contract_inconsistent_verdict

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** FAIL with `OUTPUT_CONTRACT_VERDICT_INCONSISTENT`

## Why this fixture exists

Gate 5.2-R1 P05: When a structured YAML verdict block declares verdict=PASS but the
`blocking_findings` list is non-empty, the audit contradicts itself and must block.

## Setup

OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md contains a fenced YAML block with
`output_contract_consistency.verdict: PASS` and
`blocking_findings: [STALE_MILESTONE_LABEL]`.
