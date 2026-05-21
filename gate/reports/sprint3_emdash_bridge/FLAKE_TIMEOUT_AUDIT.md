# Flake / Timeout / Load Sensitivity Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 31

State: FLAKE_TIMEOUT_AUDIT_IN_PROGRESS

---

## Check 1 -- Time-sensitive assertions

Scanning `tests/test_bridge.py` for time-sensitive patterns:

| Pattern | Found? | Location | Assessment |
|---|---|---|---|
| `setTimeout` / `setInterval` | NO | N/A | Python tests, not JavaScript |
| `sleep()` / `time.sleep()` | YES | test_bridge.py:163, 172 | `time.sleep(0.05)` -- 50ms pause after starting HTTP server before sending request. This is a startup wait, not a timing assertion. |
| `waitFor()` with short timeouts | NO | N/A | Not used |
| Timestamp equality comparison | NO | N/A | Not used |
| Scheduling-order-dependent assertions | NO | N/A | Not used |

The `time.sleep(0.05)` calls are server startup waits. They give the daemon thread time to bind the socket before the test sends its HTTP request. 50ms is generous for local socket binding. This is unlikely to flake.

Risk level: LOW. Socket binding on localhost is near-instant. 50ms is conservative.

---

## Check 2 -- Load-sensitive assumptions

| Pattern | Found? | Location | Assessment |
|---|---|---|---|
| Shared port | NO | `port=0` used in tests -- OS assigns ephemeral port | No EADDRINUSE risk |
| Shared file | NO | `tmp_path` provides isolated directory per test | No cross-test contamination |
| Shared DB table | NO | N/A -- no database | N/A |
| Network response time dependency | NO | All tests use localhost HTTP | Near-zero network latency |
| LLM response time dependency | NO | No LLM calls in bridge code | N/A |
| Fixed port server | NO | `port=0` everywhere in tests | Correct |

---

## Check 3 -- Retry/flake patterns

| Pattern | Found? | Assessment |
|---|---|---|
| Explicit retry logic | NO | Tests run once |
| Tests marked .skip for flakiness | NO | The 1 skipped test is intentional (no tool_closed policy) |
| Long timeout overrides | NO | Default pytest timeout |

---

## Check 4 -- VPS load check

Tests run on Mac locally, not on VPS. No VPS load concern.

---

## Verdict

No timing-sensitive assertions. No load-sensitive assumptions. Port=0 eliminates EADDRINUSE risk. tmp_path eliminates cross-test contamination. The 50ms sleep is conservative for local socket binding.

State: **TEST_STABILITY_OK**
