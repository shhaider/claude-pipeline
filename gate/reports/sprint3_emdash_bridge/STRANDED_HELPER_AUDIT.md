# Stranded Helper / Unused Export Scan
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 26

State: STRANDED_HELPER_AUDIT_IN_PROGRESS

---

## Applicability

Sprint 3 adds new helpers, exports, and a module. Audit is mandatory.

---

## New symbols/files added

1. `governed_fsm_conduit/bridge/__init__.py` -- new module package
2. `governed_fsm_conduit/bridge/hook_server.py` -- new module
3. `HookDecision` -- new NamedTuple class (exported from `__init__.py`)
4. `decide` -- new function (not exported from `__init__.py`, used internally)
5. `start_bridge_server` -- new function (exported from `__init__.py`)
6. `_HookHandler` -- new class (internal, not exported)
7. `tests/test_bridge.py` -- new test file
8. `agents/integrations/simpleagent-bridge.md` -- new docs file

---

## Required table

| New symbol/file | Defined in | Production caller | Test caller | Downstream consumer | Stranded? | Verdict |
|---|---|---|---|---|---|---|
| `start_bridge_server` | hook_server.py:136 | `front_door.py:407` -- `start_bridge_server(_state_root)` | `test_bridge.py:162,170` -- `start_bridge_server(tmp_path, port=0)` | emdash (via HTTP, not import) | NO | PRODUCTION_WIRED |
| `HookDecision` | hook_server.py:30 | Used by `decide()` return values -> HTTP handler -> production | `test_bridge.py:23` -- import and assertion | None directly (internal data type) | NO | PRODUCTION_WIRED |
| `decide` | hook_server.py:36 | Called by `_HookHandler.do_POST()` -> HTTPServer -> `start_bridge_server()` -> `front_door.py:main()` | `test_bridge.py:87-153` -- 7 unit tests | None directly | NO | PRODUCTION_WIRED |
| `_HookHandler` | hook_server.py:93 | Used by `HTTPServer` instantiation in `start_bridge_server()` | Used indirectly via HTTP integration tests | None directly | NO | PRODUCTION_WIRED (internal class) |
| `bridge/__init__.py` (module) | bridge/ | Imported by `front_door.py:28` | Imported by `test_bridge.py:22` | None | NO | PRODUCTION_WIRED |
| `tests/test_bridge.py` | tests/ | N/A -- test file | Self (it IS the test file) | None | NO | TEST_HELPER_ONLY (correct classification for test file) |
| `simpleagent-bridge.md` | agents/integrations/ | N/A -- documentation | N/A | Human readers | NO | DOCS_ONLY |

---

## Verdict

- All production symbols (`start_bridge_server`, `HookDecision`, `decide`, `_HookHandler`, `bridge/__init__.py`) have production callers traced to `front_door.py:main()`.
- No STRANDED_UNUSED symbols found.
- Test file and docs file are correctly classified as TEST_HELPER_ONLY and DOCS_ONLY respectively.
- The handoff correctly uses INFRASTRUCTURE_READY_NOT_WIRED, not overclaiming LIVE_BEHAVIOR_FIXED.

State: **STRANDED_HELPER_AUDIT_PASS**
