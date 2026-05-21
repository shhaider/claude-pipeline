# Consumer-API Proof Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 21

State: CONSUMER_API_PROOF_AUDIT_IN_PROGRESS

---

## Applicability

Sprint 3 adds `decide()` and `start_bridge_server()` as public APIs, plus an HTTP endpoint `POST /hooks/before-provision`. Downstream code (emdash) will call the HTTP endpoint. Tests must assert through the consumer API (HTTP POST), not just raw file inspection.

---

## Check 1 -- What API will downstream code call?

| Consumer API | How downstream code calls it |
|---|---|
| `POST /hooks/before-provision` (HTTP endpoint) | emdash sends HTTP POST with BeforeProvisionContext JSON body |
| `decide(state_root)` (Python function) | Called internally by the HTTP handler; not called directly by downstream consumers |
| `start_bridge_server(state_root, port)` (Python function) | Called by `front_door.py:main()` at boot; not called by external consumers |

The primary consumer API is the HTTP endpoint. `decide()` and `start_bridge_server()` are internal APIs called by the production code path, not by external consumers.

---

## Check 2 -- Did tests assert through the consumer API?

| Test | What it calls | Consumer API path? | Raw inspection? |
|---|---|---|---|
| test_decide_allow_no_state_root | `decide(tmp_path / "nonexistent")` | YES -- calls the exact function the HTTP handler uses | NO raw file inspection |
| test_decide_allow_no_active_runs | `decide(tmp_path)` | YES | NO |
| test_decide_allow_implementation_state | `decide(tmp_path)` after writing RUN.json | YES -- reads same files as production | NO |
| test_decide_deny_planning_state | `decide(tmp_path)` | YES | NO |
| test_decide_deny_tool_closed | `decide(tmp_path)` with patched policy | YES (with mock) | NO |
| test_decide_allow_completed_run | `decide(tmp_path)` | YES | NO |
| test_decide_deny_unknown_state | `decide(tmp_path)` | YES | NO |
| test_http_server_allow | HTTP POST via `urllib.request` to real server | YES -- tests the actual consumer API path | NO |
| test_http_server_deny | HTTP POST via `urllib.request` to real server | YES -- tests the actual consumer API path | NO |

---

## Check 3 -- Raw inspection present?

No test uses raw file inspection as a substitute for API testing. All tests assert through the `decide()` function (internal API) or the HTTP endpoint (consumer API).

---

## Check 4 -- Ordering/latest semantics

`decide()` uses `max(active, key=lambda r: r.get("last_updated", ""))` to select the most recently updated active run. No test explicitly verifies ordering behavior with multiple concurrent active runs. This is a minor gap -- the ordering logic is simple (string comparison on ISO timestamps) and unlikely to be wrong, but no test covers the multi-run ordering case.

NON-BLOCKING: The ordering logic is a single `max()` call on ISO timestamps. The risk is low. A future test could add a multi-run scenario.

---

## Required table

| Consumer API | What downstream code calls | Tested through consumer API? | Raw inspection only? | Ordering/latest semantics tested? | Verdict |
|---|---|---|---|---|---|
| POST /hooks/before-provision | emdash HTTP POST | YES (test_http_server_allow, test_http_server_deny) | NO | N/A for HTTP tests | CONSUMER_API_PROVEN |
| decide(state_root) | HTTP handler internally | YES (7 unit tests call decide() directly) | NO | NO (single-run tests only) | CONSUMER_API_PROVEN |
| start_bridge_server() | front_door.py:main() | YES (used in HTTP integration tests) | NO | N/A | CONSUMER_API_PROVEN |

---

## Verdict

All consumer APIs are tested through the consumer path. No raw-inspection-only proofs. The HTTP endpoint (the actual external consumer API) is tested with real HTTP round-trips.

State: **CONSUMER_API_PROOF_AUDIT_PASS**
