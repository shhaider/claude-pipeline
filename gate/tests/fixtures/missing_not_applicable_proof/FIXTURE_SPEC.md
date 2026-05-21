# Fixture: missing_not_applicable_proof

**Profile:** GATE_STANDARD
**Risk tier:** D2
**Task kind:** normal_impl
**Expected verdict:** FAIL with `MISSING_NOT_APPLICABLE_PROOF`

## Why this fixture exists

Gate 5.2-R1 P03: `not_applicable_proof_required` becomes a hard requirement, not advisory.
GATE_STANDARD lists DIRTY_WORKTREE_RECURRENCE_AUDIT, CONCURRENCY_ASSUMPTIONS_AUDIT,
CTO_OPERATOR_INSIGHT_REVIEW, and GATE_EFFECTIVENESS_LOG. None of the corresponding
`_NOT_APPLICABLE.md` files are present.

The checker should fire `MISSING_NOT_APPLICABLE_PROOF` for at least one of those.

## Setup

GATE_STANDARD package (sourced from happy_path_gate_full) with all GATE_STANDARD
required_always files present, but no NOT_APPLICABLE proof files.
