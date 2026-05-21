# Gate 5.4 Explicit Fixture Verification

- `final_auditor_pass`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `0`
  - Expected outcome observed: `PASS`
- `final_auditor_fail`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `1`
  - Expected blocking flag observed: `FINAL_PACKET_AUDITOR_FAIL`
- `final_auditor_schema_invalid`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `1`
  - Expected blocking flag observed: `FINAL_PACKET_AUDITOR_SCHEMA_INVALID`
- `exit_code_conflicting`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `1`
  - Expected blocking flag observed: `EXIT_CODE_CONFLICTING`
- `exit_code_non_numeric`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `1`
  - Expected blocking flag observed: `EXIT_CODE_NON_NUMERIC`
- `exit_code_fenced_only`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `1`
  - Expected blocking flag observed: `EXIT_CODE_MISSING`
- `exit_code_fenced_conflicting_bare_zero`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `0`
  - Expected outcome observed: fenced `EXIT_CODE:1` ignored, bare `EXIT_CODE:0` accepted
- `gate_full_plus_domain_addendum_pass`
  - Command profile context: `GATE_FULL_PLUS_DOMAIN_ADDENDUM / D4 / gate_change`
  - Exit code: `0`
  - Expected outcome observed: `PASS`
- `gate_full_plus_missing_full_required_proof`
  - Command profile context: `GATE_FULL_PLUS_DOMAIN_ADDENDUM / D4 / gate_change`
  - Exit code: `1`
  - Expected blocking flag observed: `REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING`
  - Purpose: proves Full Plus inherits normal `GATE_FULL.required_always` files, not only `required_always_additional`.
- `gate_full_plus_missing_domain_addendum_proof`
  - Command profile context: `GATE_FULL_PLUS_DOMAIN_ADDENDUM / D4 / gate_change`
  - Exit code: `1`
  - Expected blocking flag observed: `DOMAIN_ADDENDUM_PROOF_MISSING`
- `warning_audit_structured_fail`
  - Command profile context: `GATE_FULL / D3 / merge_verification`
  - Exit code: `1`
  - Expected blocking flag observed: `POST_PASS_UNCAUGHT_ERROR`
- `not_applicable_placeholder_reason`
  - Command profile context: `GATE_STANDARD / D2 / normal_impl`
  - Exit code: `1`
  - Expected blocking flag observed: `NOT_APPLICABLE_REASON_MISSING`

Notes:

- Some negative fixtures also fail secondary checks such as missing final-auditor schema when that surface is intentionally absent in the fixture. Those secondary failures do not weaken the primary regression signal above.
- The explicit fixture commands were run with each fixture's own declared profile/risk/task context to avoid profile-selection noise.
- Corrective export verification requires both signout zips to include `tests/fixtures/` and a clean-unzipped package to run `python3 tests/test_check_gate_package.py` successfully.

## Corrective Export Verification

- `unzip -l /Users/syedhaider/Downloads/GATE_5_4_KNOWN_ISSUE_CLOSURE_SIGNOUT.zip | grep 'tests/fixtures'`
  - Exit code: `0`
  - Fixture entries found: `2459`
- `unzip -l /Users/syedhaider/Downloads/GATE_5_4_KNOWN_ISSUE_CLOSURE_SIGNOUT_FLAT.zip | grep 'tests/fixtures'`
  - Exit code: `0`
  - Fixture entries found: `2459`
- Clean export test:
  - Commands: `rm -rf /tmp/gate54_export_check && mkdir -p /tmp/gate54_export_check && unzip -q /Users/syedhaider/Downloads/GATE_5_4_KNOWN_ISSUE_CLOSURE_SIGNOUT_FLAT.zip -d /tmp/gate54_export_check && cd /tmp/gate54_export_check && python3 tests/test_check_gate_package.py`
  - Exit code: `0`
  - Result: `66 passed, 0 failed`
- Clean export final gate:
  - Command: `python3 tools/check_gate_package.py --package . --task-area gate-5-4-known-issue-closure --gate-dir . --profile GATE_FULL_PLUS_DOMAIN_ADDENDUM --risk-tier D4 --task-kind gate_change --final`
  - Exit code: `0`
  - Result: `PASS`, `47` checks passed, `0` failed
- Direct zip final gate:
  - `/Users/syedhaider/Downloads/GATE_5_4_KNOWN_ISSUE_CLOSURE_SIGNOUT.zip`: exit code `0`, result `PASS`
  - `/Users/syedhaider/Downloads/GATE_5_4_KNOWN_ISSUE_CLOSURE_SIGNOUT_FLAT.zip`: exit code `0`, result `PASS`
