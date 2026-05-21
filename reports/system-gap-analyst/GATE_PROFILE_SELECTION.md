# Gate Profile Selection

```yaml
gate_profile: GATE_FULL_PLUS_DOMAIN_ADDENDUM
risk_tier: D2_HOT
task_kind: provider_model_routing
domain_addenda:
  - model_id_validation
profile_selection_rationale: "Adds a new pipeline node src/claude_pipeline/nodes/system_gap_analyst.py that hardcodes the LLM model identifier claude-opus-4-7 and routes the adversarial pre-lane to Tier-3 Opus. Per GATE_PROFILE_SELECTOR.md the file falls under the hot-files list (Any file containing hardcoded claude-* model strings), escalating risk_tier to D2_HOT. The hot-file escalation also triggers the LLM model routing rule which mandates the model_id_validation domain addendum, so the package selects GATE_FULL_PLUS_DOMAIN_ADDENDUM. task_kind=provider_model_routing matches the model-id introduction; risk_tier and addendum collectively require GATE_FULL minimum."
human_decision_required: false
```

## Inputs that drove the selection

- Diff touches `src/claude_pipeline/nodes/system_gap_analyst.py` (new), which contains the literal `OPUS_MODEL = "claude-opus-4-7"` model identifier.
- Diff touches `src/claude_pipeline/graph.py` to insert a new pipeline node between `research` and `plan` (handoff topology change, but not gate-state-machine logic).
- Diff touches `src/claude_pipeline/nodes/plan.py` to inject blocking/advisory gaps into the planner prompt.
- Diff touches `src/claude_pipeline/state.py` to add `GapAnalysis` TypedDict + `gap_analysis` field.
- Diff adds `prompts/metabuilder/35_system_gap_analyst.md`, `tests/__init__.py`, `tests/test_system_gap_analyst.py`, and updates `README.md`.

## Hot-file determination

Hot-file list in `GATE_PROFILE_SELECTOR.md` includes "Any file containing hardcoded `claude-*` model strings." The new node hardcodes `claude-opus-4-7`, satisfying that rule and forcing escalation from D2 to D2-hot.

## Escalation triggers fired

| Trigger | Effect |
|---|---|
| Diff contains hardcoded `claude-*` model string | risk_tier → D2_HOT → minimum GATE_FULL |
| Task modifies LLM model routing or provider selection | GATE_FULL + `model_id_validation` domain addendum |
| Therefore | Final profile: GATE_FULL_PLUS_DOMAIN_ADDENDUM |

## Domain addenda checks

- `model_id_validation` source definition exists at `gate/domain_addenda/model_id_validation.md` (verified by check_gate_package.py).
- Per-addendum proof file produced at `reports/system-gap-analyst/DOMAIN_ADDENDUM_model_id_validation.md`.
