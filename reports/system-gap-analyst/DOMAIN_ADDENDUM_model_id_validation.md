# Domain Addendum Proof — model_id_validation

**Task area:** system-gap-analyst
**Addendum source:** `gate/domain_addenda/model_id_validation.md`

## Why this addendum applies

The change adds `src/claude_pipeline/nodes/system_gap_analyst.py`, which hardcodes one model identifier:

```
OPUS_MODEL = "claude-opus-4-7"
```

at line 25 of the new node. This identifier is then passed to `run_claude(model=OPUS_MODEL, ...)`. Per `GATE_PROFILE_SELECTOR.md` ("Task modifies LLM model routing or provider selection → GATE_FULL + model validation addendum"), the addendum is mandatory.

## Addendum checks

| Required check | Status | Evidence |
|---|---|---|
| Selected model/provider identifiers are explicitly named in package evidence | MET | `claude-opus-4-7` is named in this file, in CLAIMS_LEDGER C009, in CURRENT_STATE.yaml profile_selection_rationale, and in GATE_PROFILE_SELECTION.md. |
| Handoff does not overclaim routing behaviour beyond tested paths | MET | HANDOFF.md only claims the SGA node calls Tier-3 Opus on a fresh session; no fallback chain, no provider routing, no temperature/max-tokens flags. Tests do not exercise the real CLI (monkeypatched). |
| Fallback or routing-policy changes reflected in package diff, tests, and output-contract evidence | MET | No fallback added (single model, single call site). The single call site is in the package diff (system_gap_analyst.py). Output-contract evidence: OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md lists this addendum in checked_surfaces. |

## Model identifier rationale

`claude-opus-4-7` is selected per `docs/metabuilder-port-spec.md` Tier-3 mapping and matches the current Claude family registry: Opus 4.7 is the most recent Claude Opus model. No alternative tier or fallback is introduced.

## Verdict

PASS — model_id_validation addendum requirements met for this signout.
