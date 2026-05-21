# Package manifest — system_gap_analyst port

## Artifacts in this gate package

### Process ledgers
- `CURRENT_STATE.yaml` — task area, profile, risk tier, cycle.
- `CYCLE_TRACKER.md` — cycle 1 (FAIL) → cycle 2 (this submission) narrative.
- `CLAIMS_LEDGER.yaml` — 9 claims, each cross-referenced to evidence ID.
- `EVIDENCE_LEDGER.yaml` — 6 evidence entries (raw outputs + source files).
- `STALE_FILE_REGISTER.yaml` — empty; no stale files.
- `PACKAGE_MANIFEST.md` — this file.

### Gate audits
- `GATE_PROFILE_SELECTION.md` — declares `GATE_FULL` / `D2` / `prompt_authoring`.
- `R1_REQUIREMENTS.md` — does the work satisfy the issue's acceptance criteria?
- `R2_DESIGN.md` — node shape + integration seam.
- `R3_TESTS.md` — test adequacy (relevance, real-path, behavioral, specificity, failure-aware, repeatability, raw-backed).
- `R4_RISKS.md` — what could go wrong, what's mitigated, what's deferred.
- `R5_ADJUDICATION.md` — synthesis across R1..R4.
- `PROMPT_CONTRACT_REVIEW.md` — audit of the new role prompt at `prompts/metabuilder/35_system_gap_analyst.md`.
- `FINAL_PACKET_AUDITOR_REPORT.md` — 5-field gate verdict report.
- `GATE_VERDICT.md` — coder's pre-PASS barrier checklist + verdict.

### Raw evidence
- `raw/pytest.txt` — full `python3 -m pytest -v` output with `EXIT_CODE:0` trailer.
- `raw/mermaid.txt` — full mermaid render of graph topology.
- `raw/claude_help.txt` — grep of `claude --help` showing absence of `--max-tokens`/`--temperature`.
- `raw/diff.txt` — `git diff main...HEAD --stat` for scope audit.

## Source files under review (diff from main)
- `prompts/metabuilder/35_system_gap_analyst.md` (NEW — verbatim role prompt)
- `src/claude_pipeline/nodes/system_gap_analyst.py` (NEW — node + packet builder + 8 lens table)
- `src/claude_pipeline/nodes/contract.py` (NEW — contract_writer + gap injection seam)
- `src/claude_pipeline/graph.py` (MODIFIED — topology: research → system_gap_analyst → contract → plan)
- `src/claude_pipeline/state.py` (MODIFIED — adds GapFinding/GapAnalysis/Contract typed dicts + state keys)
- `tests/__init__.py` (NEW — empty package marker)
- `tests/test_system_gap_analyst.py` (NEW — 9 pure-python tests)
- `pyproject.toml` (MODIFIED — `pythonpath = ["src"]` so pytest finds the package)
- `README.md` (MODIFIED — architecture diagram + adversarial-pre-lane explainer)

## Out-of-scope (per issue body, deferred to future issues)
- `cto_orchestrator` adversarial pre-lane
- Tier-based LLM routing
- Verify ladder split
- Plan node's consumption of contract deliverables (still uses research_brief-only path; see STALE_FILE_REGISTER note)
