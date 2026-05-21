# Package manifest — system_gap_analyst port

**Status:** VERIFIED (cycle 3)
**Profile:** GATE_FULL / D2 / prompt_authoring

## Artifacts in this gate package

### Ledgers (Gate 5.4 core)
- `CURRENT_STATE.yaml`
- `CYCLE_TRACKER.md`
- `CLAIMS_LEDGER.yaml`
- `EVIDENCE_LEDGER.yaml`
- `STALE_FILE_REGISTER.yaml`
- `PACKAGE_MANIFEST.md` (this file)

### Gate audits — required_always for GATE_FULL
- `GATE_PROFILE_SELECTION.md`  (machine-readable fenced YAML inside)
- `EVIDENCE_ADEQUACY_ASSESSMENT.md`
- `EVIDENCE_CONSISTENCY_REGISTER.md`
- `COLD_REVIEW_REQUIREMENTS_AUDIT.md`   (was R1_REQUIREMENTS.md in cycle 2)
- `COLD_REVIEW_ACTIVE_PROOF_AUDIT.md`   (was R2_DESIGN.md)
- `COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md` (was R3_TESTS.md)
- `COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md` (was R4_RISKS.md)
- `COLD_REVIEW_ADJUDICATION.md`         (was R5_ADJUDICATION.md)
- `HANDOFF.md`
- `PROMPT_CONTRACT_REVIEW.md`
- `PRODUCTION_CALLER_AUDIT.md`
- `CONSUMER_API_PROOF_AUDIT.md`
- `WARNING_OUTPUT_AUDIT.md`
- `REQUIRED_TEST_SET_EXACTNESS.md`
- `STRANDED_HELPER_AUDIT.md`
- `EXPORT_CHANNEL_AUDIT.md`
- `DIFF_BASE_SCOPE_AUDIT.md`
- `DIRTY_WORKTREE_RECURRENCE.md`
- `FLAKE_TIMEOUT_AUDIT.md`
- `DOWNSTREAM_CONSUMER_READINESS.md`
- `NEXT_PROMPT_DECISION.md`
- `CTO_OPERATOR_INSIGHT_REVIEW.md`
- `GATE_EFFECTIVENESS_LOG.md`
- `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md`
- `FINAL_PACKET_AUDITOR_REPORT.md` (structured `final_packet_auditor:` YAML block; independence: fresh-subagent)
- `GATE_PACKAGE_VALIDATION_REPORT.md` (written by `tools/check_gate_package.py --final`)
- `GATE_VERDICT.md` (coder's pre-PASS barrier checklist)

### Package integrity files
- `package_file_sizes.txt` — `wc -c` of every package file
- `package_file_hashes.txt` — `shasum -a 256` of every package file
- `git_status_final.txt`   — `git status --porcelain` after the cycle-3 commit
- `gate_hash.txt`          — SHA256 of the gate folder under `/tmp/four-way/gate/`, gate version 5.4

### Raw evidence (`raw/`)
- `pytest.txt`       — `python3 -m pytest -v`, 9 PASSED, EXIT_CODE:0
- `mermaid.txt`      — render_mermaid output, EXIT_CODE:0
- `claude_help.txt`  — `claude --help | grep -E -- '--max|--temperature|--append'`, EXIT_CODE:0
- `diff.txt`         — `git diff main...HEAD --stat`, EXIT_CODE:0

## Source under review (diff from main)

| file | type | reviewed in |
|---|---|---|
| `prompts/metabuilder/35_system_gap_analyst.md` | NEW prompt | PROMPT_CONTRACT_REVIEW.md |
| `src/claude_pipeline/nodes/system_gap_analyst.py` | NEW code | COLD_REVIEW_ACTIVE_PROOF_AUDIT.md |
| `src/claude_pipeline/nodes/contract.py` | NEW code | COLD_REVIEW_ACTIVE_PROOF_AUDIT.md |
| `src/claude_pipeline/graph.py` | MODIFIED | COLD_REVIEW_ACTIVE_PROOF_AUDIT.md |
| `src/claude_pipeline/state.py` | MODIFIED | COLD_REVIEW_ACTIVE_PROOF_AUDIT.md |
| `tests/__init__.py` | NEW | COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md |
| `tests/test_system_gap_analyst.py` | NEW | COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md |
| `pyproject.toml` | MODIFIED (1-line) | DIFF_BASE_SCOPE_AUDIT.md |
| `README.md` | MODIFIED | COLD_REVIEW_REQUIREMENTS_AUDIT.md |

## Out of scope (per issue body)

- `cto_orchestrator` lane
- Tier-based LLM routing
- Verify ladder split
- `plan_node` consumption of `state["contract"]` (port-spec step 4, separate issue — see NEXT_PROMPT_DECISION.md)
