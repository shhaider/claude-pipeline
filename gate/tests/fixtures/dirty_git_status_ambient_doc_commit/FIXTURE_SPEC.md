# Fixture: dirty_git_status_ambient_doc_commit

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** PASS

## Why this fixture exists

Gate 5.2-R1 P04: `AMBIENT_UNRELATED_DOC_COMMIT` is added as an approved label —
documentation that was committed alongside but unrelated to the audited change.

## Setup

`git_status_final.txt` lists 1 dirty entry; `DIRTY_WORKTREE_RECURRENCE.md`
classifies it as `AMBIENT_UNRELATED_DOC_COMMIT` with a reason.
