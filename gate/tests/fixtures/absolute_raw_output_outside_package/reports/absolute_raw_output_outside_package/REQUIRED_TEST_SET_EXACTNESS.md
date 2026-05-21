# Required Test Set Exactness

**Task area:** absolute_raw_output_outside_package
**Audit completed at:** 2026-05-01T00:00:00Z

## Required test set verification table

(no in-package raw outputs — declared raw output uses an absolute host path; see EVIDENCE_LEDGER.yaml)

## Verdict

REQUIRED_TEST_SET_EXACTNESS_PASS

**Rationale:** Bad-fixture: the host-path leak should fail under HOST_PATH_NOT_PACKAGE_EVIDENCE, not under this audit. This file intentionally lists no raw output rows so the only firing flag is the host-path leak.
