# Work Allocation / Hot File Conflict Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Current task file-touch map

| File | Hot file? | Risk if conflict |
|---|---|---|
| [file] | YES/NO | [HIGH/MED/LOW] |

---

## Active agents

| Agent ID | Task scope | File-touch map (if known) | Overlap with current task? |
|---|---|---|---|
| [agent_id] | [task description] | [files] | YES/NO |
| OR: No other agents known to be active |

---

## File-touch map overlap

| Overlapping file | Current task | Other agent | Conflict severity |
|---|---|---|---|
| [file] | [what current task does to it] | [what other agent does to it] | HOT_FILE_CONFLICT / WARNING / NONE |

---

## Branch/worktree state

**Command:** `git status --short`
```
[output]
```

**Command:** `git worktree list`
```
[output]
```

**Uncommitted changes from other tasks:** YES / NO

If YES: [describe what changes are present and which task left them]

---

## Hot file lock check

**Hot files in this task's touch map:** [list or "none"]

**Lock mechanism in project:** YES / NO / [description]

**Hot files currently being modified by other tasks:** YES / NO

If YES: [which file, which task]

---

## Verdict

```
WORK_ALLOCATION_CLEAR | WORK_ALLOCATION_ISOLATE_IN_TASK_WORKTREE | WORK_ALLOCATION_BLOCKED_BY_CONFLICT | WORK_ALLOCATION_NEEDS_HUMAN
```

**Rationale:** [one paragraph]

**Required action (if not CLEAR):** [what must happen before work can proceed]
