# Fixture: dirty_git_status_active_parallel_work

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** PASS

## Why this fixture exists

Gate 5.2-R1 P04: The dirty-worktree label whitelist now accepts
`ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH` as a per-path classification, in addition to the
prior `UNRELATED_EXTERNAL_WORK`. Active parallel work (e.g. another agent or another
sprint actively editing those paths) is allowed if every dirty path is classified.

## Setup

`git_status_final.txt` lists 2 dirty entries; `DIRTY_WORKTREE_RECURRENCE.md`
classifies both as `ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH` with reasons.
