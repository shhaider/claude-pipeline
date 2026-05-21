# Downstream Consumer Readiness

**Task area:** system-gap-analyst
**Verdict:** DOWNSTREAM_READY

## Immediate downstream: `plan_node`

`plan_node` now reads `state.get("gap_analysis")` and formats it into the `{gap_block}` placeholder. Pre-existing pipelines that resume from a checkpoint without `gap_analysis` see an empty gap_block (no behaviour change). Tests cover both the populated and empty paths.

## Eventual downstream: contract_writer (metabuilder roadmap item #4)

When `contract_writer` lands, the SGA edge re-targets from `plan` to `contract`. No other change to SGA is required — the consumer interface (`gap_analysis: GapAnalysis`) is stable. PLAN.md §0 records this re-targeting plan.

## Verdict

DOWNSTREAM_READY — current consumer is wired and tested; future consumer's contract is preserved.
