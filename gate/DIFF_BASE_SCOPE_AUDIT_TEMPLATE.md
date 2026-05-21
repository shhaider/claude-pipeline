# Diff Base / Scope Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Commit identity

| Item | Value |
|---|---|
| Current HEAD | [SHA] |
| Diff base (as used) | [SHA or branch name] |
| Task branch | [branch name] |
| Target branch | [dev / main / etc.] |
| Merge-base (correct base) | [SHA from `git merge-base`] |
| Diff base matches merge-base? | YES / NO |

---

## Files in diff

**Command:** `git diff [base]..[HEAD] --name-only`
```
[output]
```

---

## Scope check

| File in diff | In allowed touch map? | Reason for inclusion | Status |
|---|---|---|---|
| [file] | YES/NO | [task change / incidental fixture / noise from other branch] | OK / WARNING / BLOCKER |

**Out-of-scope files:** [count]

---

## Snapshot vs diff consistency

| File | In diff? | Snapshot exists? | Snapshot matches diff's final state? | Status |
|---|---|---|---|---|
| [file] | YES/NO | YES/NO | YES/NO | OK / SNAPSHOT_CONTRADICTS_DIFF |

---

## Old branch noise check

**Command:** `git log [target_branch]..[task_branch] --oneline`
```
[output — commits that are in task branch but not yet in target branch]
```

**All commits belong to this task:** YES / NO

If NO: [list commits that do not belong to this task and explain origin]

---

## Verdict

| Check | Result |
|---|---|
| 1 — Diff base identified | [correct SHA] |
| 2 — Diff base matches merge-base | YES / NO |
| 3 — No out-of-scope files | YES / NO — [count] out-of-scope |
| 4 — Snapshots match diff | YES / NO |
| 5 — No old branch noise | YES / NO |

```
DIFF_BASE_SCOPE_AUDIT_PASS | DIFF_BASE_SCOPE_AUDIT_FAIL
```

**Rationale:** [one paragraph]
