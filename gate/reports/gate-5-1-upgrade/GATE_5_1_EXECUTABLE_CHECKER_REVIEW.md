# Gate 5.1 Executable Checker Review — P02

**Auditor:** independent gate auditor
**Date:** 2026-05-01

---

## Checker artifact

| Attribute | Value |
|---|---|
| Path | `/Users/syedhaider/Downloads/gate/tools/check_gate_package.py` |
| Lines of code | 829 |
| Language | Python 3 (stdlib + optional PyYAML) |
| External dependencies | PyYAML (optional, falls back to skip-with-warning if absent) |
| Test runner | `tests/test_check_gate_package.py` (213 lines, 7 test functions) |

### First 30 lines of checker source (verbatim)

```python
#!/usr/bin/env python3
"""
check_gate_package.py — Gate 5.1 executable package checker.

Validates a gate package directory or zip against the required proof files,
EXIT_CODE rules, post-PASS error rules, and manifest integrity checks.

Usage:
    python3 tools/check_gate_package.py \
        --package <zip-or-folder> \
        --profile GATE_LITE|GATE_STANDARD|GATE_FULL|GATE_FULL_PLUS_DOMAIN_ADDENDUM \
        --task-area <string> \
        [--task-prompt <file>] \
        [--gate-dir <path>]

Exit codes:
    0 — all required checks pass
    1 — one or more checks failed
    2 — configuration error (missing package, missing YAML, extraction error)
"""

import argparse
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
```

This is real Python 3, not a stub. The script imports stdlib modules, defines real classes (`CheckResult`), and contains 11 distinct check functions.

---

## Per-fixture results

All commands run from a clean shell with `cd /Users/syedhaider/Downloads/gate`:

### 1. happy_path_gate_full

| Field | Value |
|---|---|
| Command | `python3 tools/check_gate_package.py --package tests/fixtures/happy_path_gate_full --profile GATE_FULL --task-area audit_happy_path --gate-dir .` |
| Exit code | **0** |
| Expected | PASS (exit 0) |
| Actual | PASS (exit 0), 42 checks passed, 0 failed |
| Verdict | **PASS** |

Key tail output:
```
[PASS] checker_report_included: GATE_PACKAGE_VALIDATION_REPORT.md found
----------------------------------------------------------------------
Result: PASS
Checks passed: 42  |  Checks failed: 0
```

### 2. blank_exit_code

| Field | Value |
|---|---|
| Exit code | **1** |
| Expected | FAIL with `EXIT_CODE_BLANK` |
| Actual | FAIL, flag `EXIT_CODE_BLANK` emitted |
| Verdict | **PASS** |

Key line:
```
[FAIL] exit_code_strict [EXIT_CODE_BLANK]: raw_test_output.txt: EXIT_CODE line found but value is blank (EXIT_CODE:)
```

### 3. post_pass_enoent

| Field | Value |
|---|---|
| Exit code | **1** |
| Expected | FAIL with `POST_PASS_UNCAUGHT_ERROR` |
| Actual | FAIL, flag emitted; EXIT_CODE check passed (correct — EXIT_CODE:0 is valid in this fixture) |
| Verdict | **PASS** |

Key line:
```
[FAIL] post_pass_uncaught_errors [POST_PASS_UNCAUGHT_ERROR]: raw_test_output.txt: error(s) found after PASS summary. First: 'Error:'
```

### 4. missing_raw_output

| Field | Value |
|---|---|
| Exit code | **1** |
| Expected | FAIL — manifest claims raw output that is absent |
| Actual | FAIL — multiple required-proof-files missing including the registered raw output |
| Verdict | **PASS** |

### 5. manifest_stale_self_size

| Field | Value |
|---|---|
| Exit code | **1** |
| Expected | FAIL — `MANIFEST_SELF_SIZE_STALE` |
| Actual | FAIL with the exact text `MANIFEST_SELF_SIZE_STALE` |
| Verdict | **PASS** |

Key line:
```
[FAIL] manifest_self_size: PACKAGE_MANIFEST.md: manifest lists itself as 0 bytes (actual: 666 bytes) — MANIFEST_SELF_SIZE_STALE
```

### 6. missing_gate_source

| Field | Value |
|---|---|
| Exit code | **1** |
| Expected | FAIL — no gate_used/ or gate_hash.txt |
| Actual | FAIL — `gate_source_included` check fails with the exact rejection text |
| Verdict | **PASS** |

Key line:
```
[FAIL] gate_source_included: MISSING: neither gate_used/ directory nor gate_hash.txt found. A local path to /Users/.../gate is NOT proof.
```

### 7. missing_required_proof_file

| Field | Value |
|---|---|
| Exit code | **1** |
| Expected | FAIL — CYCLE_TRACKER.md absent for GATE_FULL |
| Actual | FAIL — explicit `MISSING: CYCLE_TRACKER.md (required for GATE_FULL)` line plus 25+ other missing files |
| Verdict | **PASS** |

### 8. weak_profile

| Field | Value |
|---|---|
| Command | `... --profile GATE_LITE ...` (mimicking the agent's wrong choice) |
| Exit code | **1** |
| Expected | FAIL — profile escalation violation |
| Actual | FAIL — but for missing required files, not profile-selection validation |
| Verdict | **UNCERTAIN** (incidental fail, not a profile-validation pass) |

The fixture exits 1 because the package is incomplete for GATE_LITE (CYCLE_TRACKER.md, CLAIMS_LEDGER.yaml, etc., are absent). The checker does not parse the task type and reject GATE_LITE for merge verification. Implementer's handoff discloses this gap.

---

## Self-test results (independent re-run)

Command:
```bash
cd /Users/syedhaider/Downloads/gate && python3 tests/test_check_gate_package.py
```

Result (verbatim):
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

Exit code: 0. **7/7 pass.**

---

## Code-level review observations

I read the full 829-line checker source. Notable observations:

### Strengths

1. **Manifest-driven raw output discovery** (lines 213–303): The `find_raw_test_outputs()` function uses three approaches — EVIDENCE_LEDGER.yaml `artifact_type: raw_test_output`, PACKAGE_MANIFEST.md `Raw Test Outputs` table, and a heuristic fallback. The fallback is restricted to likely test-output filenames to avoid scanning the whole package indiscriminately. This is a clean design that matches the prose spec.

2. **EXIT_CODE strict validation** (lines 306–389): Six distinct flags (`EXIT_CODE_MISSING`, `EXIT_CODE_BLANK`, `EXIT_CODE_NON_NUMERIC`, `EXIT_CODE_NONZERO`, `EXIT_CODE_CONFLICTING`, plus implicit-only `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW`). The blank-value branch is the exact M77-P05A failure mode and is handled correctly.

3. **Post-PASS error detection** (lines 396–444): Locates the last PASS summary line, then scans subsequent lines for `Error:`, `ENOENT`, `UnhandledPromiseRejection`, `uncaughtException`, `Jest did not exit`, and 4-space-indent stack trace lines. This is the correct approach.

4. **Circular dependency handled** (lines 142–148, 644–655): GATE_PACKAGE_VALIDATION_REPORT.md is skipped on first run with an explicit comment. Avoids the chicken-and-egg failure where the checker would always fail because its own report doesn't exist yet.

5. **YAML fallback** (lines 58–70): If PyYAML isn't installed, the checker degrades gracefully with a warning. It does not crash. This is operationally important.

### Limitations / minor concerns

1. **Heuristic fallback for raw outputs** (lines 285–301): If neither manifest nor ledger registers raw outputs, the checker falls back to filename pattern matching (`*raw_test_output*`, `*test_output*`, etc.). This means a misnamed raw output that isn't registered could escape detection. Mitigation: `23_REQUIRED_TEST_SET_EXACTNESS.md` requires raw outputs to be registered; an unregistered raw output is BLOCKING for GATE_FULL by prose rule. The checker doesn't enforce this prose rule mechanically.

2. **EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW not implemented** in the executable checker. The flag is defined in `03_EVIDENCE_CONSISTENCY.md` but the checker has no code path that compares EXIT_CODE in summary docs vs. raw outputs. Not a regression vs. Gate 5 (which had no checker), but worth noting.

3. **Profile escalation not validated**: As noted, `weak_profile` fixture is advisory. The checker does not parse task type and reject inappropriate profile selection. The standing rule in P04 covers this via independent profile selection.

4. **`final_git_status_proof` check** (lines 536–560): Looks for files matching `*git_status*` glob OR scans EVIDENCE_CONSISTENCY_REGISTER.md / CYCLE_TRACKER.md / HANDOFF.md for the literal text "git status". This is sound for normal cases but could miss edge cases where git status is recorded only in a non-listed file.

5. **Manifest self-size regex** (lines 495–498): The two patterns expect either `| <bytes>` or `<bytes>$` after the `PACKAGE_MANIFEST.md` token. Unusual manifest formats may not match. This is documented in the usage guide as a known limitation.

### No obvious bugs

I did not find any obvious bugs that would cause false negatives in the verified failure modes. The fixtures I tested all returned the expected exit code with the expected flag.

---

## Verdict on the executable checker

**ACCEPTABLE FOR INSTALLATION.**

The checker:
- Exists as real Python 3 code (829 lines, not a stub)
- Correctly catches all 7 self-test failure modes
- Correctly passes the happy-path fixture (exit 0)
- Has documented limitations the implementer disclosed honestly
- Degrades gracefully on missing dependencies
- Returns proper Unix-style exit codes (0/1/2)

It is not a perfect closed-loop check (profile escalation and stale-report-contradiction gaps remain), but it materially advances the gate from Gate 4.1's specification-only state to a working mechanical enforcement layer.
