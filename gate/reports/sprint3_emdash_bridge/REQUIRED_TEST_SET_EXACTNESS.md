# Required Test Set Exactness
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 23

State: REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS

---

## Check 1 -- Required test set identification

The contract (contract.md) specifies: `pytest tests/test_bridge.py` must pass.
The HANDOFF.md confirms: "Bridge tests: 8 passed, 1 skipped (exit 0)".

Required test file: `tests/test_bridge.py`

This is an exact file specification, not a pattern.

---

## Check 2 -- Verify required test file was included in run

Test command used (from EVIDENCE_LEDGER.yaml E001): `pytest tests/test_bridge.py -v`

The raw output (test_output.txt) shows:
```
tests/test_bridge.py::test_decide_allow_no_state_root PASSED
tests/test_bridge.py::test_decide_allow_no_active_runs PASSED
tests/test_bridge.py::test_decide_allow_implementation_state PASSED
tests/test_bridge.py::test_decide_deny_planning_state PASSED
tests/test_bridge.py::test_decide_deny_tool_closed SKIPPED
tests/test_bridge.py::test_decide_allow_completed_run PASSED
tests/test_bridge.py::test_decide_deny_unknown_state_not_in_implementation_states PASSED
tests/test_bridge.py::test_http_server_allow PASSED
tests/test_bridge.py::test_http_server_deny PASSED
```

The exact required test file (`tests/test_bridge.py`) appears in every test line. 9 items collected, 8 passed, 1 skipped.

---

## Check 3 -- EXIT_CODE verification

Raw output file: test_output.txt
EXIT_CODE line present: YES (line 20, value 0, format has space between colon and digit)
Parsed value: 0
Post-PASS errors: NONE
All exit code checks passed. EXIT_CODE:0 is in the raw output file itself, not only in summary documents.

---

## Check 4 -- Broad pattern verification

The test command `pytest tests/test_bridge.py -v` targets a specific file, not a broad pattern. No pattern substitution issue.

---

## Required table

Test claim: `pytest tests/test_bridge.py -v`
Raw output path: test_output.txt
Listed in manifest: YES (EVIDENCE_LEDGER.yaml E001)
Included in package: YES
EXIT_CODE parsed: 0 (valid)
Post-pass errors: NONE
Verdict: PASS

---

## Raw output registration check (Gate 5.1)

test_output.txt is registered in EVIDENCE_LEDGER.yaml as artifact E001 with `artifact_type: raw_test_output`.
PACKAGE_MANIFEST.md will list this file.

Raw output is registered. No issues.

---

## Verdict

Required test file `tests/test_bridge.py` is present in the raw output.
All 9 tests accounted for (8 passed, 1 skipped).
EXIT_CODE:0 confirmed in raw output.
No post-PASS errors.

State: **REQUIRED_TEST_SET_EXACTNESS_PASS**
