# Gate 5.1 Failure-Mode Verification — P01

**Auditor:** independent gate auditor
**Date:** 2026-05-01
**Method:** Re-ran the Gate 5.1 executable checker against each named bad fixture from a clean shell. Exit codes captured directly. Output text inspected for required flags.

---

## Self-test re-run (independent)

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

**Exit code: 0. 7/7 tests pass.** Confirms implementer's claim.

---

## Happy-path sanity check (must pass)

Command:
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/happy_path_gate_full \
  --profile GATE_FULL \
  --task-area audit_happy_path \
  --gate-dir /Users/syedhaider/Downloads/gate
```

Result: `Result: PASS / Checks passed: 42  |  Checks failed: 0`. **Exit code: 0.**

This is critical — proves the checker isn't a false-positive engine. A clean Gate Full package passes.

---

## Failure-mode-by-failure-mode results

### Failure mode 1 — Blank EXIT_CODE

**Fixture:** `tests/fixtures/blank_exit_code/`
**Raw output content (verbatim):**
```
PASS tests/foo.test.js
Tests: 3 passed, 3 total
Snapshots: 0 total
Time: 1.4 s
Ran all test suites.
EXIT_CODE:
```

**Command:**
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/blank_exit_code \
  --profile GATE_FULL \
  --task-area audit_blank_exit_code \
  --gate-dir /Users/syedhaider/Downloads/gate
```

**Exit code:** 1 (FAIL)

**Key output line:**
```
[FAIL] exit_code_strict [EXIT_CODE_BLANK]: raw_test_output.txt: EXIT_CODE line found but value is blank (EXIT_CODE:)
```

**Verdict:** PASS — flag `EXIT_CODE_BLANK` emitted exactly as required. The exact M77-P05A failure mode is mechanically caught.

---

### Failure mode 2 — Post-PASS Jest error (ENOENT)

**Fixture:** `tests/fixtures/post_pass_enoent/`
**Raw output content (verbatim):**
```
PASS tests/foo.test.js
Tests: 3 passed, 3 total
Snapshots: 0 total
Time: 2.1 s, estimated 2 s
Ran all test suites.
EXIT_CODE:0

Error: ENOENT: no such file or directory, open '/tmp/jest_rs/perf-cache-abc123'
    at Object.openSync (node:fs:596:3)
    at Object.writeFileSync (node:fs:2248:35)
    at JestCache.saveResults (/node_modules/jest-runner/build/runTest.js:482:19)
```

**Exit code:** 1 (FAIL)

**Key output line:**
```
[FAIL] post_pass_uncaught_errors [POST_PASS_UNCAUGHT_ERROR]: raw_test_output.txt: error(s) found after PASS summary. First: 'Error:'
```

**Verdict:** PASS — flag `POST_PASS_UNCAUGHT_ERROR` emitted. Note that `EXIT_CODE:0` itself is correct in this fixture (so EXIT_CODE check passes), but the post-PASS scan catches the trailing error. This isolates the two failure modes correctly.

---

### Failure mode 3 — Stale report contradiction

This is the "runtime-scope report names stale milestone labels that contradict source/tests/diff" scenario.

**No fixture exists. No specific executable check covers this case.**

I searched `01_EVIDENCE_ADEQUACY.md`, `03_EVIDENCE_CONSISTENCY.md`, and `EVIDENCE_LEDGER_TEMPLATE.yaml` for relevant rules:

- `03_EVIDENCE_CONSISTENCY.md` Check 8 — REPORT_AGREEMENT_TABLE — defines a manual cross-document reconciliation pass (handoff vs. manifest vs. gate report etc.). It addresses agreement on HEAD SHA, files changed, test counts. But it does not specifically check that report-level milestone labels (e.g., "this is M77-P05") match what the diff actually contains.
- `03_EVIDENCE_CONSISTENCY.md` Check 6 — STALE_LANGUAGE_TABLE — is the closest relevant rule. It greps for "stale", "superseded", "TODO", "TBD", and other staleness markers in the reports/ directory. This is prose-driven, not executable.

**Verdict: UNCERTAIN.**

- The rule is implicit in evidence consistency (Check 6 + Check 8) but is not mechanically enforced by `check_gate_package.py`.
- This is not strictly a regression vs. Gate 5 — Gate 5 also did not have a mechanical check for this.
- It represents a known limitation, not a broken Gate 5.1.

**Recommendation:** Document this as a known limitation in the install decision. Do not block acceptance over it.

---

### Failure mode 4 — Missing required proof file

**Fixture:** `tests/fixtures/missing_required_proof_file/`
**Contents:** Has `EVIDENCE_LEDGER.yaml`, `FIXTURE_SPEC.md`, `GATE_PROFILE_SELECTION.md`, but missing CYCLE_TRACKER.md and most other required-for-GATE_FULL files.

**Exit code:** 1 (FAIL)

**Key output lines (excerpt):**
```
[FAIL] required_proof_files: MISSING: CURRENT_STATE.yaml (required for GATE_FULL)
[FAIL] required_proof_files: MISSING: CYCLE_TRACKER.md (required for GATE_FULL)
[FAIL] required_proof_files: MISSING: CLAIMS_LEDGER.yaml (required for GATE_FULL)
...
```

**Verdict:** PASS — checker correctly flags every absent required proof file individually. The fixture's stated "CYCLE_TRACKER.md absent" is detected, plus 20+ other missing required files.

---

### Failure mode 5 — Manifest stale self-size

**Fixture:** `tests/fixtures/manifest_stale_self_size/`
**PACKAGE_MANIFEST.md content (relevant row):**
```
| PACKAGE_MANIFEST.md | 0 bytes | (not computed) |
```

Actual file size: 666 bytes.

**Exit code:** 1 (FAIL)

**Key output line:**
```
[FAIL] manifest_self_size: PACKAGE_MANIFEST.md: manifest lists itself as 0 bytes (actual: 666 bytes) — MANIFEST_SELF_SIZE_STALE
```

**Verdict:** PASS — `MANIFEST_SELF_SIZE_STALE` flag emitted as required.

---

### Failure mode 6 — Wrong gate profile (Lite when Full required)

**Fixture:** `tests/fixtures/weak_profile/`
**Contents:** Has only `FIXTURE_SPEC.md` and `GATE_PROFILE_SELECTION.md`. The fixture spec states the scenario is "GATE_LITE selected for merge verification."

**Command (using GATE_LITE, mimicking the agent's wrong choice):**
```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/weak_profile \
  --profile GATE_LITE \
  --task-area audit_weak \
  --gate-dir /Users/syedhaider/Downloads/gate
```

**Exit code:** 1 (FAIL) — but for the wrong reason.

**What actually fails:** The fixture is missing required GATE_LITE proof files (CYCLE_TRACKER.md, CLAIMS_LEDGER.yaml, all five cold review reports, etc.), so the checker fails on `required_proof_files`. **It does not specifically detect the "GATE_LITE chosen for merge verification" escalation violation.**

**Verdict:** UNCERTAIN with documented limitation.

The fixture exits 1 incidentally, not because the checker validates the profile-selection-vs-task-class match. The implementer's handoff explicitly discloses this (Open questions item 3):

> The `weak_profile` fixture (Fixture 5) was created but the checker does not yet enforce profile escalation triggers (e.g., rejecting GATE_LITE for merge verification). This would require parsing the task prompt or GATE_PROFILE_SELECTION.md for escalation triggers. Current check only verifies profile is a valid value.

**This is a real gap, not a regression.** Gate 5 also did not have automated profile-selection validation. The standing rule in P04 (independent reviewer-driven profile selection before implementer starts) is the compensating control.

**Recommendation:** Accept Gate 5.1 with this limitation noted. Do not represent the `weak_profile` fixture as proof of profile-escalation enforcement in any handoff.

---

### Failure mode 7 — File on VPS but not in exported package

This is the "package-export gap" — a file produced during execution but absent from the final zip/directory.

The checker's `check_required_proof_files` and `check_gate_source_included` cover this — they scan the actual package contents (not any external host). The `missing_required_proof_file` fixture and `missing_gate_source` fixture both exercise this rule.

**Independent verification:**

Fixture `missing_gate_source/` has no `gate_used/` directory and no `gate_hash.txt` file.

```bash
python3 tools/check_gate_package.py \
  --package tests/fixtures/missing_gate_source \
  --profile GATE_FULL \
  --task-area audit_missing_gate_source \
  --gate-dir /Users/syedhaider/Downloads/gate
```

**Exit code:** 1 (FAIL)

**Key output line:**
```
[FAIL] gate_source_included: MISSING: neither gate_used/ directory nor gate_hash.txt found. A local path to /Users/.../gate is NOT proof.
```

**Verdict:** PASS — the export-vs-host distinction is enforced. Files on the host that aren't in the package fail the checker.

---

## Failure-mode summary table

| # | Failure mode | Verdict | Evidence |
|---|---|---|---|
| 1 | Blank EXIT_CODE | PASS | exit 1, flag `EXIT_CODE_BLANK` emitted on `blank_exit_code` fixture |
| 2 | Post-PASS Jest error (ENOENT) | PASS | exit 1, flag `POST_PASS_UNCAUGHT_ERROR` emitted on `post_pass_enoent` fixture |
| 3 | Stale report contradiction | UNCERTAIN | No specific executable check; implicit in `03_EVIDENCE_CONSISTENCY.md` Checks 6 & 8 (manual review). Documented limitation. Not a Gate 5.1 regression. |
| 4 | Missing required proof file | PASS | exit 1, multiple `MISSING: ...` lines emitted on `missing_required_proof_file` fixture |
| 5 | Manifest stale self-size | PASS | exit 1, flag `MANIFEST_SELF_SIZE_STALE` emitted on `manifest_stale_self_size` fixture |
| 6 | Wrong gate profile (Lite when Full required) | UNCERTAIN | Fixture exits 1 but for missing files, not profile validation. Implementer disclosed gap. Not enforced by checker. |
| 7 | File on host but not in exported package | PASS | exit 1, flags emitted on `missing_required_proof_file` and `missing_gate_source` fixtures |

**Score: 5 PASS, 2 UNCERTAIN, 0 FAIL.**

---

## Self-test results (independent re-run)

7/7 self-tests pass. Exit 0. Matches implementer's claim verbatim.

---

## Required corrections

None blocking. The two UNCERTAINs are pre-existing limitations that Gate 5 also had, explicitly disclosed by the implementer, and compensated by the standing rule in P04 and the manual evidence-consistency checks.

If the operator wants to close the UNCERTAIN gaps in a future Gate 5.2:

- For mode 3 (stale report contradiction): add a `check_diff_vs_claim_consistency()` function that cross-references `git diff [base]..[HEAD] --name-only` against milestone labels in handoff/manifest. This requires a `git_diff.txt` artifact in the package.
- For mode 6 (weak profile): add a `check_profile_selection_validity()` function that parses GATE_PROFILE_SELECTION.md for "task type" and validates it against the escalation-trigger table from `GATE_PROFILE_SELECTOR.md`.

These are not required for accepting Gate 5.1.
