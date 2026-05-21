# Concurrency Assumptions Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Systems with concurrency exposure

| System / module | Shared state? | Multi-process? | Multi-async-caller? |
|---|---|---|---|
| [module] | YES/NO | YES/NO | YES/NO |

---

## Concurrency model assessment

| Check | Answer | Evidence |
|---|---|---|
| 1 — Single-process or multi-process? | [single / multi / async-within-one] | [code/design note] |
| 2 — Sequential safe? (if single-process) | YES / NO / STATED | [assertion / lock / note] |
| 3 — Concurrent safe? (if multi-caller) | YES / NO | [lock type / evidence] |
| 4 — Idempotent? | YES / NO / N/A | [evidence or "not tested"] |
| 5 — Race condition risks | [list or "none identified"] | [analysis] |
| 6 — Explicit "not guaranteed" statements | [list or "none — add if needed"] | [doc location] |

---

## Race condition analysis

For each identified race condition risk:

**Race:** [description]
**When it occurs:** [two agents doing X and Y simultaneously]
**Failure mode:** SILENT_CORRUPTION / EXCEPTION / UNDEFINED / SAFE
**Mitigation present:** YES / NO — [describe or "none"]
**Action required:** [add lock / document limitation / add idempotency / etc.]

---

## Not-guaranteed statements

The following concurrency guarantees are explicitly NOT made by this system:

1. [guarantee not made — e.g., "not safe for concurrent writes"]
2. [guarantee not made]

These must be stated in the handoff.

---

## Verdict

| Check | Pass? | Notes |
|---|---|---|
| Sequential-safe assumption stated | YES/NO | — |
| Concurrent-safe claims have evidence | YES/NO | — |
| No undocumented race conditions | YES/NO | — |
| Not-guaranteed statements present | YES/NO | — |

```
CONCURRENCY_ASSUMPTIONS_AUDIT_PASS | CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL
```

**Rationale:** [one paragraph]
