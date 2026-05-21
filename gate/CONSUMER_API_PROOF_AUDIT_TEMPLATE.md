# Consumer-API Proof Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Consumer API surface

List every module, method, or endpoint added or changed by this task:

| API | File | Method signature or endpoint | Downstream caller(s) |
|---|---|---|---|
| [name] | [file:line] | [signature] | [who will call this] |

---

## Test assertion method table

For each test claimed as proof of a consumer API:

| Test file | Test name | What it calls/inspects | Consumer API path? | Raw inspection only? | Verdict |
|---|---|---|---|---|---|
| [test_file] | [test name] | [what is asserted] | YES / NO | YES / NO | CONSUMER_API_PROVEN / RAW_ONLY |

---

## Consumer API proof table

| Consumer API | Tested through consumer path? | Evidence file | Raw inspection also present? | Ordering/latest semantics tested? | Verdict |
|---|---|---|---|---|---|
| [API name] | YES / NO | [test file:line] | YES / NO | YES / NO / N/A | CONSUMER_API_PROVEN / RAW_ONLY / INSUFFICIENT |

---

## Raw-only test findings

For each test that uses only raw DB/file inspection:

**Test:** [test_file:test_name]
**What it asserts:** [SQL query / file read / direct object inspection]
**Consumer API that downstream will use:** [method name]
**Gap:** [what the raw inspection cannot prove that the consumer API might differ in]
**Verdict:** INSUFFICIENT — add consumer-API assertion

---

## Ordering / latest semantics

| API | Ordering claim | Tested? | Evidence |
|---|---|---|---|
| [API] | [returns latest / ordered by X] | YES / NO | [test file or "not tested"] |

---

## Verdict

**Total consumer APIs:** [count]
**Proven through consumer path:** [count]
**Raw-only (insufficient):** [count]

```
CONSUMER_API_PROOF_AUDIT_PASS | CONSUMER_API_PROOF_AUDIT_FAIL
```

**Rationale:** [one paragraph]
