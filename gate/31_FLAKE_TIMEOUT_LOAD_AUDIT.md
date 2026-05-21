# Step 31 — Flake / Timeout / Load Sensitivity Audit

**State machine:** Write `current_state: FLAKE_TIMEOUT_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_FULL.** Optional for GATE_STANDARD.

**Skip for GATE_LITE.** Produce `FLAKE_TIMEOUT_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

A test that passes under low load but fails under high load is not a stable proof. A test with an arbitrary timeout that passes when the system is fast but fails during nightly CI is not a reliable regression guard. These tests create false confidence — they pass now, but they will randomly fail in production CI, during benchmark runs, or on a stressed server.

---

## Output file

Copy `FLAKE_TIMEOUT_LOAD_AUDIT_TEMPLATE.md` to `reports/<task_area>/FLAKE_TIMEOUT_AUDIT.md`.

Also update `reports/<task_area>/TEST_AND_EVIDENCE_PLAN.md` (append flake assessment if test plan exists).
Also update `reports/<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` (append flake findings).

---

## Checks

### Check 1 — Identify time-sensitive assertions

Scan test files for:
- `setTimeout` / `setInterval` with hard-coded durations in assertion paths
- `sleep()` or `await delay()` between actions and assertions
- `waitFor()` with short timeouts (< 500ms for I/O operations)
- Timestamps compared with equality rather than range
- Assertions that depend on task scheduling order without explicit synchronization

### Check 2 — Identify load-sensitive assumptions

Scan test files for:
- Tests that pass only when no other tests are running concurrently (uses a shared port, shared file, shared DB table)
- Tests that assume a specific response time from a real network/DB call
- Tests that assume Ollama/LLM response arrives within N seconds
- Tests that start a server on a fixed port (EADDRINUSE failure)

### Check 3 — Identify retry or flake patterns

Check test run history (if available) or inspect test code for:
- Tests with explicit retry logic (masking intermittent failures)
- Tests marked `.skip` that were previously flaky
- Tests with `jest.setTimeout(10000)` or similar long timeouts that suggest prior flakiness

### Check 4 — VPS load check

If tests run on VPS: check whether the current server load would affect test stability.
```bash
cat /proc/loadavg && free -h && nproc
```

If load is high: flag `TESTS_RUN_UNDER_HIGH_LOAD` — results may not be reproducible.

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `TEST_STABILITY_OK` | No timing-sensitive or load-sensitive issues found |
| `TEST_STABILITY_WARNING_FOLLOWUP` | Minor timing sensitivity found; tests passed but a follow-up task should address stability |
| `TEST_STABILITY_BLOCKING` | Tests are fundamentally unstable; this handoff cannot claim these tests as proof |

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| No instability found | `TEST_STABILITY_OK` | Continue |
| Minor sensitivity — follow-up recommended | `TEST_STABILITY_WARNING_FOLLOWUP` | Continue (with warning) |
| Fundamental instability | `TEST_STABILITY_BLOCKING` | `FIX_CYCLE_IN_PROGRESS` |
