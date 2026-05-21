# Fixture: output_contract_structured_pass

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** PASS

## Why this fixture exists

Gate 5.2-R1 P05: When a structured YAML verdict block is present with verdict=PASS
and an empty blocking_findings list, the checker uses the structured verdict directly
(no prose scanning).

## Setup

OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md contains a fenced YAML block with
`output_contract_consistency.verdict: PASS` and `blocking_findings: []`.
