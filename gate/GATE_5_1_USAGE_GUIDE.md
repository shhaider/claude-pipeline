# Gate 5.1 Usage Guide

This guide documents what changed in Gate 5.1 and how to use the new executable checker.
Read `GATE_4_1_USAGE_GUIDE.md` for the full profile selection guide (it still applies).

---

## What changed in Gate 5.1 vs Gate 4.1

### 1. EXIT_CODE enforcement is now strict and exhaustive

Gate 4.1 defined `EXIT_CODE_MISSING` but did not cover:
- `EXIT_CODE_BLANK` — `EXIT_CODE:` present but no value (e.g., blank PIPESTATUS)
- `EXIT_CODE_NON_NUMERIC` — non-numeric value
- `EXIT_CODE_CONFLICTING` — multiple EXIT_CODE lines with different values
- `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` — value in handoff but absent from raw output

Gate 5.1 defines all six flags. All are BLOCKING. None may be classified `EXPECTED_NON_BLOCKING`.

The exact required pattern is: `^EXIT_CODE:0\s*$`

### 2. Post-PASS uncaught error detection is now a named blocking flag

Gate 4.1 had a `post-pass error?` column in the RAW_TEST_OUTPUT_TABLE but no defined flag.
Reviewers could classify a post-PASS `ENOENT` as `REQUIRES_FOLLOWUP` (non-blocking).

Gate 5.1 adds `POST_PASS_UNCAUGHT_ERROR` as a distinct BLOCKING flag. Any `Error:`, `ENOENT`,
`UnhandledPromiseRejection`, `uncaughtException`, `Jest did not exit`, or stack trace line
appearing AFTER a PASS summary line is BLOCKING unless the package provides explicit
evidence-backed justification.

### 3. An executable checker now exists

Gate 4.1 had `SCRIPT_SPEC_check_gate_package.md` — a specification document only.
Gate 5.1 ships `tools/check_gate_package.py` — a working Python 3 script.

Gate Full cannot pass unless the checker exits 0. The checker report must be included in
the exported package.

### 4. Raw output discovery is manifest-driven

Gate 4.1 scanners scanned directories named `raw/` or `raw_outputs/`. If a raw output was
stored elsewhere, it was not scanned.

Gate 5.1 requires all raw test outputs to be registered in EVIDENCE_LEDGER.yaml with
`artifact_type: raw_test_output` or listed in PACKAGE_MANIFEST.md "Raw Test Outputs" section.
The checker scans ALL registered files regardless of directory or filename.

### 5. Pre-PASS barrier is now explicit

Gate 4.1 required "all required states recorded" but did not prevent issuing PASS while
required states were recorded as FAIL.

Gate 5.1 adds an explicit pre-PASS barrier in `10_GATE_VERDICT.md` and `15_FINAL_PACKAGE_AUDIT.md`:
PASS cannot be issued while any required audit state is FAIL/BLOCKING/UNCERTAIN/missing.

### 6. Proof files must be exported (not just produced locally)

Gate 5.1 makes explicit that every required proof file must be physically included in the
exported package. A local path to `/Users/.../gate` is not acceptable as proof of gate
source. Include `gate_used/` or `gate_hash.txt`.

### 7. GATE_STANDARD now explicitly requires WARNING_OUTPUT_AUDIT and REQUIRED_TEST_SET_EXACTNESS

Gate 4.1 listed these as `required_conditional` for GATE_STANDARD. Gate 5.1 moves them
to `required_always` to match the prose in GATE_PROFILES.md (which already said YES for
GATE_STANDARD). If no raw outputs are present, produce `_NOT_APPLICABLE.md` files.

---

## When to use each profile

### GATE_LITE

Use for:
- Documentation-only changes (D0)
- Single-line isolated fixes in non-hot leaf modules (D1)
- No downstream impact, no migration, no exports

**Do NOT use for merge verification, hot files, migrations, or any live-behavior claim.**

### GATE_STANDARD

Use for:
- Normal D2 implementation slices
- New features in non-hot modules
- Test coverage improvements

Requires: Warning Output Audit, Required Test Set Exactness, Export Channel Audit,
Diff Base/Scope Audit, Next Prompt Decision, package_file_sizes.txt.

### GATE_FULL

**Required for:**
- Merge verification
- Package signout / final handoffs
- Hot file touches (D2-hot)
- Migrations, runtime state, gate logic (D3)
- Provider/model routing, cross-system evidence (D4)
- Any claim of "live behavior fixed"
- Multi-agent coordination on shared files
- Gate cycle count reached 3+ in a prior attempt

Additional requirements beyond GATE_STANDARD:
- All GATE_STANDARD files
- `package_file_hashes.txt`
- `GATE_EFFECTIVENESS_LOG.md`
- `GATE_PACKAGE_VALIDATION_REPORT.md` (from checker)
- `gate_used/` or `gate_hash.txt`

### GATE_FULL_PLUS_DOMAIN_ADDENDUM

Same as GATE_FULL plus named domain addenda (model ID validation, data boundary, etc.).

---

## How to run the checker

### Basic usage

```bash
python3 /Users/syedhaider/Downloads/gate/tools/check_gate_package.py \
    --package /path/to/your/export-package/ \
    --profile GATE_FULL \
    --task-area m77 \
    --gate-dir /Users/syedhaider/Downloads/gate
```

### With a zip package

```bash
python3 /Users/syedhaider/Downloads/gate/tools/check_gate_package.py \
    --package /path/to/package.zip \
    --profile GATE_FULL \
    --task-area m77
```

### What the checker validates

- Required proof files for the selected profile (from REQUIRED_PROOF_FILES_BY_PROFILE.yaml)
- Gate source proof: `gate_used/` or `gate_hash.txt` present
- EXIT_CODE: strict validation on all registered raw test outputs
- Post-PASS uncaught error detection on all raw test outputs
- package_file_sizes.txt and package_file_hashes.txt (Gate Full)
- Manifest self-size (not 0, within 10% of actual)
- Final git status proof file
- REQUIRED_TEST_SET_EXACTNESS.md (no FAIL verdicts)
- WARNING_OUTPUT_AUDIT.md (no BLOCKING findings)
- GATE_PACKAGE_VALIDATION_REPORT.md (skips on first run — circular dep)

### What to do if checker exits nonzero

Fix all reported failures internally and rerun the checker before returning PASS.

**Never return PASS if the checker exits nonzero.** The checker is a hard gate for Gate Full.

---

## Registering raw test outputs (required for Gate 5.1 checks)

In EVIDENCE_LEDGER.yaml, mark each raw test output:

```yaml
artifacts:
  - artifact_id: E001
    artifact_filename: "jest_output.txt"
    artifact_type: raw_test_output   # <-- required for Gate 5.1 scanning
    created_by_command: "npx jest tests/foo.test.js 2>&1 | tee jest_output.txt; echo EXIT_CODE:$? >> jest_output.txt"
    included_in_package: YES
```

In PACKAGE_MANIFEST.md, include a "Raw Test Outputs" section:

```markdown
## Raw Test Outputs

| Artifact ID | File | artifact_type in ledger | EXIT_CODE:0 present? | POST_PASS errors? | Present in package |
|---|---|---|---|---|---|
| E001 | jest_output.txt | raw_test_output | YES | NO | YES |
```

---

## Capturing clean EXIT_CODE

The recommended capture pattern:

```bash
npx jest tests/foo.test.js 2>&1 | tee raw_output.txt
echo "EXIT_CODE:$?" >> raw_output.txt
```

This appends `EXIT_CODE:0` (or `EXIT_CODE:1`) as the final line of the raw output file.

**Important:** Capture `$?` IMMEDIATELY after the test command. Any intermediate command
between the test run and `echo EXIT_CODE:$?` will overwrite `$?`.

---

## Prompt snippet for operators

Include this in any task prompt that requires Gate Full verification:

```
Gate requirement (Gate 5.1):
Run the gate using GATE_FULL. Include gate_used/ or gate_hash.txt, all required
proof files, raw test outputs registered in EVIDENCE_LEDGER.yaml with
artifact_type: raw_test_output, WARNING_OUTPUT_AUDIT.md, REQUIRED_TEST_SET_EXACTNESS.md
(with EXIT_CODE parsed column), package_file_sizes.txt, package_file_hashes.txt, and
GATE_PACKAGE_VALIDATION_REPORT.md.

Run:
  python3 /Users/syedhaider/Downloads/gate/tools/check_gate_package.py \
    --package <your-export-package-folder> \
    --profile GATE_FULL \
    --task-area <task_area> \
    --gate-dir /Users/syedhaider/Downloads/gate

If check_gate_package exits nonzero, fix internally and rerun before returning PASS.
Raw outputs must end with EXIT_CODE:0 (exact match: ^EXIT_CODE:0\s*$).
No post-PASS uncaught errors permitted.
```

---

## Known limitations of the checker

1. **GATE_PACKAGE_VALIDATION_REPORT.md circular dependency**: The checker skips validating
   its own report on the first run. After the first run, include the report in the package,
   then rerun the checker to verify the report is present.

2. **YAML parsing fallback**: If PyYAML is not installed, the checker skips some checks
   and emits a warning. Install PyYAML: `pip3 install pyyaml`.

3. **NOT_APPLICABLE files**: The checker only warns (does not fail) when NOT_APPLICABLE
   files are absent. This is by design — the checker cannot determine if a state should
   have been NOT_APPLICABLE without domain knowledge.

4. **Manifest self-size pattern matching**: The self-size check uses regex patterns to
   find self-referential size entries. If the manifest uses an unusual format, the check
   may not detect the self-size entry.

5. **YAML string vs boolean**: EVIDENCE_LEDGER.yaml `included_in_package` can be either
   `YES` (string) or `true` (boolean). The checker handles both.

---

## Self-test fixtures

The gate includes 7 self-test fixtures in `tests/fixtures/`:

| Fixture | Expected result | Failure mode exercised |
|---|---|---|
| `blank_exit_code` | FAIL: EXIT_CODE_BLANK | M77-P05A exact failure mode |
| `post_pass_enoent` | FAIL: POST_PASS_UNCAUGHT_ERROR | M77-P05A ENOENT failure mode |
| `missing_raw_output` | FAIL | Manifest claims file that is absent |
| `manifest_stale_self_size` | FAIL | Manifest lists itself as 0 bytes |
| `missing_gate_source` | FAIL | No gate_used/ or gate_hash.txt |
| `missing_required_proof_file` | FAIL | CYCLE_TRACKER.md absent for Gate Full |
| `happy_path_gate_full` | PASS | Minimal valid Gate Full package |

Run self-tests:
```bash
cd /Users/syedhaider/Downloads/gate && python3 tests/test_check_gate_package.py
```
