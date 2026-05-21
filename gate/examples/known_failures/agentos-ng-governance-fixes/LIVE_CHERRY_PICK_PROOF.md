# Live Cherry-Pick Path Proof

**Date:** 2026-04-30
**Project:** `/tmp/agentos-ng-cherry-proof`
**Task:** tsk__79EIht "Add CHANGELOG entry with git commit"

## Setup

Project root checked out on `agentos-ng-integration` branch.
ORCH auto-merge target: `agentos-ng-integration`.
AgentOS-NG merge target: `main`.

## Step 1 — BEFORE state of main

```
63008fe Initial commit — cherry-pick proof project
```

Only the initial commit. `main` branch has no task commits.

## Step 2 — ORCH agent ran and committed

ORCH created worktree on branch `orchestry/tsk__79EIht/add-changelog-entry-with-git-commit`.
Agent modified README.md and committed:

```
commit f3505998fb341101f6cff7b0e0d5061f3de574ac
docs: add CHANGELOG section to README
```

## Step 3 — ORCH mergeBack() merged to agentos-ng-integration

Merge commit created on `agentos-ng-integration`:

```
ade86b9 Merge orchestry/tsk__79EIht/add-changelog-entry-with-git-commit
```

Agent's commit `f350599` is the `^2` parent of the merge commit.

## Step 4 — SHA extraction (path 3: proof.branch → merge commit → ^2)

`_extract_task_commit_sha()` extracted:
```
SHA: f3505998fb341101f6cff7b0e0d5061f3de574ac
```

Extraction path: `proof.branch` = `orchestry/tsk__79EIht/add-changelog-entry-with-git-commit`
→ `git log --all --grep <branch>` → merge commit `ade86b9`
→ `git rev-parse ade86b9^2` → `f3505998...`

## Step 5 — agentos-ng merge tsk__79EIht output

```
[merge] promoted to main: 1ccb8f3d98e3
Approving task tsk__79EIht via orchestry task approve...
✓ Approved tsk__79EIht
[merge] integration HEAD: ade86b95b7de

MERGED — task tsk__79EIht approved and merged. HEAD: ade86b95b7dedf6b810c44447bbfdf863dcdaf9e
```

## Step 6 — AFTER state of main

```
1ccb8f3 [agentos-ng] tsk__79EIht promoted to main
63008fe Initial commit — cherry-pick proof project
```

Task commit `f350599` (cherry-picked as `1ccb8f3`) is now on `main`.
ORCH task status: `done`.

## Bug found and fixed during live-path verification

**Bug:** `_cherry_pick_to_main()` used `git cherry-pick --no-ff <sha> -m <message>`.
`-m` in `git cherry-pick` is `--mainline` (expects a number), not a commit message flag.
This caused `error: option 'mainline' expects a number greater than zero`.

**Fix applied** (BLOCKER-CHERRY-BUG):
```python
# BEFORE (broken):
run_cmd(["git", "cherry-pick", "--no-ff", task_sha,
         "-m", f"[agentos-ng] {task_id} promoted to main"], cwd=root)

# AFTER (fixed):
run_cmd(["git", "cherry-pick", "--no-commit", task_sha], cwd=root)
run_cmd(["git", "commit", "-m", f"[agentos-ng] {task_id} promoted to main"], cwd=root)
```

Fix verified at `agentos_ng.py` lines 1486–1497.
Classifier tests: 17/17 PASS after fix.

## Verification summary

| Check | Result |
|-------|--------|
| ORCH agent ran and committed | PROVEN — f350599 on branch, ade86b9 merge commit |
| SHA extraction path 3 (proof.branch → ^2) | PROVEN — extracted f3505998... |
| _cherry_pick_to_main() succeeded | PROVEN — 1ccb8f3 on git log main |
| ORCH task approved to done | PROVEN — status=done |
| git log main BEFORE → AFTER | PROVEN — 1 new commit on main |
| Classifier tests after fix | 17/17 PASS |

## Conclusion

BLOCKER-CHERRY-C2 is resolved. The cherry-pick positive path (SHA extracted → cherry-pick runs → commit on main) has been live-demonstrated with real ORCH agent data. The SHA-not-found path is blocked by `return _block()` (code-verified, BLOCKER-SPLITBRAIN fix from Cycle 1). An additional bug was found and fixed: the `-m` flag misuse in `git cherry-pick`.
