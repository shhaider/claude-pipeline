# Downstream Consumer Readiness Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Next-phase consumers

| Consumer | Type | Depends on |
|---|---|---|
| [consumer name] | [next sprint / downstream service / test suite / human] | [what it needs from this task] |

---

## API contract check

| API / export | Consumer expects | Actual name/path/shape | Match? | Notes |
|---|---|---|---|---|
| [function] | [expected name] | [actual name] | YES/NO | [breaking change if NO] |
| [module path] | [expected path] | [actual path] | YES/NO | [path mismatch if NO] |
| [response field] | [expected field] | [actual field] | YES/NO | [field missing if NO] |

---

## Breaking change check

| Changed item | Old value | New value | Callers affected | Impact |
|---|---|---|---|---|
| [function name] | [old signature] | [new signature] | [caller list] | BREAKING / NON_BREAKING |
| [config key] | [old key] | [new key or removed] | [users] | BREAKING / NON_BREAKING |

---

## Required artifact check

| Artifact | Required by consumer | Path | Exists? | Correct format? |
|---|---|---|---|---|
| [artifact] | [consumer] | [path] | YES/NO | YES/NO |

---

## Caveats (if DOWNSTREAM_READY_WITH_CAVEAT)

1. [caveat — e.g., "Consumer must update import path from X to Y"]
2. [caveat]

---

## Verdict

```
DOWNSTREAM_READY | DOWNSTREAM_READY_WITH_CAVEAT | DOWNSTREAM_NOT_READY
```

**Rationale:** [one paragraph]

**Blockers (if DOWNSTREAM_NOT_READY):**
1. [blocker]
2. [blocker]
