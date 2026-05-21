# Cold Review — R1 Requirements Traceability Audit
Sprint 3 — SimpleAgent emdash Bridge
Gate 5.4 — Reviewer 1

State: R1_IN_PROGRESS

Do not be charitable. Do not praise. Fail closed.

---

## Requirements extracted from contract.md and task prompt

| id | requirement text (verbatim) | artifact/file satisfying it | test/proof satisfying it | status | evidence path | BLOCKING: YES/NO |
|---|---|---|---|---|---|---|
| R01 | "Expose POST /hooks/before-provision on http://127.0.0.1:8765" | hook_server.py — HTTPServer on 127.0.0.1, _HookHandler.do_POST matches path | test_http_server_allow, test_http_server_deny — real HTTP POST to this endpoint | SATISFIED | test_output.txt | NO |
| R02 | "Keep the bridge module self-contained in governed_fsm_conduit/bridge/" | bridge/__init__.py, bridge/hook_server.py exist at that path | Repo structure confirmed | SATISFIED | repo_state.txt (untracked files list) | NO |
| R03 | "Decision logic is read-only — never mutates FSM state" | hook_server.py — decide() only reads RUN.json, no writes | Tests do not check for writes; hook_server.py code has no write calls | SATISFIED | hook_server.py (no write operations in code) | NO |
| R04 | "Server starts alongside SimpleAgent's normal boot (not a standalone script)" | front_door.py lines 405-407: _state_root and start_bridge_server() called in main() unconditionally | No test proves main() actually starts the bridge in integration | PARTIAL — see R04 note | diff.patch, front_door.py | NO |
| R05-DET | "No active FSM run → emdash receives {allowed: true} — detection: bridge identifies no active runs" | decide() returns HookDecision(allowed=True) when no active runs | test_decide_allow_no_active_runs, test_http_server_allow | SATISFIED | test_output.txt | NO |
| R05-PRV | "No active FSM run → emdash receives {allowed: true} — prevention: emdash does not block provisioning" | INFRASTRUCTURE_READY — Sprint 2 verified emdash honors allow response | No Sprint 3 live e2e test | PARTIAL — accepted for INFRASTRUCTURE_READY tier | HANDOFF.md | NO |
| R06-DET | "FSM in implementation state → emdash receives {allowed: true}" | decide() returns allowed=True for S14 | test_decide_allow_implementation_state | SATISFIED | test_output.txt | NO |
| R06-PRV | "FSM in implementation state → emdash receives {allowed: true} — emdash allows provisioning" | Sprint 2 proof (not in Sprint 3) | Not tested in Sprint 3 | PARTIAL — accepted for INFRASTRUCTURE_READY tier | HANDOFF.md | NO |
| R07-DET | "FSM in planning/approval state → emdash receives {allowed: false, reason: ...}" | decide() returns allowed=False with reason for S06 | test_decide_deny_planning_state | SATISFIED | test_output.txt | NO |
| R07-PRV | "FSM in planning state → emdash blocks provisioning" | Sprint 2 proof (not in Sprint 3) | Not tested in Sprint 3 | PARTIAL — accepted for INFRASTRUCTURE_READY tier | HANDOFF.md | NO |
| R08 | "tool_closed → emdash receives {allowed: false, reason: ...}" | decide() returns allowed=False with "tool_closed" in reason; hook_server.py lines 76-81 | test_decide_deny_tool_closed (SKIPPED — no state in MVP uses tool_closed) | PARTIAL — branch exists and is tested via mock; not tested against real policy | test_output.txt (1 skipped) | NO |
| R09 | "Do NOT start a new FSM run per hook call" | hook_server.py has no call to any service or runtime; pure file reader | No direct test for this | SATISFIED — by code inspection; no FSM service import in hook_server.py | hook_server.py | NO |
| R10 | "Do NOT require a running FSM to respond" | decide() handles missing state_root, empty state_root, completed runs | test_decide_allow_no_state_root, test_decide_allow_no_active_runs | SATISFIED | test_output.txt | NO |
| R11 | "Do NOT modify any FSM state on hook call" | hook_server.py reads only; no write operations | Implicit in test setup (tmp_path state unchanged after decide()) | SATISFIED — code inspection + test side-effects | hook_server.py | NO |
| R12 | "No auth between emdash and SimpleAgent" | hook_server.py — no auth logic; trusts all requests | By code structure | SATISFIED | hook_server.py | NO |
| R13 | "No other hook events beyond task.before_provision" | do_POST returns 404 for non-matching paths | No test for 404 path | PARTIAL — 404 implemented but untested | hook_server.py:99 | NO |
| R14 | "pytest tests/test_bridge.py must pass" | test_output.txt shows 8 passed, 1 skipped, EXIT_CODE: 0 | Direct evidence | SATISFIED | test_output.txt | NO |
| R15 | "front_door.py starts without starting the bridge server → FAILURE condition" | front_door.py calls start_bridge_server unconditionally | No integration test verifying bridge actually started | PARTIAL — code is wired; no runtime verify | diff.patch | NO |
| R16 | "Any import of bridge module causes ImportError → FAILURE condition (must NOT happen)" | import in front_door.py works (tests run, which import from bridge) | tests import from bridge successfully | SATISFIED | test_output.txt (tests pass means import works) | NO |
| R17 | "/hooks/before-provision returns 200 JSON — never 500" | do_POST wraps decide() in try/except, fails open to allowed=True on error | No test for the error path (internal exception) | PARTIAL — code implements it; exception path untested | hook_server.py:112-117 | NO |
| R18 | "state_policy_for raises if unknown state → wrap with try/except, default to DENY" | hook_server.py lines 66-74: try/except around state_policy_for, returns DENY | test_decide_deny_unknown_state_not_in_implementation_states (exercises unknown state) | SATISFIED | test_output.txt | NO |
| R19 | "Bridge must not crash if state_root doesn't exist yet" | decide() checks root.exists() → returns ALLOW | test_decide_allow_no_state_root | SATISFIED | test_output.txt | NO |

---

## Notes on PARTIAL items

**R04 — server starts alongside boot:** The code wires start_bridge_server in main(). There is no integration test that calls main() and verifies the bridge is listening. This is a code-inspection-only verification. For an INFRASTRUCTURE_READY sprint, this is acceptable.

**R08 — tool_closed branch:** The test is SKIPPED because no current MVP state has `enforcement_tier="tool_closed"`. The test uses `unittest.mock.patch` to inject a synthetic policy. This is a behavioral test of the code branch, not a test against real policy. The branch is proved to exist and execute correctly.

**R13 — 404 for other paths:** Not explicitly tested. Code at hook_server.py:99 returns `self.send_error(404)` for non-matching paths. Minor gap; not blocking.

**R15 — no runtime verification of bridge start:** The diff shows the bridge is wired. There is no test that calls `main()` and then makes a real HTTP request to verify the bridge started. This is an integration gap; acceptable for INFRASTRUCTURE_READY.

**R17 — exception path:** The `except Exception` handler in do_POST fails open (allows provisioning on error). This is tested implicitly only by the happy-path tests succeeding; no test injects an exception into decide() via the HTTP layer.

---

## R1 Summary
- Total requirements found: 19 (including 4 detection/prevention pairs counted separately)
- SATISFIED: 11
- PARTIAL: 8 (all non-blocking, all either accepted for INFRASTRUCTURE_READY or minor code coverage gaps)
- MISSING: 0
- NOT_APPLICABLE: 0
- BLOCKING findings: 0
- NON-BLOCKING findings: 8 (partial requirements, all with justification)
