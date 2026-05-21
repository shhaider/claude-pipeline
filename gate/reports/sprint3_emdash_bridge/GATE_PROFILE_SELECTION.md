# Gate Profile Selection — Sprint 3 emdash Bridge
Gate 5.4

**State:** GATE_PROFILE_SELECTION_IN_PROGRESS → GATE_PROFILE_SELECTION_COMPLETE

---

## Step 1 — Risk Tier Assessment

```
RISK_TIER_ASSESSMENT
Files in touch map: 5
  - governed_fsm_conduit/bridge/__init__.py (CREATE — new module)
  - governed_fsm_conduit/bridge/hook_server.py (CREATE — new module)
  - front_door.py (MODIFY — main entrypoint, shared by all callers)
  - tests/test_bridge.py (CREATE — new test file)
  - agents/integrations/simpleagent-bridge.md (CREATE — docs)

Hot files found: front_door.py is NOT on the gate's hot-files list (it is not an LLM routing file,
  a gate file, a workflow yml, or a migration registry). However it IS a shared production entrypoint.

Migration files: none

Live-behavior claims: YES — "Server starts alongside SimpleAgent's normal boot" (contract)
  front_door.py:407 calls start_bridge_server unconditionally in main()
  This is a production wiring claim.

Escalation triggers fired:
  - "Task claims live behavior is fixed / production wiring complete" → D3 → GATE_FULL
  - task_kind = production_wiring → GATE_FULL minimum

Determined risk tier: D3
Rationale: Sprint 3 claims that front_door.py now unconditionally starts the bridge server on every
  SimpleAgent boot — this is a production wiring claim that directly modifies runtime behavior of
  the main entrypoint, qualifying as D3.
```

---

## Step 2 — Profile Selection

| Risk tier | Default profile |
|---|---|
| D3 | GATE_FULL |

The operator specified GATE_FULL in the task prompt. This matches the default for D3. No override required.

**Selected profile: GATE_FULL**

---

## Step 3 — Domain Addenda

Checking each addendum trigger:
- LLM model routing or provider selection: NO — bridge uses stdlib HTTP server, no LLM calls
- Multi-tenant data isolation: NO — localhost-only server, no user data
- Security-sensitive path: NO — localhost trust for v1, no auth by design
- Financial/billing system: NO
- Medical/safety-critical: NO
- Explicit addendum named in task prompt: NONE

**Domain addenda: none**

---

## Step 4 — Human Decision Requirement

- Task prompt is clear about which files are touched: YES (contract lists exact files)
- Risk tier could be ambiguous D2/D4: NO — D3 is unambiguous (production wiring claim)
- Escalation triggers contradict each other: NO
- Missing addendum file: NO (no addenda required)

**human_decision_required: false**

---

## Step 5 — Profile Selection Output

```yaml
selected_profile: GATE_FULL
risk_tier: D3
task_kind: production_wiring
reason: >
  Sprint 3 modifies front_door.py to unconditionally start the HTTP bridge server in main().
  This is a production wiring claim: the bridge becomes part of SimpleAgent's boot sequence.
  D3 (production wiring, live-behavior claimed) requires GATE_FULL.
  No domain addenda apply: bridge is localhost-only, no LLM routing, no migration, no auth change.
domain_addenda: []
profile_override_required: false
human_decision_required: false
```

---

## Routing

Profile selected, no human decision required.
State: GATE_PROFILE_SELECTION_COMPLETE
Next: 01_EVIDENCE_ADEQUACY.md
