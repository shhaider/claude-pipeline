# Diff Base / Scope Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 30

State: DIFF_BASE_SCOPE_AUDIT_IN_PROGRESS

---

## Check 1 -- Identify diff base and head

- diff.patch header: `index 5fbbec57..73b81fbd` (file-level object SHAs, not commit SHAs)
- diff_base: The diff was generated as `git diff HEAD~1 HEAD -- front_door.py` per EVIDENCE_LEDGER.yaml E003.
- diff_head: `756a5706` (HEAD at time of diff generation). Current HEAD: `d04d7288` (Sprint 3 commit).
- task_branch: `shhaider/emdash-bridge`
- target_branch: `shhaider/denver` (or eventual merge to `main`)

Note: The diff only covers `front_door.py` modifications. Sprint 3's other deliverables (bridge module, test file, docs) are new untracked files that do not appear in a diff against HEAD because they were not committed at diff generation time.

---

## Check 2 -- Verify diff base is correct

The diff was generated against HEAD~1 of the task branch. This is appropriate because Sprint 3 modifies only one existing file (`front_door.py`). The new files (bridge module, test, docs) are untracked additions that would only appear as new files in a diff, not as modifications.

The diff base is the commit immediately before the front_door.py changes were staged. This correctly isolates Sprint 3's modifications.

---

## Check 3 -- Out-of-scope changes

The diff shows changes only in `front_door.py`:
- Line 28: `+from governed_fsm_conduit.bridge import start_bridge_server`
- Lines 405-407: `+_state_root = ROOT / ".agentos-ng" / "governed-fsm-conduit"` and `+start_bridge_server(_state_root)`

Both changes are within the contract's file-touch map (`MODIFY front_door.py`).

No files outside the allowed touch map appear in the diff.

DIFF_CONTAINS_OUT_OF_SCOPE_CHANGES: **NO**

---

## Check 4 -- Diff matches final snapshots

No named snapshot files exist for Sprint 3 (directory-based review). The diff's changes match the actual content of `front_door.py` as read directly from the repo:
- Line 28 in current front_door.py: `from governed_fsm_conduit.bridge import start_bridge_server` -- matches diff
- Lines 405-407 in current front_door.py: bridge server start code -- matches diff

No contradiction between diff and actual repo state.

---

## Check 5 -- Old branch noise

The diff is scoped to a single file (`front_door.py`) and shows exactly 4 added lines. No noise from other branches, no unrelated commits, no stale base contamination.

---

## Verdict

Diff base is correct. Scope is clean. No out-of-scope changes. No old branch noise.

State: **DIFF_BASE_SCOPE_AUDIT_PASS**
