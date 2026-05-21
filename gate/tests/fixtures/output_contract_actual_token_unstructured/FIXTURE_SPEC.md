# Fixture: output_contract_actual_token_unstructured

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** FAIL with `STALE_MILESTONE_LABEL`

## Why this fixture exists

Gate 5.2-R1 P05: When no structured verdict block is present, the fallback prose
scan must still detect a positive token in non-negated context.

## Setup

OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md has no structured YAML block. The body
contains "STALE_MILESTONE_LABEL detected in HANDOFF.md line 42".
