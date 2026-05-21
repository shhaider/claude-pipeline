# Fixture: dirty_git_status_unknown_requires_human

**Profile:** GATE_FULL
**Risk tier:** D3
**Task kind:** merge_verification
**Expected verdict:** FAIL with `UNKNOWN_REQUIRES_HUMAN_BLOCKER`

## Why this fixture exists

Gate 5.2-R1 P04: A dirty path explicitly classified `UNKNOWN_REQUIRES_HUMAN` is BLOCKING.
This is the escape hatch for a row the agent could not classify on its own — the gate
must surface it to a human, not auto-pass.

## Setup

`git_status_final.txt` lists 1 dirty entry; `DIRTY_WORKTREE_RECURRENCE.md`
classifies it as `UNKNOWN_REQUIRES_HUMAN`.
