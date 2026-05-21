# Fixture: absolute_raw_output_outside_package

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** FAIL with `HOST_PATH_NOT_PACKAGE_EVIDENCE`

## Why this fixture exists

Gate 5.2-R1 P01: An exported package must contain its own raw test outputs. A package that
declares an absolute host path like `/tmp/some_raw_output.txt` in EVIDENCE_LEDGER.yaml has not
actually exported the evidence — it is referencing a host filesystem location that may be
gone, modified, or different on a reviewer's machine.

The checker must flag this as `HOST_PATH_NOT_PACKAGE_EVIDENCE` and refuse PASS.

## Setup

Same as happy_path_gate_full, but:
- `EVIDENCE_LEDGER.yaml` declares a single `raw_test_output` artifact whose `artifact_path`
  is `/tmp/some_raw_output.txt`
- That file is NOT included in the package
- No `package_relative_path` field is provided
