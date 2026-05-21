# Production Caller / Active Path Claim Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 20

State: PRODUCTION_CALLER_AUDIT_IN_PROGRESS

---

## Applicability

Sprint 3 claims production wiring: `front_door.py:main()` unconditionally calls `start_bridge_server()`. This is a live-behavior claim -- the bridge starts on every SimpleAgent boot. Audit is mandatory.

---

## Required table

| Claimed live behavior | Function / module changed | Production caller found? | Caller evidence | Test-only? | Verdict |
|---|---|---|---|---|---|
| Bridge server starts on boot | `governed_fsm_conduit.bridge.hook_server:start_bridge_server` | YES | `front_door.py` line 28: `from governed_fsm_conduit.bridge import start_bridge_server`; line 407: `start_bridge_server(_state_root)` in `main()` | NO -- called from production entrypoint `front_door.py:main()` | INFRASTRUCTURE_READY_NOT_WIRED |
| decide() returns allow/deny based on FSM state | `governed_fsm_conduit.bridge.hook_server:decide` | YES (indirect) | `decide()` is called by `_HookHandler.do_POST()` which is the HTTP handler for the server started by `start_bridge_server()`. Production caller chain: `front_door.py:main()` -> `start_bridge_server()` -> HTTPServer -> `_HookHandler.do_POST()` -> `decide()` | NO | INFRASTRUCTURE_READY_NOT_WIRED |
| HookDecision used in production | `governed_fsm_conduit.bridge.hook_server:HookDecision` | YES (indirect) | Returned by `decide()` which is called by the HTTP handler in production. Also used in test assertions. | NO -- production path exists via decide() | INFRASTRUCTURE_READY_NOT_WIRED |

---

## Production caller import trace

```
front_door.py (production entrypoint: `python front_door.py --interactive`)
  line 28: from governed_fsm_conduit.bridge import start_bridge_server
  line 405-407 in main():
    _state_root = ROOT / ".agentos-ng" / "governed-fsm-conduit"
    start_bridge_server(_state_root)
      -> hook_server.py: HTTPServer(("127.0.0.1", port), handler_cls)
        -> handler_cls.do_POST() -> decide(self.state_root)
```

This is a complete import trace from production entrypoint to the bridge module.

---

## Why INFRASTRUCTURE_READY_NOT_WIRED (not LIVE_BEHAVIOR_FIXED)

The production caller (`front_door.py:main()`) exists and is proven. However, the HANDOFF.md correctly classifies the delivery as INFRASTRUCTURE_READY_NOT_WIRED because:

1. The bridge server starts and listens, but no external consumer (emdash) has been verified calling it in this sprint's evidence.
2. Sprint 2 verified the emdash hook chain with mocked responses. Sprint 3 builds the real SimpleAgent side. Full e2e proof requires running both together, which is out of Sprint 3 scope.
3. The createTask.ts bypass means enforcement is partial.

The production caller is real. The infrastructure is wired. The classification is honest.

---

## Verdict

All claimed live behaviors have a production caller traced from `front_door.py:main()`. No overclaim detected -- HANDOFF.md uses `INFRASTRUCTURE_READY_NOT_WIRED`, not `LIVE_BEHAVIOR_FIXED`.

State: **PRODUCTION_CALLER_AUDIT_PASS**
