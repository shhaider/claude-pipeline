# Gate 5.1 Self-Test Results

**Run date:** 2026-05-01
**Test runner:** `tests/test_check_gate_package.py`
**Checker under test:** `tools/check_gate_package.py`

---

## Test output (verbatim)

```
============================================================
Gate 5.1 self-tests — check_gate_package.py
============================================================
PASS: test_blank_exit_code
PASS: test_post_pass_enoent
PASS: test_missing_raw_output
PASS: test_manifest_stale_self_size
PASS: test_missing_gate_source
PASS: test_missing_required_proof_file
PASS: test_happy_path
------------------------------------------------------------
7 passed, 0 failed
============================================================
```

---

## Summary

| Test | Result | Fixture | Failure mode verified |
|---|---|---|---|
| test_blank_exit_code | PASS | blank_exit_code | EXIT_CODE_BLANK flag emitted |
| test_post_pass_enoent | PASS | post_pass_enoent | POST_PASS_UNCAUGHT_ERROR flag emitted |
| test_missing_raw_output | PASS | missing_raw_output | Manifest-listed file absent → FAIL |
| test_manifest_stale_self_size | PASS | manifest_stale_self_size | 0-byte self-size → FAIL |
| test_missing_gate_source | PASS | missing_gate_source | No gate_used/ or gate_hash.txt → FAIL |
| test_missing_required_proof_file | PASS | missing_required_proof_file | CYCLE_TRACKER.md absent for GATE_FULL → FAIL |
| test_happy_path | PASS | happy_path_gate_full | Minimal GATE_FULL package → PASS (exit 0) |

**Total: 7/7 tests passed. Exit code: 0.**

---

## M77-P05A failure modes confirmed caught

1. **Blank EXIT_CODE** (`EXIT_CODE:` with no value): caught by `test_blank_exit_code` — flag `EXIT_CODE_BLANK` emitted, exit nonzero.
2. **Post-PASS ENOENT** (ENOENT after `Tests: N passed`): caught by `test_post_pass_enoent` — flag `POST_PASS_UNCAUGHT_ERROR` emitted, exit nonzero.

Both failure modes now cause mechanical exit-nonzero. A Gate Full package with either failure cannot pass the checker.
