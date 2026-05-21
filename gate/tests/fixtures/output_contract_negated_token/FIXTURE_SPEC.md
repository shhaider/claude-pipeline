# Fixture: output_contract_negated_token

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** PASS

## Why this fixture exists

Gate 5.2-R1 P05: When the OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md uses prose like
"No STALE_MILESTONE_LABEL found", the negation-aware fallback scan must NOT
mistake the negated token for a positive detection.

## Setup

OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md has no structured YAML verdict block; it
contains negated prose for every blocking token.
