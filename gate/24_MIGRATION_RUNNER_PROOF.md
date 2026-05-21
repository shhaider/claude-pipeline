# Step 24 — Migration Runner Proof

**State machine:** Write `current_state: MIGRATION_RUNNER_PROOF_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory when the task involves any of the following:**
- SQL migration files
- Database schema changes
- Migration registry changes (e.g., `migrations/index.js`, `db/schema.rb`, `alembic/versions/`)
- Repositories or code that depends on new tables or columns

**Skip when:** No migrations present. Produce `MIGRATION_RUNNER_PROOF_NOT_APPLICABLE.md`.

---

## Why this step exists

A SQL file can be syntactically valid and manually applied to a dev database, yet still fail when the real migration runner runs it — because the runner has ordering constraints, a version registry, or naming conventions that the manual application bypassed. If the runner fails to discover, register, or apply the migration, the dependent code will fail at runtime with a schema error.

---

## Output file

Copy `MIGRATION_RUNNER_PROOF_TEMPLATE.md` to `reports/<task_area>/MIGRATION_RUNNER_PROOF.md`.

---

## Checks

### Check 1 — SQL file validity

Verify the SQL migration file:
1. Is syntactically valid SQL
2. Can be parsed by the migration runner's parser
3. Does not conflict with existing schema (table already exists, constraint name collision, etc.)

Manual validation: apply the SQL to a clean test database and confirm it succeeds with no errors.

### Check 2 — Real migration runner discovery

The migration runner must discover and queue the new migration file:
1. Run the migration runner's list/status command (e.g., `knex migrate:status`, `flyway info`, `python manage.py showmigrations`)
2. Verify the new migration file appears in the "pending" list
3. Record the exact command and output

If the migration file does not appear in the pending list: `MIGRATION_NOT_DISCOVERED` — check naming conventions, registry registration, or version number ordering.

### Check 3 — Real migration runner application

The migration runner must successfully apply the migration:
1. Run the migration runner's up/migrate command (e.g., `knex migrate:latest`, `flyway migrate`, `python manage.py migrate`)
2. Capture the exact output with EXIT_CODE
3. Verify the migration appears as "applied" in the runner's status afterward
4. Verify no warnings or errors in the output

### Check 4 — Migration registry update

If the project uses a migration registry file (e.g., `migrations/index.js` that requires all migration files), verify:
1. The new migration file is registered in the registry
2. The registry file is included in the task's file-touch map
3. The registry change is in the diff

### Check 5 — Dependent repository can use resulting schema

After the migration runner applies the migration:
1. Run the existing tests that depend on the new schema
2. Verify that repository methods can insert, query, and delete using the new columns/tables
3. Exit codes from these tests must be 0

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `MIGRATION_RUNNER_PROVEN` | Migration discovered, applied, and verified via real runner; dependent code passes |
| `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN` | SQL file is valid and manually applicable, but real runner discovery/application is unproven |
| `MIGRATION_BLOCKED` | Migration cannot be applied within scope (e.g., requires production DB access, or conflicts with existing schema that cannot be modified) |

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Migration runner proven | `MIGRATION_RUNNER_PROVEN` | Continue |
| SQL manually applied but runner not proven | `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN` | `FIX_CYCLE_IN_PROGRESS` (add runner proof) |
| Migration cannot be applied within scope | `MIGRATION_BLOCKED` | `BLOCKED_HANDOFF_COMPLETE` |
