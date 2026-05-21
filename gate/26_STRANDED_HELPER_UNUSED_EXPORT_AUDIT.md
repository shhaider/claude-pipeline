# Step 26 — Stranded Helper / Unused Export Scan

**State machine:** Write `current_state: STRANDED_HELPER_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_STANDARD and GATE_FULL when:** The task adds new helpers, exports, agents, prompts, catalogs, registries, or strategy modules.

**Skip when:** The task adds no new exported symbols and no new files. Produce `STRANDED_HELPER_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

A helper used only by tests is not production wiring — it is a test infrastructure addition. A module that is exported but never imported by production code is stranded. If the handoff claims these symbols are "production wired" or "live," it is overclaiming. The correct label is `INFRASTRUCTURE_READY_NOT_WIRED` or `TEST_HELPER_ONLY`.

---

## Output file

Copy `STRANDED_HELPER_UNUSED_EXPORT_AUDIT_TEMPLATE.md` to `reports/<task_area>/STRANDED_HELPER_AUDIT.md`.

---

## Required table

| New symbol/file | Defined in | Production caller | Test caller | Downstream consumer | Stranded? | Verdict |
|---|---|---|---|---|---|---|
| [function/class/module] | [file:line] | [caller path or "none"] | [test file or "none"] | [consumer module or "none"] | YES / NO | PRODUCTION_WIRED / INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY / STRANDED_UNUSED |

---

## Identification step

List every new symbol or file added by this task:

1. New exported functions
2. New exported classes
3. New modules (new files with any exports)
4. New agents or prompts registered in a catalog
5. New entries in a registry or strategy table
6. New helper files

For each symbol: search for all callers (production and test).

---

## Production caller search

For each new symbol:

```bash
grep -RIn "[symbol_name]" src/ app/ lib/ --include="*.js" --include="*.ts" | grep -v "test\|spec\|__mocks__"
```

If output is empty: no production callers. Mark `stranded: YES`.

If output shows callers: record the caller paths and trace upward to a production entry point.

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `PRODUCTION_WIRED` | Symbol has a production caller reachable from a live entry point |
| `INFRASTRUCTURE_READY_NOT_WIRED` | Symbol exists, tests pass, but no production caller yet — this is explicit infrastructure work |
| `TEST_HELPER_ONLY` | Symbol is imported only by test files; intentional test infrastructure |
| `STRANDED_UNUSED` | Symbol has no callers at all (not production, not test) — dead code |

---

## Hard rules

1. A helper used only by tests is not production wiring — even if the task claimed to produce production wiring.
2. `INFRASTRUCTURE_READY_NOT_WIRED` is an acceptable final status only if the task prompt explicitly acknowledged that wiring would occur in a subsequent sprint.
3. `STRANDED_UNUSED` is always a blocker — adding dead code is not acceptable unless the task explicitly creates a documented infrastructure placeholder.
4. Infrastructure-only final handoff must use `INFRASTRUCTURE_READY_NOT_WIRED`, not `LIVE_BEHAVIOR_FIXED`.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| All new symbols have production callers OR are explicitly infrastructure/test-only | `STRANDED_HELPER_AUDIT_PASS` | `R4_IN_PROGRESS` |
| Any new symbol is stranded or overclaimed | `STRANDED_HELPER_AUDIT_FAIL` | `FIX_CYCLE_IN_PROGRESS` |
