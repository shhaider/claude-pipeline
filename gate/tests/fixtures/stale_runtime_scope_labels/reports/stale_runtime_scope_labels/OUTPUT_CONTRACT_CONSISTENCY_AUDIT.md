# Output Contract Consistency Audit

**Task area:** stale_runtime_scope_labels
**Verdict:** FAIL

## Compared surfaces

- HANDOFF
- RUNTIME_SCOPE_CHECK
- REQUIREMENTS_TRACEABILITY_MATRIX
- PACKAGE_MANIFEST
- source snapshots
- tests
- diff

## Blocking findings

- STALE_MILESTONE_LABEL: runtime scope still claims `planning_initiated`, `research_complete`, `gap_analysis_complete`, `cto_review_complete`, `prompts_written`, and `planning_complete`.
- CONTRADICTS_SOURCE: source/test snapshots use `research_done`, `contract_done`, `plan_done`, `expansion_done`, `governance_done`, and `output_written`.
