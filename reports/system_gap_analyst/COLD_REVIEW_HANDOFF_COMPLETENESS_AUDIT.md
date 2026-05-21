# R4 — Risk review (cold)

**Reviewer perspective:** What could go wrong in production with this change? What blast radius, what mitigation, what residual risk?

## Risk register

### R4.1 — Unsupported `claude` CLI flags
- **Severity:** WAS BLOCKING (cycle 1); now resolved.
- **Description:** Cycle 1 passed `--max-tokens 8192 --temperature 0.2` to `claude --print`. Those flags are not exposed by the CLI (`raw/claude_help.txt`). The subprocess would have exited non-zero, surfaced as `ClaudeError(... exited 2 ...)`, breaking every live run of the system_gap_analyst and contract nodes.
- **Mitigation:** Cycle 2 removes both flags. Only `--model` and `--append-system-prompt` are passed — both are documented as valid in `claude --help`. Limitation re: parameter control is captured in module docstrings and in `claude_help.txt`.
- **Residual risk:** Without temperature control, runs may be less deterministic than the spec implies. Acceptable for an adversarial reviewer role (variance can surface different gaps across runs; the contract_writer downstream can absorb that variance).

### R4.2 — Source-of-truth drift on the 8 lens names
- **Severity:** Low.
- **Description:** Lens names live in `prompts/metabuilder/35_system_gap_analyst.md` AND in `nodes/system_gap_analyst.py:LENSES`. Drift would silently degrade the analyst's adherence to the lens taxonomy.
- **Mitigation:** `test_gap_packet_lenses_are_the_metabuilder_eight` pins the code-side list. The prompt-side list is reviewed in `PROMPT_CONTRACT_REVIEW.md`.
- **Residual risk:** Future edit to the prompt file without a corresponding edit to `LENSES` would not be caught by tests. **Suggested follow-up issue:** add a test that greps each lens name out of the prompt file. Not blocking for this gate.

### R4.3 — Codebase anchor degrades silently when research output is markdown
- **Severity:** Low.
- **Description:** `_build_codebase_anchor` extracts `sources_consulted` + `implementation_details` only when the research brief is JSON-shaped. Today's research_node returns markdown, so the anchor block falls back to a "research brief embedded as plain context below" note.
- **Mitigation:** This is the intended behaviour — the issue body says the anchor should be "drawn from research output's `sources_consulted` and `implementation_details`" if available. The fallback message is explicit so it's not invisible.
- **Residual risk:** None until research_node is upgraded (port-spec step 3). When that lands, the anchor automatically gets richer.

### R4.4 — `plan_node` does not yet consume `contract`
- **Severity:** Low (intentional out-of-scope).
- **Description:** The new `contract` field on `PipelineState` is populated but ignored by `plan_node`. Plans are still built from `research_brief` only.
- **Mitigation:** STALE_FILE_REGISTER calls this out. It is the next-issue's scope per `docs/metabuilder-port-spec.md` step 4 ("Split plan into contract + planner two-step").
- **Residual risk:** Until that issue lands, the value of the contract_writer is only that it (a) gives the system_gap_analyst something to feed and (b) is on the graph topology so live runs exercise it. Acceptable: this issue is "port system_gap_analyst", not "rewire plan_node".

### R4.5 — Live runs of new graph not exercised
- **Severity:** Low.
- **Description:** Tests are pure-python; no end-to-end run against a real issue is included. The graph compiles cleanly (`render_mermaid` succeeds) but the live-LLM path is not proven.
- **Mitigation:** The LLM-touching nodes follow the exact pattern of the already-working `intake_node` / `research_node` / `plan_node`. No new transport code. No new SDK. The blast radius of a runtime issue is "one pipeline run errors out", which is logged and bounded by `claude --print` timeout.
- **Residual risk:** First live run may discover something CLI- or model-specific that didn't surface in unit tests. Standard A/B-eval risk per the architectural rules.

### R4.6 — Permission mode for the new nodes
- **Severity:** Low.
- **Description:** `run_claude` defaults `permission_mode="bypassPermissions"`. The system_gap_analyst is a read-only / no-tool-use role (it doesn't need to write files). `bypassPermissions` is wider than needed.
- **Mitigation:** Same as existing intake/research nodes — they also use the default. A tighter `--permission-mode plan` would be more correct but is a cross-cutting cleanup, not this issue's scope.
- **Residual risk:** None substantive; the gap analyst is given a textual packet and asked for JSON, so even if it tried to write files, there is nothing in the prompt asking it to.

## Blast radius if this commit is wrong

- **Live pipeline:** A run kicked off after this commit would route through the new nodes. If either node failed, the existing fail-safe logic (each node returns `{"error": ...}` and LangGraph stops the run) would catch it. No data corruption path; no irreversible action upstream of `pr_node`.
- **Tests:** Existing v0.1 suite had 0 tests; this commit only adds tests. No regression vector.
- **PR creation:** `pr_node` is downstream and unchanged.

## Verdict (R4)

**PASS.** The most material risk (R4.1) was the cycle-1 judge's fix #6 and is now resolved. Remaining risks are low-severity with clean mitigation paths and no path to data corruption or irreversible action.
