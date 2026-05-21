# Gate Profile Selection

**Task ID:** ROUND4-AGENT1-FSM-001
**Task area:** round4-agent1-fsm
**Gate run ID:** gate-2026-05-02T12:00:00Z

---

## Risk Tier Assessment

```
RISK_TIER_ASSESSMENT
Files in touch map: 8
Hot files found:
  - gui/lib/scribbli_llm.js (consumed by call_gateway_shim — LLM routing consumer)
  - gui/routes/front_door_route.js (modifies desired_provider_order — LLM provider selection)
Migration files: none
Live-behavior claims:
  - "provider_used SSE event now emits provider:anthropic" — live behavior fixed
  - "Alice memory test now passes in browser" — live behavior fixed
  - "software pipeline generates real code via LLM" — live behavior fixed
Escalation triggers fired:
  - "Diff touches hot file (scribbli_llm consumer + provider order change)" → GATE_FULL
  - "Task claims live behavior fixed" → GATE_FULL
  - "Task modifies LLM model routing/provider selection" → GATE_FULL + model_id_validation addendum
Determined risk tier: D2-hot
Rationale: Task modifies LLM provider order in front_door_route.js and creates a scribbli_llm shim — both are LLM routing hot-file territory, with live-behavior-fixed claims on top.
```

---

## Profile Selection

Selected profile: **GATE_FULL** (with model_id_validation domain addendum)

| Risk tier | Default profile |
|---|---|
| D2-hot | GATE_FULL |

Escalation to `GATE_FULL_PLUS_DOMAIN_ADDENDUM` applies because the model_id_validation addendum file exists at `gate/domain_addenda/model_id_validation.md`.

---

## Domain Addenda

- `model_id_validation` — task creates `call_gateway_shim.js` which hardcodes `desired_provider_order: ['anthropic', 'openai', 'proxy']` and model identifiers (`claude-sonnet-4-6`, `gpt-4o`). Addendum requires: model/provider IDs explicitly named in evidence; handoff does not overclaim routing behavior; routing-policy changes reflected in diff + tests.

Model ID validation check:
- `claude-sonnet-4-6` — valid current Anthropic model. Present in `.env` as `FRONT_DOOR_MODEL`. ✓
- `gpt-4o` — valid OpenAI model. ✓
- `meta-llama/llama-3.3-70b-instruct` — valid OpenRouter model. ✓
- `desired_provider_order: ['anthropic', 'openai', 'proxy']` — correct order, anthropic is first. ✓
- Curl evidence confirms `provider:anthropic` is used in practice. ✓
- Handoff does NOT overclaim: writing pipeline still uses OpenRouter when OpenRouter key is present; Anthropic SDK is used only for chat. ✓

Addendum result: **PASS**

---

## YAML selector output

```yaml
selected_profile: GATE_FULL_PLUS_DOMAIN_ADDENDUM
risk_tier: D2-hot
task_kind: provider_model_routing
reason: "Task modifies LLM provider selection order in front_door_route.js (desired_provider_order), creates callGatewayLLM shim over scribbli_llm, and claims live behavior is fixed for provider_used SSE and Alice browser memory test. Hot-file escalation + live-behavior-fixed escalation + model routing change all trigger GATE_FULL. model_id_validation addendum applies because model IDs are hardcoded in shim."
domain_addenda: ["model_id_validation"]
profile_override_required: false
human_decision_required: false
```
