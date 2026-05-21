# Downstream Consumer Readiness Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 33

State: DOWNSTREAM_CONSUMER_READINESS_AUDIT_IN_PROGRESS

---

## Check 1 -- Identify next-phase consumers

| Consumer | What it needs from Sprint 3 | Type |
|---|---|---|
| Sprint 4 (emdash createTask.ts fix) | bridge API shape (`POST /hooks/before-provision`, response schema `{allowed, reason, details}`) | Code consumer |
| Human reviewer | Gate package with all evidence | Review consumer |
| Future integration tests | `start_bridge_server()` function signature, `HookDecision` type | Test consumer |
| merge into target branch | Clean commit with no conflicts | Git consumer |

---

## Check 2 -- API contract matches what consumer expects

### emdash consumer (Sprint 2 already wired for provisionTask path)

emdash expects:
- Endpoint: `POST /hooks/before-provision` at `http://127.0.0.1:8765` -- MATCHES (hook_server.py default port 8765, path `/hooks/before-provision`)
- Request body: `BeforeProvisionContext` JSON -- MATCHES (bridge accepts any valid JSON on POST)
- Response: `{allowed: true}` or `{allowed: false, reason: "...", details: "..."}` -- MATCHES (hook_server.py:119-124)
- Timeout handling: emdash has `timeout_ms: 30000` in hooks.json example -- bridge responds synchronously, well under 30s

### createTask.ts consumer (Sprint 4)

Sprint 4 will need to wire createTask.ts through the hook. The hook API shape is stable and documented in `agents/integrations/simpleagent-bridge.md`.

---

## Check 3 -- No breaking changes introduced

Sprint 3 adds new code; it does not remove or rename any existing exports or functions. The only modified file (`front_door.py`) adds lines; no existing functionality is altered.

| Check | Result |
|---|---|
| Exported function removed or renamed? | NO |
| Function signature changed? | NO (new functions only) |
| Config key removed or renamed? | NO |

---

## Check 4 -- Required artifacts exist

| Required artifact | Exists? | Format correct? |
|---|---|---|
| Bridge module at `governed_fsm_conduit/bridge/` | YES | Python module with __init__.py |
| HTTP endpoint at `/hooks/before-provision` | YES | Returns 200 JSON |
| Test file at `tests/test_bridge.py` | YES | pytest compatible, 9 tests |
| Documentation at `agents/integrations/simpleagent-bridge.md` | YES | Markdown with setup, schema, limitations |
| diff.patch | YES | Standard unified diff format |
| test_output.txt | YES | Raw pytest output with EXIT_CODE |

---

## Verdict

### Caveats for downstream consumers

1. **createTask.ts bypass** -- the emdash consumer using the createTask path will not be governed until Sprint 4 wires it through the hook.
2. **No e2e integration test** -- downstream integration testing (SimpleAgent + emdash together) is deferred. Sprint 2's mock-based test covers the interface contract.
3. **Port configuration** -- emdash must configure `hooks.json` to point to port 8765 (or the port set via `SIMPLEAGENT_HOOK_PORT` env var).

State: **DOWNSTREAM_READY_WITH_CAVEAT**

Caveats are documented in HANDOFF.md and `agents/integrations/simpleagent-bridge.md`. The next phase can start with awareness of these limitations.
