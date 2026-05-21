# Fixture Spec: happy_path_gate_full

**Scenario:** Minimal Gate Full happy path. All required files present, valid EXIT_CODE:0,
no post-PASS errors, gate_hash.txt present, manifest not self-referencing 0 bytes.

**Expected checker result:** PASS (exit 0)

**Files included:**
- raw_test_output.txt — valid EXIT_CODE:0, clean post-PASS
- EVIDENCE_LEDGER.yaml — marks raw output as artifact_type: raw_test_output
- CURRENT_STATE.yaml — terminal GATE_FULL_PASS_HANDOFF_COMPLETE
- CYCLE_TRACKER.md — 1 cycle, PASS
- WARNING_OUTPUT_AUDIT.md — no blocking findings
- REQUIRED_TEST_SET_EXACTNESS.md — EXIT_CODE:0 column, no FAIL rows
- GATE_PROFILE_SELECTION.md — GATE_FULL
- package_file_sizes.txt — file size listing
- package_file_hashes.txt — hash listing
- GATE_EFFECTIVENESS_LOG.md — completed
- gate_hash.txt — gate source proof
- git_status_final.txt — git status proof
- GATE_PACKAGE_VALIDATION_REPORT.md — checker report (circular dep note)
- PACKAGE_MANIFEST.md — lists all files

Note on circular dependency: GATE_PACKAGE_VALIDATION_REPORT.md is included in this
fixture to represent the state after a first checker run. The checker skips validating
its own report on first run to avoid the circular dependency.
