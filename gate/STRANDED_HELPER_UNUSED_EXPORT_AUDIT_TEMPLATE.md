# Stranded Helper / Unused Export Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## New symbols added by this task

| Symbol / file | Type | Defined in | Exported? |
|---|---|---|---|
| [name] | function / class / module / agent / registry entry | [file:line] | YES / NO |

---

## Caller search results

For each new symbol:

**Symbol:** [name]
**Defined in:** [file:line]

**Production caller search:**
```bash
grep -RIn "[symbol_name]" src/ app/ lib/ | grep -v "test\|spec"
# Output: [exact output or "no matches"]
```

**Test caller search:**
```bash
grep -RIn "[symbol_name]" tests/ __tests__/ | grep -v "node_modules"
# Output: [exact output or "no matches"]
```

---

## Stranded helper / unused export table

| New symbol/file | Defined in | Production caller | Test caller | Downstream consumer | Stranded? | Verdict |
|---|---|---|---|---|---|---|
| [name] | [file:line] | [caller or "none"] | [test file or "none"] | [consumer or "none"] | YES/NO | PRODUCTION_WIRED / INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY / STRANDED_UNUSED |

---

## Stranded symbols (requiring action)

For each stranded or overclaimed symbol:

**Symbol:** [name]
**Current label in handoff:** [what the handoff claims]
**Correct label:** INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY / STRANDED_UNUSED
**Action required:** [correct the label / add production caller / delete dead code]

---

## Summary

| Verdict | Count |
|---|---|
| PRODUCTION_WIRED | [count] |
| INFRASTRUCTURE_READY_NOT_WIRED | [count] |
| TEST_HELPER_ONLY | [count] |
| STRANDED_UNUSED | [count] |

**Blocking findings (STRANDED_UNUSED or overclaims):** [count]

---

## Verdict

```
STRANDED_HELPER_AUDIT_PASS | STRANDED_HELPER_AUDIT_FAIL
```

**Rationale:** [one paragraph]
