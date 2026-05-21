# Gate 5.4 Self-Test Results

- `python3 -m pytest -q tests/test_check_gate_package.py -k "final_auditor or domain_addendum or exit_code or dirty_git_status or not_applicable or warning_audit"`
  - Exit code: `0`
  - Result: `42 passed, 24 deselected in 3.57s`
- `python3 -m pytest -q tests/test_check_gate_package.py`
  - Exit code: `0`
  - Result: `66 passed in 5.43s`
- `python3 tests/test_check_gate_package.py`
  - Exit code: `0`
  - Result: `66 passed, 0 failed`

Additional corrective regression:

- `python3 -m pytest -q tests/test_check_gate_package.py -k "final_auditor or domain_addendum or exit_code or dirty_git_status or not_applicable or warning_audit or full_plus"`
  - Exit code: `0`
  - Result: `44 passed, 22 deselected in 3.80s`

Covered regression areas:

- final auditor structured schema and independence checks
- domain addendum enforcement
- `GATE_FULL_PLUS_DOMAIN_ADDENDUM` inheritance of normal `GATE_FULL` required files
- fence-aware EXIT_CODE parsing
- dirty git-status path parsing
- NOT_APPLICABLE reason validation
- structured and prose warning-audit enforcement
