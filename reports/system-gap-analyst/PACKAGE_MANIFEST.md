# Package Manifest

**Task area:** system-gap-analyst
**Manifest status:** VERIFIED
**Gate profile:** GATE_FULL_PLUS_DOMAIN_ADDENDUM
**Risk tier:** D2_HOT
**Task kind:** provider_model_routing

## Raw Test Outputs

| Artifact ID | File | artifact_type in ledger | EXIT_CODE:0 present? | POST_PASS errors? | Present in package |
|---|---|---|---|---|---|
| E001 | reports/system-gap-analyst/raw_test_output.txt | raw_test_output | YES | NO | YES |

## Required gate artifacts (GATE_FULL_PLUS_DOMAIN_ADDENDUM)

| File | Present | Verified |
|---|---|---|
| GATE_PROFILE_SELECTION.md | YES | YES |
| CURRENT_STATE.yaml | YES | YES |
| CYCLE_TRACKER.md | YES | YES |
| CLAIMS_LEDGER.yaml | YES | YES |
| EVIDENCE_LEDGER.yaml | YES | YES |
| STALE_FILE_REGISTER.yaml | YES | YES |
| PACKAGE_MANIFEST.md | YES | YES |
| EVIDENCE_ADEQUACY_ASSESSMENT.md | YES | YES |
| EVIDENCE_CONSISTENCY_REGISTER.md | YES | YES |
| COLD_REVIEW_REQUIREMENTS_AUDIT.md | YES | YES |
| COLD_REVIEW_ACTIVE_PROOF_AUDIT.md | YES | YES |
| COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md | YES | YES |
| COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md | YES | YES |
| COLD_REVIEW_ADJUDICATION.md | YES | YES |
| HANDOFF.md | YES | YES |
| PROMPT_CONTRACT_REVIEW.md | YES | YES |
| PRODUCTION_CALLER_AUDIT.md | YES | YES |
| CONSUMER_API_PROOF_AUDIT.md | YES | YES |
| WARNING_OUTPUT_AUDIT.md | YES | YES |
| REQUIRED_TEST_SET_EXACTNESS.md | YES | YES |
| STRANDED_HELPER_AUDIT.md | YES | YES |
| EXPORT_CHANNEL_AUDIT.md | YES | YES |
| DIFF_BASE_SCOPE_AUDIT.md | YES | YES |
| DIRTY_WORKTREE_RECURRENCE.md | YES | YES |
| FLAKE_TIMEOUT_AUDIT.md | YES | YES |
| DOWNSTREAM_CONSUMER_READINESS.md | YES | YES |
| NEXT_PROMPT_DECISION.md | YES | YES |
| CTO_OPERATOR_INSIGHT_REVIEW.md | YES | YES |
| GATE_EFFECTIVENESS_LOG.md | YES | YES |
| OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md | YES | YES |
| GATE_PACKAGE_VALIDATION_REPORT.md | YES | YES |
| FINAL_PACKET_AUDITOR_REPORT.md | YES | YES |
| DOMAIN_ADDENDUM_model_id_validation.md | YES | YES |
| package_file_sizes.txt | YES | YES |
| package_file_hashes.txt | YES | YES |
| gate_hash.txt | YES | YES |
| git_status_final.txt | YES | YES |
| PACKAGE_MANIFEST.md | YES | YES |

## Reproducibility artifacts

| File or directory | Present | Verified |
|---|---|---|
| src/claude_pipeline/nodes/system_gap_analyst.py | YES | YES |
| src/claude_pipeline/state.py | YES | YES |
| src/claude_pipeline/graph.py | YES | YES |
| src/claude_pipeline/nodes/plan.py | YES | YES |
| prompts/metabuilder/35_system_gap_analyst.md | YES | YES |
| tests/test_system_gap_analyst.py | YES | YES |
| tests/__init__.py | YES | YES |
| reports/system-gap-analyst/mermaid_render.txt | YES | YES |

## Domain addendum

| Addendum | Source path | Package proof |
|---|---|---|
| model_id_validation | gate/domain_addenda/model_id_validation.md (resolved at validation time) | reports/system-gap-analyst/DOMAIN_ADDENDUM_model_id_validation.md |
