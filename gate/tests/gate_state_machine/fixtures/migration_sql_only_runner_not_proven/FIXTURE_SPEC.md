# Fixture: migration_sql_only_runner_not_proven

## Setup

- Task: "Add `session_id` column to `memories` table"
- SQL file: `migrations/20260501_add_session_id_to_memories.sql`
- `MIGRATION_RUNNER_PROOF.md` shows:
  - Check 1 (SQL validity): PASS — applied manually with `psql -f migration.sql`
  - Check 2 (Runner discovery): NOT RUN — "Runner discovery skipped, manual application sufficient"
  - Check 3 (Runner application): NOT RUN
  - Verdict: MIGRATION_RUNNER_PROVEN (incorrect — should be SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN)
- The project uses Knex as migration runner
- `migrations/index.js` (the Knex migration registry) was NOT updated to include the new file
- `knex migrate:status` would NOT show this migration as pending (it is undiscovered)
- `CURRENT_STATE.yaml` records `migration_runner_proof_result: MIGRATION_RUNNER_PROVEN` (incorrect)

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Migration runner not proven:
       MIGRATION_RUNNER_PROOF.md: Runner discovery check: NOT RUN
       MIGRATION_RUNNER_PROOF.md: Runner application check: NOT RUN
       MIGRATION_RUNNER_PROOF.md verdict: MIGRATION_RUNNER_PROVEN (contradicts checks above)
       Correct verdict: SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN
       Invariant violated: migration_runner_discovery_proven
[FAIL] Migration registry not updated:
       migrations/index.js not in task file-touch map
       Knex will not discover 20260501_add_session_id_to_memories.sql
       Consequence: schema divergence between dev and production at next deployment
```

## Expected invariant

`migration_runner_discovery_proven`

## Why this matters

The SQL is valid. The column was added to the dev database. But when this code is deployed,
`knex migrate:latest` will not run this migration because the registry does not include it.
The production database will be missing the `session_id` column. Every query that references
it will fail with a column-not-found error.
