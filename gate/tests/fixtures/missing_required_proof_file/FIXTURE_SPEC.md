# Fixture Spec: missing_required_proof_file

**Scenario:** Profile is GATE_FULL but CYCLE_TRACKER.md is absent from the package.
CYCLE_TRACKER.md is in the required_always list for GATE_FULL.

**Expected checker result:** FAIL — CYCLE_TRACKER.md missing (required for GATE_FULL).
