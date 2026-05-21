# Migration Runner Proof

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Migration files in this task

| File | Type | Status |
|---|---|---|
| [path/to/migration.sql] | SQL migration | [new / modified] |
| [path/to/registry.js] | Migration registry | [updated? YES/NO] |

---

## Check 1 — SQL file validity

**Validation method:** [manual application to test DB / SQL parser / etc.]

**Command:**
```sql
-- applied to: [database name / type]
[SQL content summary — do not paste full SQL if large]
```

**Result:** PASS / FAIL

**Errors:** [none / list errors]

---

## Check 2 — Real migration runner discovery

**Migration runner:** [knex / flyway / alembic / django / other]

**Status command:**
```bash
[exact command, e.g.: knex migrate:status]
```

**Output:**
```
[exact output showing the new migration in "pending" list]
EXIT_CODE: [0/1]
```

**New migration appears in pending list:** YES / NO

If NO: **Reason:** [naming convention mismatch / not registered / version order conflict]

---

## Check 3 — Real migration runner application

**Apply command:**
```bash
[exact command, e.g.: knex migrate:latest]
```

**Output:**
```
[exact output]
EXIT_CODE: [0/1]
```

**Post-apply status:**
```bash
[status command again, showing migration as "applied"]
EXIT_CODE: [0/1]
```

**Warnings or errors in output:** [none / list]

---

## Check 4 — Migration registry update

**Registry file:** [path or "N/A — no registry used"]

**New migration registered:** YES / NO / N/A

**Registry change in diff:** YES / NO / N/A

---

## Check 5 — Dependent repository test

**Test command:**
```bash
[npx jest tests/repositories/users.test.js, etc.]
```

**Output file:** [path to raw output]
**EXIT_CODE:** [0/1]
**Test count:** [X passed, Y failed]

---

## Verdict

| Check | Result |
|---|---|
| 1 — SQL validity | PASS / FAIL |
| 2 — Runner discovery | PASS / FAIL / MIGRATION_NOT_DISCOVERED |
| 3 — Runner application | PASS / FAIL |
| 4 — Registry update | PASS / FAIL / N/A |
| 5 — Repository test | PASS / FAIL |

```
MIGRATION_RUNNER_PROVEN | SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN | MIGRATION_BLOCKED
```

**Rationale:** [one paragraph]
