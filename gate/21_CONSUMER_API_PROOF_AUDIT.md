# Step 21 — Consumer-API Proof Audit

**State machine:** Write `current_state: CONSUMER_API_PROOF_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_STANDARD and GATE_FULL when:** The task adds repository methods, helper APIs, or any module that downstream code will call via an API rather than inspecting raw DB/file state directly.

**Skip for GATE_LITE.** Produce `CONSUMER_API_PROOF_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

Raw DB or file inspection in tests can pass even when the consumer API is broken. If downstream code calls `userRepo.findById(id)` but the test asserts by running `SELECT * FROM users WHERE id = ?` directly, the test proves the DB row exists — but not that `userRepo.findById` works correctly. The consumer-API path may have different error handling, caching, transformation, or access control logic.

---

## Output file

Copy `CONSUMER_API_PROOF_AUDIT_TEMPLATE.md` to `reports/<task_area>/CONSUMER_API_PROOF_AUDIT.md`.

---

## Checks

### Check 1 — What API will downstream code call?

For each module, method, or helper added or changed:
1. Identify the public API surface (exported functions, class methods, REST endpoints)
2. Identify how downstream code is expected to call this API (function call, HTTP request, message dispatch)
3. Record this as the "consumer API path"

### Check 2 — Did tests assert through the consumer API?

For each test that is claimed as proof:
1. Identify what the test calls or inspects
2. Is it calling the consumer API (the same path downstream code will use)?
3. Or is it directly inspecting the DB/file/in-memory state?

If the test bypassed the consumer API (raw inspection), record it.

### Check 3 — Is raw inspection also present?

Raw DB/file inspection is useful but insufficient on its own. Check whether:
- The test has BOTH consumer-API assertion AND raw inspection (this is acceptable — belt-and-suspenders)
- The test has ONLY raw inspection (this is insufficient — consumer API path is unproven)

### Check 4 — Does future code rely on ordering or "latest" semantics not tested by raw inspection?

Examples:
- A query that returns results ordered by `created_at DESC` — raw inspection of a single row does not prove ordering
- A cache that returns the most recently written value — direct memory/file inspection does not prove cache eviction behavior
- A repository method that applies a transform or filter — raw DB row does not prove the transform is applied

---

## Required table

| Consumer API | What downstream code calls | Tested through consumer API? | Raw inspection only? | Ordering/latest semantics tested? | Verdict |
|---|---|---|---|---|---|
| [method/endpoint] | [how it will be called] | YES / NO | YES / NO | YES / NO / N/A | CONSUMER_API_PROVEN / RAW_ONLY / INSUFFICIENT |

---

## Hard rule

Raw DB/file inspection is useful for debugging and sanity-checking but is **insufficient as the sole proof** if downstream code will use a repository/helper/API method. The consumer-API path must also be tested — because that path may have different behavior.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| All consumer APIs tested through consumer path | `CONSUMER_API_PROOF_AUDIT_PASS` | `R3_IN_PROGRESS` |
| One or more consumer APIs proven only by raw inspection | `CONSUMER_API_PROOF_AUDIT_FAIL` | `FIX_CYCLE_IN_PROGRESS` (add consumer-API assertions) |
