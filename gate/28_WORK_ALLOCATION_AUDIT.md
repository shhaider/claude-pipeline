# Step 28 — Work Allocation / Hot File Conflict Audit

**State machine:** Write `current_state: WORK_ALLOCATION_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory when any of the following are true:**
- Multiple agents are active concurrently
- The task touches hot files
- The shared `dev` branch is currently dirty or has uncommitted work
- Branch/worktree coordination is required
- The task's file-touch map overlaps with another known active task's file-touch map

**Skip when:** Single agent, no hot files, clean branch, no known concurrent tasks. Produce `WORK_ALLOCATION_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

Two agents modifying the same file concurrently will produce conflicts. The later agent will overwrite the earlier agent's work, or one will read a stale version of the file. Hot files (LLM routing, gate logic, migrations) are especially dangerous because small conflicts can cause silent behavioral changes.

---

## Output file

Copy `WORK_ALLOCATION_AUDIT_TEMPLATE.md` to `reports/<task_area>/WORK_ALLOCATION_AUDIT.md`.

---

## Checks

### Check 1 — Active agents

List all currently active agents and their task scopes. This requires checking:
- The orchestrator's active task list
- Any known spawned subagents
- Any background processes

### Check 2 — File-touch map overlap

For each other active agent:
1. List its file-touch map (if known)
2. Check if any files overlap with the current task's file-touch map
3. If overlap on a non-hot file: flag as WARNING
4. If overlap on a hot file: flag as CONFLICT

### Check 3 — Branch/worktree state

```bash
git status --short
git stash list
git worktree list
```

If the shared branch has uncommitted changes from another task:
1. Identify which task left the changes
2. Determine whether they should be committed first or stashed

### Check 4 — Hot file lock check

If the task touches hot files:
1. Is there a lock/flag mechanism for hot files in this project? (advisory locks, worktree isolation)
2. Is the hot file currently being modified by another task?
3. If yes: conflict — must isolate in task worktree or wait for the other task to complete

---

## Output verdicts

| Verdict | Meaning |
|---|---|
| `WORK_ALLOCATION_CLEAR` | No conflicts; no concurrent tasks on same files; proceed normally |
| `WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE` | Conflicts exist but can be resolved by working in a dedicated task worktree; proceed in isolation |
| `WORK_ALLOCATION_BLOCKED_BY_CONFLICT` | Active conflict that cannot be resolved without stopping one of the conflicting tasks |
| `WORK_ALLOCATION_NEEDS_HUMAN` | Conflict resolution requires human decision (e.g., which task's changes take precedence) |

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Clear | `WORK_ALLOCATION_CLEAR` | Continue |
| Isolate in worktree | `WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE` | Continue (in task worktree) |
| Blocked by conflict | `WORK_ALLOCATION_BLOCKED_BY_CONFLICT` | `BLOCKED_HANDOFF_COMPLETE` |
| Needs human | `WORK_ALLOCATION_NEEDS_HUMAN` | Return to operator with conflict description |
