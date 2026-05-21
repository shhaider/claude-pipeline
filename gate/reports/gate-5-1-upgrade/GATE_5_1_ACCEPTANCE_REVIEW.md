# Gate 5.1 Acceptance Review — P00

**Auditor role:** independent gate auditor (Step 8 in software-dev pipeline)
**Date:** 2026-05-01
**Canonical gate path:** `/Users/syedhaider/Downloads/gate`
**Implementer signout ZIP:** `/Users/syedhaider/Downloads/gate_5_1.zip`

---

## Question-by-question answers

### Q1 — Does the package include the full updated gate folder?

**YES.** The canonical gate folder at `/Users/syedhaider/Downloads/gate/` contains the in-place edited Gate 5.1. The implementer's ZIP at `/Users/syedhaider/Downloads/gate_5_1.zip` is an exported copy of the same folder.

Evidence: `unzip -l /Users/syedhaider/Downloads/gate_5_1.zip` shows the full folder structure, including:
- `gate/tools/check_gate_package.py` (33,441 bytes)
- `gate/tests/test_check_gate_package.py`
- All 36 numbered step files
- All YAML schemas, templates, and examples
- Full `tests/fixtures/` tree (8 fixtures)

### Q2 — Does it include a diff from Gate 5 to Gate 5.1?

**NO. Gap detected.** The file `/Users/syedhaider/Downloads/gate/reports/gate-5-1-upgrade/GATE_5_1_DIFF.patch` exists but contains only 43 bytes of error text:

```
diff: gate/null: No such file or directory
```

This is the stdout of a failed `diff` command — not a real patch. The implementer apparently attempted `diff -ru gate/null gate/...` or similar with a missing source. **A meaningful patch comparing Gate 5 to Gate 5.1 was never produced.**

However, `GATE_5_1_CHANGED_FILES.md` provides a thorough manual file-level summary of what changed. This partially compensates for the missing patch but is not a substitute — there is no machine-applicable reverse patch.

**Implication for rollback:** if Gate 5.1 needs to be reverted, the operator cannot apply `git apply -R GATE_5_1_DIFF.patch` to reconstruct the prior state. They must rely on a separate Gate 5 backup if one exists.

### Q3 — Does it include an executable checker, not only markdown?

**YES.** Path: `/Users/syedhaider/Downloads/gate/tools/check_gate_package.py` (829 lines, real Python 3).

First 30 lines:

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

The script uses standard library (argparse, re, zipfile, pathlib) plus optional PyYAML. It is real Python that I executed and observed exit codes from.

### Q4 — Does it include self-test fixtures?

**YES — 8 fixtures.** Located at `/Users/syedhaider/Downloads/gate/tests/fixtures/`:

| # | Fixture | Files | Purpose |
|---|---|---|---|
| 1 | `blank_exit_code` | 5 | EXIT_CODE: with blank value (M77-P05A failure mode 1) |
| 2 | `post_pass_enoent` | 5 | ENOENT after PASS summary (M77-P05A failure mode 2) |
| 3 | `missing_raw_output` | 5 | Manifest claims file that is absent |
| 4 | `manifest_stale_self_size` | 5 | Manifest lists itself as 0 bytes |
| 5 | `missing_gate_source` | 5 | No gate_used/ or gate_hash.txt |
| 6 | `missing_required_proof_file` | 4 | CYCLE_TRACKER.md absent for Gate Full |
| 7 | `weak_profile` | 2 | GATE_LITE selected for merge verification (advisory; not enforced) |
| 8 | `happy_path_gate_full` | 39 | Minimal valid Gate Full package |

Each fixture (except `weak_profile`) includes a FIXTURE_SPEC.md that documents the scenario and expected result.

### Q5 — Does it include proof that the checker fails known-bad packages?

**YES.** The implementer's `GATE_5_1_SELF_TEST_RESULTS.md` shows 7/7 self-tests pass. I re-ran the suite independently and confirmed 7/7 pass. I also re-ran each bad fixture individually and observed exit code 1 in all 6 cases (see `GATE_5_1_FAILURE_FIX_VERIFICATION.md`).

### Q6 — Does it preserve Gate Lite / Standard / Full / Full+Domain lanes?

**YES.** `GATE_PROFILES.md` (read in full) preserves all four profiles:
- `GATE_LITE` — D0/D1, docs-only, single-line leaf fixes
- `GATE_STANDARD` — D2 normal feature work
- `GATE_FULL` — D2-hot, D3, D4, merge verification
- `GATE_FULL_PLUS_DOMAIN_ADDENDUM` — Full + named domain addenda

The terminal states `GATE_LITE_PASS_HANDOFF_COMPLETE`, `GATE_STANDARD_PASS_HANDOFF_COMPLETE`, and `GATE_FULL_PASS_HANDOFF_COMPLETE` are all present in `TRANSITION_RULES.md`. Profile-specific required-state lists are intact.

`REQUIRED_PROOF_FILES_BY_PROFILE.yaml` defines all four profiles with profile-specific required_always lists. The Gate 5.1 deltas (moving WARNING_OUTPUT_AUDIT and REQUIRED_TEST_SET_EXACTNESS to required_always for GATE_STANDARD; adding GATE_PACKAGE_VALIDATION_REPORT to GATE_FULL) match the documented changes in the handoff.

### Q7 — Does it require proof files to be stored/exported?

**YES — explicitly hardened in Gate 5.1.**

Citation 1, `PROOF_FILE_REQUIREMENTS.md` lines 93–116:

> ## Proof File Export Requirement (Gate 5.1)
>
> **Every required proof file produced by the gate must be physically included in the final exported package.**
>
> A file that exists on the execution host but is absent from the exported zip/directory is NOT acceptable as proof.

Followed by an exhaustive mandatory contents list, ending:

> If any mandatory item is absent from the package: BLOCKING. Not a warning.
>
> The checker script `tools/check_gate_package.py` enforces this mechanically for Gate Full.

Citation 2, `12_PASS_HANDOFF.md` is referenced in the handoff as expanded with comprehensive mandatory list (I did not re-read it in full, but it is in the changed-files list and is an existing file the implementer claimed to update).

### Q8 — Does it require gate_used/ source inclusion?

**YES.** Three independent loci:

1. `PROOF_FILE_REQUIREMENTS.md` lines 78–89:
   > **A local path such as `/Users/.../gate` is NOT proof that gate source was consulted. Include either:**
   > - `gate_used/` — a copy of the gate folder used, OR
   > - `gate_hash.txt` — SHA256 of the gate folder contents plus gate version string

2. `tools/check_gate_package.py` `check_gate_source_included()` (lines 196–206) emits FAIL with this exact text when neither is present:
   > "MISSING: neither gate_used/ directory nor gate_hash.txt found. A local path to /Users/.../gate is NOT proof."

3. The `missing_gate_source` fixture proves this rule is enforced (verified — exit 1).

---

## Gaps surfaced in P00

| # | Gap | Severity | Recommendation |
|---|---|---|---|
| G1 | `GATE_5_1_DIFF.patch` is a 43-byte error message, not a real diff | LOW (documentation) | Note in install decision; not blocking — handoff and CHANGED_FILES.md provide equivalent narrative |
| G2 | `weak_profile` fixture is documented as expected-FAIL but the checker's profile validation is advisory only — it does not detect "this task should have been GATE_FULL but was selected as GATE_LITE" | MEDIUM (acknowledged limitation) | Implementer's handoff already discloses this in "Open questions" item 3. Acceptable for this release if standing rule (P04) compensates |
| G3 | No fixture exists for "stale report contradiction" (failure mode 3 from prompt) | LOW | The rule exists implicitly in `03_EVIDENCE_CONSISTENCY.md` Check 8 (REPORT_AGREEMENT_TABLE), but the executable checker does not cover diff-vs-claim contradiction. Documented as known limitation |

---

## Summary verdict for P00

The package contains everything required EXCEPT a real diff patch. The folder contents, executable checker, fixtures, and proof requirements are all present and verifiable. The missing diff patch is a documentation gap, not a functional gap — the gate works without it.

Proceed to P01 (failure-mode verification) and P02 (executable checker review).
