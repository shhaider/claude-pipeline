# CTO / operator insight review

**Task area:** `system_gap_analyst`

## Strategic context

This issue ports the FIRST of two adversarial pre-lanes from metabuilder (`system_gap_analyst`). The second (`cto_orchestrator`) is explicitly out of scope here. Together they form the "stress-test the framing before writing the contract" discipline that metabuilder has and the claude-pipeline currently lacks.

## Insights worth surfacing to the operator

1. **The pipeline now has a dormant `contract` node.** This commit wires the topology and the seam, but `plan_node` does not yet consume the contract. The next issue (see `NEXT_PROMPT_DECISION.md`) closes that loop. If the operator runs the pipeline today, the contract_node will execute and produce deliverables that are then ignored by plan. This is intentional sequencing — splitting the plan/contract upgrade across two issues bounds blast radius — but the operator should know that the value of system_gap_analyst is only fully realized once issue N+1 lands.

2. **The `claude --print` CLI does not expose `--max-tokens` or `--temperature`.** This was the cycle-1 bug. The fix is local (remove the flags), but the deeper implication is that **any spec calling for parameter control (T=0.2, 8192 tok, etc.) is currently unenforceable from the pipeline's transport layer.** Operator should either (a) accept implicit CLI defaults across the board, or (b) prioritize an SDK migration. Recommend (b) before any role that genuinely depends on low-T determinism (e.g. release_gatekeeper).

3. **Self-reviewed gate.** The four-way harness does not (currently) provide separate reviewer agents for the R1–R5 panel or for FINAL_PACKET_AUDITOR independence. The coder writes all reviews. The FINAL_PACKET_AUDITOR_REPORT.md in this package addresses independence by spawning a fresh subagent to act as the auditor, but that is a workaround. The honest long-term path is a separate-process review pool. Track this as a meta-issue.

4. **Profile selection chose D2 over D3.** Justified because the change is additive and downstream consumers tolerate the new state fields. If a future issue flips `plan_node` to a required-consumer of `state["contract"]`, the risk tier will bump to D3 and that issue should be GATE_FULL with a stricter consumer-API-proof audit.

5. **Three-cycle gate run.** Cycle 1 (substantive impl) → judge FAIL (process). Cycle 2 (process + CLI fix) → judge FAIL (gate package format). Cycle 3 (this) — converging on the actual checker output. This is expensive. Suggest: the next coder onboarding doc should foreground `tools/check_gate_package.py` as the entry point, not the prose `00_START.md`. Code is the spec.

## Verdict

**Insights logged. No blocking concerns. Strategic recommendations for the operator surfaced.**
