# Gate 5.3 Acceptance — Targeted Fixture Verification (P04)

The audit ran `tools/check_gate_package.py` against 14 fixtures (8 new Gate 5.3
fixtures + 6 R1 regression fixtures). Each invocation captured the true exit code via
direct `$?` inspection (NOT through a piped `tail` which masks the real exit code).

Common command shape:
```
cd /Users/syedhaider/Downloads/gate && \
python3 tools/check_gate_package.py \
  --package "tests/fixtures/<FIXTURE>" \
  --profile <PROFILE> \
  --task-area "<FIXTURE>" \
  --gate-dir /Users/syedhaider/Downloads/gate \
  --risk-tier <TIER> \
  --task-kind <KIND> \
  [--final]
```

## Results table

| # | Fixture | Profile | --final | Risk | Kind | Expected exit | Observed exit | Key flag / output | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `final_auditor_missing` | GATE_FULL | yes | D3 | merge_verification | 1 (FAIL) | 1 | `FINAL_PACKET_AUDITOR_MISSING: reports/final_auditor_missing/FINAL_PACKET_AUDITOR_REPORT.md not found` | PASS |
| 2 | `final_auditor_pass` | GATE_FULL | yes | D3 | merge_verification | 0 (PASS) | 0 | `Result: PASS  Checks passed: 47  Checks failed: 0` | PASS |
| 3 | `final_auditor_fail` | GATE_FULL | yes | D3 | merge_verification | 1 (FAIL) | 1 | `FINAL_PACKET_AUDITOR_FAIL: auditor verdict is FAIL` | PASS |
| 4 | `final_auditor_human_decision_but_ready_status` | GATE_FULL | yes | D3 | merge_verification | 1 (FAIL) | 1 | `FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED: verdict is HUMAN_DECISION_REQUIRED but handoff does not declare a blocked/human-decision status` | PASS |
| 5 | `final_auditor_schema_invalid` | GATE_FULL | yes | D3 | merge_verification | 1 (FAIL) | 1 | `FINAL_PACKET_AUDITOR_SCHEMA_INVALID: missing fields ['RERUN_FROM:']` | PASS |
| 6 | `final_auditor_beginning_rerun_but_pass_handoff` | GATE_FULL | yes | D3 | merge_verification | 1 (FAIL) | 1 | `FINAL_PACKET_AUDITOR_RERUN_REQUIRED: RERUN_FROM is BEGINNING but final status claims READY/MERGED/VERIFIED` | PASS |
| 7 | `final_auditor_not_applicable_lite` | GATE_LITE | no | D0 | docs | 0 (PASS) | 0 | `Result: PASS  Checks passed: 33  Checks failed: 0` | PASS |
| 8 | `final_auditor_not_applicable_full` | GATE_FULL | yes | D3 | merge_verification | 1 (FAIL) | 1 | `FINAL_PACKET_AUDITOR_MISSING: reports/final_auditor_not_applicable_full/FINAL_PACKET_AUDITOR_REPORT.md not found` | PASS |
| 9 | `happy_path_gate_full` | GATE_FULL | yes | D3 | merge_verification | 0 (PASS) | 0 | `Result: PASS  Checks passed: 47  Checks failed: 0` | PASS |
| 10 | `blank_exit_code` | GATE_FULL | no | D3 | merge_verification | 1 (FAIL) | 1 | `EXIT_CODE_BLANK: ... EXIT_CODE line is blank` + `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` | PASS |
| 11 | `post_pass_enoent` | GATE_FULL | no | D3 | merge_verification | 1 (FAIL) | 1 | `POST_PASS_UNCAUGHT_ERROR: ... post-PASS error found: Error:` | PASS |
| 12 | `output_contract_structured_fail` | GATE_FULL | no | D3 | merge_verification | 1 (FAIL) | 1 | `STALE_MILESTONE_LABEL: structured verdict is FAIL; findings=['STALE_MILESTONE_LABEL']` | PASS |
| 13 | `lite_profile_missing_risk_task` | GATE_LITE | no | (omitted) | (omitted) | 1 (FAIL) | 1 | `MISSING_RISK_TIER` + `MISSING_TASK_KIND` + multiple required-proof-file misses | PASS |
| 14 | `absolute_raw_output_outside_package` | GATE_FULL | no | D3 | merge_verification | 1 (FAIL) | 1 | `HOST_PATH_NOT_PACKAGE_EVIDENCE: /tmp/...txt declared via evidence_ledger but path is absolute and resolves outside the package` | PASS |

## Summary

**14/14 PASS.** Every fixture's observed exit code matches expected. Every fixture's
key flag matches the documented behavior:

- All 5 Gate 5.3 final-auditor flags are emitted by their respective fixtures
  (MISSING #1, FAIL #3, HUMAN_DECISION_REQUIRED #4, SCHEMA_INVALID #5,
  RERUN_REQUIRED #6).
- Happy paths (#2 final_auditor_pass, #7 final_auditor_not_applicable_lite,
  #9 happy_path_gate_full) all return Result: PASS, exit 0.
- All 5 R1-regression fixtures (#10–#14) still emit their R1-era flags correctly:
  EXIT_CODE_BLANK, POST_PASS_UNCAUGHT_ERROR, output-contract structured-FAIL,
  MISSING_RISK_TIER + MISSING_TASK_KIND, HOST_PATH_NOT_PACKAGE_EVIDENCE.

## Note: exit-code capture method

The checker prints "Blocking issues:" and a result block, then writes a
GATE_PACKAGE_VALIDATION_REPORT.md, then `sys.exit(0 if failed == 0 else 1)`. Earlier
runs that piped output through `tail` masked the python exit code with `tail`'s exit
code (always 0). Re-run with direct `>/tmp/log; echo $?` produced the true exit codes
listed above, all matching expected.
