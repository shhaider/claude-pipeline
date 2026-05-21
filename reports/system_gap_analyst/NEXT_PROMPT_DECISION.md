# Next-prompt decision

**Task area:** `system_gap_analyst`

## Recommended next issue

**Title:** Wire `plan_node` to consume `state["contract"].deliverables` (pack_planner port)

**Why now:** This issue (system_gap_analyst + contract_writer) introduces `gap_analysis` and `contract` into pipeline state, but `plan_node` still reads only `research_brief`. The seam is dormant until the planner consumes it. Port spec roadmap step 4 ("Split plan into contract + planner two-step") is the natural next step.

## Recommended next-issue prompt sketch

```
Title: Port pack_planner to consume contract deliverables

Body:
Currently nodes/plan.py reads intake + research_brief and produces a Stage[]
without consulting state["contract"]. Now that contract_node exists upstream
and produces structured deliverables, plan_node must route every deliverable
into at least one stage.

What to build:
1. Update nodes/plan.py to:
   - Read state["contract"].deliverables.
   - Inject the deliverables verbatim into the planner prompt as
     "MANDATORY CONTRACT — every deliverable below MUST appear in at least one
     stage."
   - Output Stage[] tagged with which deliverable(s) each stage covers.
2. Add checkPlanCompleteness deterministic post-processor: every
   deliverable.id must appear in some stage's purpose or file_touch_map; if
   missing, trigger one 4-Correction cycle.
3. Tests: covers (a) deliverable injection into planner prompt; (b)
   completeness check catches missing deliverable; (c) 4-Correction cycle
   fires at most once.

Out of scope:
- Don't port revision loop or surgical mode (separate issues).
- Don't change the contract_node schema.
```

## Why not other candidates?

- **cto_orchestrator port** — would be the third adversarial pre-lane. Lower priority than wiring the existing contract into the planner; the planner is the bottleneck for downstream value.
- **verify ladder split** — large, would block on a separate port (4 mandatory reviewers panel). Not ready.
- **tier-based LLM routing** — needs a transport layer that doesn't exist yet. Defer until SDK migration.

## Verdict

**Decision:** ship the pack_planner consumption upgrade next.
