# Fixture Spec: missing_raw_output

**Scenario:** REQUIRED_TEST_SET_EXACTNESS.md claims tests/foo.test.js was run (PASS verdict row),
but the raw output file listed in EVIDENCE_LEDGER.yaml is absent from the package.

**Expected checker result:** FAIL — raw output file listed in manifest/ledger but absent from package.

**Why this matters:** Proves that manifest-driven discovery catches missing raw outputs
even when the REQUIRED_TEST_SET_EXACTNESS file claims PASS.
