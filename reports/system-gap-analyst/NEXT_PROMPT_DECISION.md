# Next Prompt Decision

**Cycle:** 1
**Verdict:** PASS

---

## Question

Given that this gate run terminated `PASS_HANDOFF_COMPLETE`, what is the recommended next prompt for the implementer pipeline to pick up?

---

## Recommendation

**Roadmap item 4 — "Split plan into contract + planner two-step."**

Source of truth: `docs/metabuilder-port-spec.md` "Upgrade roadmap" section, line marked as item 4.

### Why this next

1. The `system_gap_analyst` injection is currently glued onto `plan_node` because there is no contract node yet. The honest call-out is in the source comments, the README, and the commit body. Splitting into `contract_writer` + `pack_planner` is the natural next step — it lets the blocking gaps be injected at the contract level (where `MANDATORY_DELIVERABLES` semantics belong) rather than mid-prompt in the monolithic planner.
2. It is the largest single change still in the MVP-shape backlog. Doing it now unblocks roadmap items 5 (`checkPlanCompleteness` 4-Correction cycle) and 7 (`cto_orchestrator` adversarial pre-lane, which also wants the contract as input).
3. No new external dependencies. Stays inside the LangGraph + `claude --print` envelope.

### What it does NOT mean

- Not "port roadmap item 5/6/7 first" — those need the contract output as input.
- Not "rip out the current `plan_node` and rebuild" — the existing planner becomes the `pack_planner` of the new pair, and a new `contract_writer` node prepends.

---

## Alternatives considered (and why deferred)

- **Roadmap item 7 — `cto_orchestrator`:** Could be ported next on the same prompt-authoring pattern as `system_gap_analyst`, but it expects the contract output. Better after item 4.
- **Roadmap item 9 — per-stage prompt expansion + execution:** Highest-impact for end-to-end accuracy but doesn't depend on the contract split and is a larger rewrite of `nodes/code.py`. Can be parallelised against the contract split if multiple implementers run.
- **Roadmap item 11 — split verify into the 5-role ladder:** Highest leverage on quality but largest change. The current MVP verify is intentionally a placeholder; replacing it requires also wiring the revision loop. Defer until at least the contract split is in.

---

## Findings

- **Blocking:** none
- **Non-blocking:** none

## Verdict

PASS. Next-prompt recommendation: "Implement roadmap item 4 — split `plan_node` into `contract_writer` + `pack_planner`. Migrate the `system_gap_analyst` blocking-gap injection from `plan_node` to the new `contract_writer` node as part of the split."
