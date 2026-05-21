# Step 30 — Diff Base / Scope Audit

**State machine:** Write `current_state: DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_STANDARD and GATE_FULL.**

**Skip for GATE_LITE.** Produce `DIFF_BASE_SCOPE_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

A diff that uses the wrong base commit will include unrelated changes (noise from old branches), miss actual changes (if base is too recent), or misrepresent what was changed. A diff that includes changes from other branches or prior unrelated work will mislead reviewers and gate checks into believing more was changed than the task actually touched.

---

## Output file

Copy `DIFF_BASE_SCOPE_AUDIT_TEMPLATE.md` to `reports/<task_area>/DIFF_BASE_SCOPE_AUDIT.md`.

Also update `reports/<task_area>/03_EVIDENCE_CONSISTENCY.md` (if using GATE_FULL) — append diff base verification result.
Also update `reports/<task_area>/15_FINAL_PACKAGE_AUDIT.md` — append diff scope verification.

---

## Checks

### Check 1 — Identify diff base and head

```bash
git rev-parse HEAD
git rev-parse [base_branch or base_commit]
git log --oneline [base]..[HEAD]
```

Record:
- `diff_base`: the commit or branch the diff was generated against
- `diff_head`: the current HEAD
- `task_branch`: the branch containing the task's work
- `target_branch`: the branch the task will merge into (e.g., `dev`, `main`)

### Check 2 — Verify diff base is correct

The diff base should be:
- The last commit on the target branch before the task branch diverged
- OR the merge-base of the task branch and the target branch

Correct base: `git merge-base [task_branch] [target_branch]`

If the diff base differs from `merge-base`: investigate whether the diff includes noise from other work.

### Check 3 — Verify diff does not include out-of-scope changes

Inspect the diff for files that are not in the task's allowed file-touch map:
```bash
git diff [base]..[HEAD] --name-only
```

If files outside the allowed touch map appear in the diff:
- Are they incidental test fixture changes? (may be OK)
- Are they changes from a prior unmerged branch that leaked into this diff? (blocker)
- Are they changes that should have been in a different task? (blocker)

### Check 4 — Verify diff matches final snapshots

The diff must show the same changes as the final changed-file snapshots:
1. For each file in the diff: verify the snapshot reflects the diff's final state
2. For each snapshot: verify it appears in the diff

If diff shows file A was changed but snapshot shows the original content: the snapshot is stale. Flag: `SNAPSHOT_CONTRADICTS_DIFF`.

### Check 5 — Verify diff does not include old branch noise

If the task branch was created from a stale base (not from the most recent commit on the target branch):
1. Check whether the diff includes commits that are already on the target branch
2. Check whether the diff includes commits from other unmerged features

---

## Hard rule

The gate must reject stale diffs that contradict final snapshots or include unrelated branch history. A diff that includes 500 lines of changes from a prior sprint that are not part of this task will cause all reviewers to draw incorrect conclusions.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Diff base correct, scope clean, no noise | `DIFF_BASE_SCOPE_AUDIT_PASS` | Continue |
| Stale diff or scope contamination | `DIFF_BASE_SCOPE_AUDIT_FAIL` | `FIX_CYCLE_IN_PROGRESS` (regenerate diff from correct base) |
