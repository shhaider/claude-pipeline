# Script Spec — check_gate_package

A standalone validation script that an agent or human can run against a gate package directory to verify it is structurally sound before shipping.

This script implements the same checks as `15_FINAL_PACKAGE_AUDIT.md` and `16_CANONICAL_HANDOFF_AUDIT.md` in an automated form. It does not replace the gate steps — it provides a fast pre-check and post-check.

---

## Invocation

```bash
python3 tools/check_gate_package.py <package_path> [--zip <zip_file>]
```

- `<package_path>`: path to the unpacked package directory (e.g., `reports/agentos-ng-governance-fixes/`)
- `--zip <zip_file>`: if provided, also verify the zip contents match the directory

### Output

```
check_gate_package — <package_path>
─────────────────────────────────────────────────────────
[PASS] CURRENT_STATE.yaml present and parseable
[PASS] State is terminal: PASS_HANDOFF_COMPLETE
[PASS] Package manifest: VERIFIED (14/14 files present)
[FAIL] CLAIMS_LEDGER.yaml: 1 HARD_FACT claim has verification_result NOT_IN_PACKAGE
       Claim C003: "e2e_v2 tests ran successfully" — artifact e2e_v2_output.log not in package
[PASS] EVIDENCE_LEDGER.yaml: all 12 included_in_package artifacts verified present
[FAIL] Local-path-only manifest entries: 2 found
       MANIFEST.md line 14: /Users/agent/project/reports/... (not portable)
       MANIFEST.md line 15: /Users/agent/project/reports/... (not portable)
[PASS] STALE_FILE_REGISTER.yaml: 3 stale files, all have HISTORICAL banners
[FAIL] Contradictory handoff status:
       HANDOFF.md → Readiness: PENDING
       CYCLE_TRACKER.md → Final gate verdict: PASS_FOR_HANDOFF
[PASS] Exactly 1 active HANDOFF.md
[FAIL] BLOCKED_HANDOFF.md present without HISTORICAL banner
       Expected: banner at top of file
       Found: no banner

─────────────────────────────────────────────────────────
Result: FAIL
Blockers: 4
Warnings: 0

Fix required before issuing PASS_FOR_HANDOFF:
  1. Include e2e_v2_output.log in package
  2. Replace local paths in MANIFEST.md with relative paths
  3. Update HANDOFF.md Readiness from PENDING to READY
  4. Add HISTORICAL banner to BLOCKED_HANDOFF.md
```

---

## Implementation spec

### Language and dependencies

Python 3.9+, stdlib only (yaml, json, pathlib, zipfile, hashlib, re, sys, argparse).
No pip dependencies.

### File: `tools/check_gate_package.py`

#### Function: `load_current_state(package_path) -> dict`
- Read `CURRENT_STATE.yaml` from package_path
- Parse YAML
- Return dict or raise `CheckError("CURRENT_STATE.yaml missing or unparseable")`

#### Function: `verify_state_is_terminal(state: dict) -> CheckResult`
- `state["current_state"]` must be one of: `PASS_HANDOFF_COMPLETE`, `BLOCKED_HANDOFF_COMPLETE`
- If `gate_completed` is not `true`, fail: "Gate not completed — cannot verify incomplete package"

#### Function: `verify_manifest(package_path, zip_path=None) -> list[CheckResult]`
- Read `PACKAGE_MANIFEST.md`
- Extract file list (parse markdown table rows)
- For each file:
  - If `zip_path`: check via `zipfile.ZipFile(zip_path).namelist()`
  - Else: check via `Path(package_path / filename).exists()`
  - If path starts with any local prefix (`/Users/`, `/home/`, `/tmp/`, `C:\\`): LOCAL_PATH_ONLY fail
  - If file not found: MISSING fail

#### Function: `verify_claims_ledger(package_path, zip_path=None) -> list[CheckResult]`
- Read `CLAIMS_LEDGER.yaml`
- For every claim with `claim_type: HARD_FACT`:
  - Check `evidence_artifact_path` against package contents (same method as manifest)
  - Report `verification_result` for each claim
  - Fail if `verification_result` in (`SOURCE_MISSING`, `NOT_IN_PACKAGE`, `LOCAL_PATH_ONLY`, `SOURCE_CONTRADICTS`)

#### Function: `verify_evidence_ledger(package_path, zip_path=None) -> list[CheckResult]`
- Read `EVIDENCE_LEDGER.yaml`
- For every artifact with `included_in_package: YES`:
  - Check physical presence in package
  - Report `verified_in_package` result

#### Function: `check_local_paths(package_path) -> list[CheckResult]`
- For every `.md` file in package_path:
  - Grep for patterns: `/Users/`, `/home/`, `/tmp/`, `C:\`
  - Report each match as LOCAL_PATH_ONLY warning (not blocker unless in manifest)

#### Function: `verify_stale_file_register(package_path) -> list[CheckResult]`
- Read `STALE_FILE_REGISTER.yaml`
- For every entry with `banner_added: false`:
  - Check if file exists in package
  - If file exists: FAIL — stale file present without HISTORICAL banner
- For every entry with `banner_added: true`:
  - Read the file
  - Check first 10 lines for pattern `STATUS: HISTORICAL`
  - If not found: FAIL — banner_added says true but banner not present in file

#### Function: `verify_handoff_consistency(package_path) -> list[CheckResult]`
- Read CURRENT_STATE.yaml `final_gate_verdict`
- Read HANDOFF.md for readiness status (grep for `Readiness:` or `Final readiness status:`)
- Read CYCLE_TRACKER.md final outcome section
- Check all three agree
- Check BLOCKED_HANDOFF.md:
  - If present and `final_gate_verdict == PASS_FOR_HANDOFF`: check for HISTORICAL banner
  - If present without banner: FAIL

#### Function: `verify_reviewer_reports(package_path) -> list[CheckResult]`
- Required files in final cycle:
  - `COLD_REVIEW_REQUIREMENTS_AUDIT.md` (or `CYCLE{N}_...` for N = max cycle)
  - `COLD_REVIEW_ACTIVE_PROOF_AUDIT.md`
  - `COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md`
  - `COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md`
  - `COLD_REVIEW_ADJUDICATION.md`
- Check each present; FAIL if missing

#### Main

```python
def main():
    args = parse_args()
    results = []
    results += [verify_state_is_terminal(load_current_state(args.package_path))]
    results += verify_manifest(args.package_path, args.zip)
    results += verify_claims_ledger(args.package_path, args.zip)
    results += verify_evidence_ledger(args.package_path, args.zip)
    results += check_local_paths(args.package_path)
    results += verify_stale_file_register(args.package_path)
    results += verify_handoff_consistency(args.package_path)
    results += verify_reviewer_reports(args.package_path)
    
    print_report(results)
    sys.exit(0 if all_pass(results) else 1)
```

Exit 0 = all checks pass. Exit 1 = one or more blockers found.

---

## Usage in the gate

The agent does not need to run this script — it is equivalent to what Steps 15 and 16 perform manually. This script is for:
- Human spot-checks on a finished package
- CI verification after a gate run
- Debugging when a package is suspected of being malformed

The authoritative gate is Steps 15 and 16 as run by the agent. This script is a secondary verifier.

---

## Gate 4.1 — Additional checks

The following checks are added for Gate 4.1 profile-aware validation. Append these functions to `check_gate_package.py`.

### Function: `verify_gate_profile(package_path) -> CheckResult`
- Read `GATE_PROFILE_SELECTION.md` from package_path
- Extract the `gate_profile` from the YAML selector output block
- Verify it is one of: `GATE_LITE`, `GATE_STANDARD`, `GATE_FULL`, `GATE_FULL_PLUS_DOMAIN_ADDENDUM`
- If profile missing or invalid: FAIL — "Gate profile not recorded or invalid in GATE_PROFILE_SELECTION.md"

### Function: `load_required_proof_files(profile) -> list[ProofFileSpec]`
- Read `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`
- Return the list of `required_always` proof files for the given profile
- If YAML not found: raise `CheckError("REQUIRED_PROOF_FILES_BY_PROFILE.yaml missing")`

### Function: `verify_required_proof_files(package_path, profile) -> list[CheckResult]`
- Load required proof files via `load_required_proof_files(profile)`
- For each required file: check physical presence in package_path
- For each NOT_APPLICABLE file: check that `STATE_NAME_NOT_APPLICABLE.md` is present
- FAIL if required file is absent
- FAIL if NOT_APPLICABLE file is absent for a state that should have been skipped

### Function: `verify_manifest_file_sizes(package_path) -> list[CheckResult]`
- Read `package_file_sizes.txt` (generated by `stat`)
- For each file listed in PACKAGE_MANIFEST.md:
  - Check its size in `package_file_sizes.txt`
  - If size is 0 bytes and file is not an intentional placeholder: FAIL — "File listed at 0 bytes: [path]"
- Check the manifest file itself: its listed size must match `stat` size
  - If manifest size is 0 or less than its actual current size: FAIL — "MANIFEST_SELF_SIZE_STALE"

### Function: `verify_manifest_hashes(package_path) -> list[CheckResult]`
- Read `package_file_hashes.txt` (generated by `sha256sum`)
- For GATE_FULL: FAIL if `package_file_hashes.txt` is absent
- For GATE_STANDARD: WARN if `package_file_hashes.txt` is absent

### Function: `verify_final_git_status_proof(package_path) -> CheckResult`
- Search for a file containing `git status --short` output in the package
- Acceptable locations: EVIDENCE_CONSISTENCY_REGISTER.md, CYCLE_TRACKER.md, HANDOFF.md
- FAIL if no `git status --short` output is found anywhere in the package
- FAIL if `git status --short` output shows untracked files but HANDOFF.md claims "clean repo"

### Function: `verify_raw_output_exit_codes(package_path) -> list[CheckResult]`

**Gate 5.1 — strict version. Replaces prior spec.**

Discovery: scan ALL files marked as `artifact_type: raw_test_output` in EVIDENCE_LEDGER.yaml or listed in PACKAGE_MANIFEST.md under "Raw Test Outputs" section. Do NOT scan only `raw/` or `raw_outputs/` directories.

For every discovered raw test output file:
1. Search for lines matching `^EXIT_CODE:\s*\S+\s*$` (any EXIT_CODE line)
2. Collect all matching lines
3. If no EXIT_CODE line found: emit flag `EXIT_CODE_MISSING` — FAIL
4. If exactly one EXIT_CODE line:
   a. Strip prefix `EXIT_CODE:` and whitespace
   b. If remaining value is empty string: emit flag `EXIT_CODE_BLANK` — FAIL
   c. If value is not a digit string: emit flag `EXIT_CODE_NON_NUMERIC` — FAIL
   d. If value is `0`: PASS
   e. Otherwise: emit flag `EXIT_CODE_NONZERO` — FAIL
5. If multiple EXIT_CODE lines:
   a. If all have value `0`: PASS
   b. Otherwise: emit flag `EXIT_CODE_CONFLICTING` — FAIL

### Function: `verify_post_pass_uncaught_errors(package_path) -> list[CheckResult]`

**Gate 5.1 — new function.**

Discovery: same as verify_raw_output_exit_codes — use manifest/ledger, not directory scan.

For every raw test output file:
1. Find the line number of the last PASS summary line (matches: `PASS `, `Tests: .* passed`, `✓ .* passing`, `All tests passed`)
2. If no PASS summary line found: skip (no PASS to be after)
3. Scan all lines AFTER the PASS summary line for blocking patterns:
   - `Error:` (line starts with or contains `Error:`)
   - `ENOENT`
   - `UnhandledPromiseRejection`
   - `uncaughtException`
   - `Jest did not exit`
   - Lines starting with `    at ` (stack trace frames)
4. If any blocking pattern found after PASS: emit flag `POST_PASS_UNCAUGHT_ERROR` — FAIL
5. If no blocking patterns after PASS: PASS

### Function: `verify_raw_outputs_in_manifest(package_path) -> list[CheckResult]`

**Gate 5.1 — new function.**

For every file in the package that could be a raw test output (heuristic: files containing `EXIT_CODE:` or `Tests:` lines):
1. Check if the file is listed in EVIDENCE_LEDGER.yaml with `artifact_type: raw_test_output`
2. OR listed in PACKAGE_MANIFEST.md "Raw Test Outputs" section
3. If not listed in either: emit WARNING for GATE_STANDARD, FAIL for GATE_FULL

### Function: `verify_package_listing_from_export(package_path, zip_path=None) -> list[CheckResult]`
- Find any file claiming to be a "package file listing" or "PACKAGE_FILE_LISTING"
- Verify it was generated from `zipinfo -1 <zip>` or `tar -tzf` (not from local `find`)
- FAIL if listing contains absolute local paths (`/Users/`, `/home/`)

### Function: `verify_gate_source_included(package_path) -> CheckResult`
- Check for presence of `gate_used/` folder or equivalent in the package
- For GATE_FULL: FAIL if gate source folder is missing
- For GATE_STANDARD: WARN if gate source folder is missing

### Function: `verify_local_only_gate_paths(package_path) -> list[CheckResult]`
- Scan all CURRENT_STATE.yaml, GATE_PROFILE_SELECTION.md, and any file claiming a gate source path
- FAIL if any gate source path starts with `/Users/`, `/home/`, or `C:\` — these are local-only paths
- This catches the failure where an agent reads gate files from its local machine but claims they are from the package

### Function: `verify_next_prompt_decision_for_d2plus(package_path, risk_tier) -> CheckResult`
- If risk_tier is D2, D2-hot, D3, or D4:
  - Check for presence of `NEXT_PROMPT_DECISION.md` in package
  - FAIL if absent: "NEXT_PROMPT_DECISION.md required for D2+ tasks but not found"
- If risk_tier is D0 or D1: skip this check

### Updated main function (Gate 5.1)

```python
def main():
    args = parse_args()
    results = []
    
    # Existing checks
    results += [verify_state_is_terminal(load_current_state(args.package_path))]
    results += verify_manifest(args.package_path, args.zip)
    results += verify_claims_ledger(args.package_path, args.zip)
    results += verify_evidence_ledger(args.package_path, args.zip)
    results += check_local_paths(args.package_path)
    results += verify_stale_file_register(args.package_path)
    results += verify_handoff_consistency(args.package_path)
    results += verify_reviewer_reports(args.package_path)
    
    # Gate 4.1 additional checks
    profile = verify_gate_profile(args.package_path)
    results += [profile]
    if profile.passed:
        results += verify_required_proof_files(args.package_path, profile.value)
    results += verify_manifest_file_sizes(args.package_path)
    results += verify_manifest_hashes(args.package_path)
    results += [verify_final_git_status_proof(args.package_path)]
    results += verify_package_listing_from_export(args.package_path, args.zip)
    results += [verify_gate_source_included(args.package_path)]
    results += verify_local_only_gate_paths(args.package_path)
    
    state = load_current_state(args.package_path)
    risk_tier = state.get('risk_tier', 'D2')
    results += [verify_next_prompt_decision_for_d2plus(args.package_path, risk_tier)]
    
    # Gate 5.1 additional checks
    results += verify_raw_output_exit_codes(args.package_path)         # strict EXIT_CODE validation
    results += verify_post_pass_uncaught_errors(args.package_path)      # POST_PASS_UNCAUGHT_ERROR
    results += verify_raw_outputs_in_manifest(args.package_path)        # manifest-driven discovery
    
    print_report(results)
    sys.exit(0 if all_pass(results) else 1)
```
