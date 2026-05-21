# Package Manifest

**Task area:** gate-5-4-known-issue-closure
**Manifest status:** VERIFIED
**Gate profile:** GATE_FULL_PLUS_DOMAIN_ADDENDUM

## Raw Test Outputs

| Artifact ID | File | artifact_type in ledger | EXIT_CODE:0 present? | POST_PASS errors? | Present in package |
|---|---|---|---|---|---|
| E001 | reports/gate-5-4-known-issue-closure/raw_test_output.txt | raw_test_output | YES | NO | YES |

## Required gate artifacts

| File | Present | Verified |
|---|---|---|
| GATE_PROFILE_SELECTION.md | YES | YES |
| FINAL_PACKET_AUDITOR_REPORT.md | YES | YES |
| DOMAIN_ADDENDUM_model_id_validation.md | YES | YES |
| WARNING_OUTPUT_AUDIT.md | YES | YES |
| REQUIRED_TEST_SET_EXACTNESS.md | YES | YES |
| OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md | YES | YES |
| package_file_sizes.txt | YES | YES |
| package_file_hashes.txt | YES | YES |

## Reproducibility artifacts

| File or directory | Present | Verified |
|---|---|---|
| tools/check_gate_package.py | YES | YES |
| tests/test_check_gate_package.py | YES | YES |
| tests/fixtures/ | YES | YES |
| domain_addenda/model_id_validation.md | YES | YES |
