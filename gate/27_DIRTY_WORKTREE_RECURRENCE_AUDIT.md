# Step 27 — Dirty Worktree Recurrence Audit

**State machine:** Write `current_state: DIRTY_WORKTREE_RECURRENCE_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_FULL.** Optional for GATE_STANDARD.

**Skip for GATE_LITE.** Produce `DIRTY_WORKTREE_RECURRENCE_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

When the same path shows up as uncommitted/untracked in multiple gate runs, it indicates a systemic problem:
- A file that is generated during the task but not gitignored
- A report file that is always re-generated and dirtied
- An artifact that belongs outside the repo but keeps appearing inside it

If these are treated as one-off issues each time, they will recur indefinitely. This audit checks whether any currently dirty path has appeared before and requires a follow-up hygiene task if so.

---

## Output file

Copy `DIRTY_WORKTREE_RECURRENCE_TEMPLATE.md` to `reports/<task_area>/DIRTY_WORKTREE_RECURRENCE.md`.

---

## Step 1 — Run git status

```bash
git status --short
```

Record every path that appears (modified, untracked, etc.).

## Step 2 — Check against recurrence register

The recurrence register lives at `gate/DIRTY_WORKTREE_RECURRENCE_REGISTER.md` (or the task-area-specific equivalent). Check each currently-dirty path against the register.

## Step 3 — Seed common known paths

These paths are known to recur. Add to the register if not already present:

| Path | Likely source |
|---|---|
| `docs/DOC_FRESHNESS_REPORT.md` | Auto-generated doc freshness report |
| `node_modules/` | npm install artifacts |
| `.run_artifacts/` | Test runner output directory |
| `raw_outputs/` | Evidence artifact directory |
| `reports/` (if not gitignored) | Gate report directory |
| `*.zip` in root | Package signout zip |
| `PACKAGE_MANIFEST.md` | Package manifest generated in repo root |
| `PACKAGE_FILE_LISTING.txt` | Package listing generated in repo |

## Step 4 — Check recurrence count

For each currently-dirty path found in the register:
- If `recurrence_count >= 2`: this is a recurring dirty path
- Add a follow-up hygiene issue/task to `ROADMAP_ADDITIONS.md` if not already tracked

## Step 5 — Update the register

For each currently-dirty path:
- If new (not in register): add it with `first_seen = now`, `recurrence_count = 1`
- If existing: increment `recurrence_count`, update `last_seen`

---

## Hard rule

If the same path dirties the repo twice across separate gate runs, a follow-up hygiene issue must be created and tracked — not treated as a one-off each time. Recurring dirty paths without a hygiene tracking ticket are a blocker.

---

## Required table

| Path | First seen | Recurrence count | Likely source | Current policy | Follow-up ticket |
|---|---|---|---|---|---|
| [path] | [date] | [N] | [source] | [gitignore / out-of-repo / committed] | [ticket ID or "needs creation"] |

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| No recurring dirty paths, or all have hygiene tickets | `DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS` | Continue |
| Recurring dirty path without hygiene ticket | `DIRTY_WORKTREE_RECURRENCE_BLOCKER` | `FIX_CYCLE_IN_PROGRESS` (create hygiene ticket) |
