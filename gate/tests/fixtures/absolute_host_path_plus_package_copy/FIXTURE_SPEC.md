# Fixture: absolute_host_path_plus_package_copy

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** PASS

## Why this fixture exists

Gate 5.2-R1 P01 allows a host-provenance reference IF the same artifact also has a
package-relative copy. This documents the exact provenance (where the file came from
on the host) without sacrificing the export-completeness rule (the artifact is still
present in the package and verifiable).

## Setup

EVIDENCE_LEDGER.yaml declares one `raw_test_output` artifact with both:
- `provenance_host_path: /tmp/something_that_was_run_on_host.txt`
- `package_relative_path: raw/test_output.txt`

`raw/test_output.txt` exists in the package and contains a valid `EXIT_CODE:0`.

The checker should resolve the host-path leak via the package-relative copy and PASS.
