# Fixture: dirty_git_status_unclassified_paths

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** FAIL with `DIRTY_PATH_NOT_CLASSIFIED`

## Why this fixture exists

Gate 5.2-R1 P04: A `DIRTY_WORKTREE_RECURRENCE.md` file exists, but it does not include
every dirty path from `git_status_final.txt`. The unclassified path must block.

## Setup

`git_status_final.txt` lists 2 dirty entries; `DIRTY_WORKTREE_RECURRENCE.md`
classifies only one of them.
