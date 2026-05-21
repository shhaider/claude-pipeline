# Change Manifest

**Task:** agentos-ng-governance-fixes (5 ORCH/AgentOS-NG governance blockers)
**Date:** 2026-04-30
**Note:** Implementation files are in `/Users/syedhaider/.codex/agentos_ng/` which is git-excluded by `.codex/.gitignore` (`*` pattern whitelists only AGENTS.md and project_os/). Therefore no `git diff` is available. This document serves as the authoritative change record, verified by direct code inspection.

---

## File: agentos_ng.py (2076 lines total)

### Change 1 — New constant: INTEGRATION_BRANCH (line 37)

**Location:** Line 37, after existing constants (ORCHESTRY_DIR, etc.)

**Added:**
```python
INTEGRATION_BRANCH = "agentos-ng-integration"
```

**Purpose:** BLOCKER 1 — names the integration branch that ORCH auto-merges into. The project root must be checked out to this branch so ORCH's `mergeBack()` merges task branches into integration (not main).

---

### Change 2 — New function: `_ensure_integration_branch()` (lines 1456–1475)

**Location:** Added after `_extract_task_commit_sha()` function.

**Added:**
```python
def _ensure_integration_branch(root: Path) -> bool:
    """Switch to integration branch, creating it from main if needed."""
    rc_cur, current, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    current = current.strip() if rc_cur == 0 else ""
    if current == INTEGRATION_BRANCH:
        return True
    rc_ver, _, _ = run_cmd(["git", "rev-parse", "--verify", INTEGRATION_BRANCH], cwd=root)
    if rc_ver != 0:
        rc_br, _, err_br = run_cmd(["git", "branch", INTEGRATION_BRANCH, "main"], cwd=root)
        if rc_br != 0:
            print(f"[integration] failed to create {INTEGRATION_BRANCH}: {err_br}", file=sys.stderr)
            return False
    rc_co, _, err_co = run_cmd(["git", "checkout", INTEGRATION_BRANCH], cwd=root)
    if rc_co != 0:
        print(f"[integration] failed to checkout {INTEGRATION_BRANCH}: {err_co}", file=sys.stderr)
        return False
    print(f"[integration] switched to {INTEGRATION_BRANCH}")
    return True
```

**Purpose:** BLOCKER 1 — utility to set up the integration branch architecture on a new project root.

---

### Change 3 — New function: `_cherry_pick_to_main()` (lines 1478–1497)

**Location:** Added after `_ensure_integration_branch()`.

**Added:**
```python
def _cherry_pick_to_main(task_sha: str, task_id: str, root: Path) -> int:
    """Cherry-pick a specific commit from integration branch to main.
    Switches to main, cherry-picks, then switches back to INTEGRATION_BRANCH."""
    rc_co, _, err_co = run_cmd(["git", "checkout", "main"], cwd=root)
    if rc_co != 0:
        print(f"[merge] cannot checkout main: {err_co}", file=sys.stderr)
        return rc_co
    rc_cp, out_cp, err_cp = run_cmd(
        ["git", "cherry-pick", "--no-ff", task_sha,
         "-m", f"[agentos-ng] {task_id} promoted to main"],
        cwd=root,
    )
    if rc_cp != 0:
        print(f"[merge] cherry-pick failed: {err_cp}", file=sys.stderr)
        run_cmd(["git", "cherry-pick", "--abort"], cwd=root)
    run_cmd(["git", "checkout", INTEGRATION_BRANCH], cwd=root)
    return rc_cp
```

**Purpose:** BLOCKER 1 — the only path that promotes a task commit from integration to main. Called by `cmd_merge()` only after validate + MCO review both pass.

---

### Change 4 — Updated `cmd_merge()`: cherry-pick before ORCH approve (lines 1711–1724)

**Location:** Inside `cmd_merge()`, after MCO review check, before `orchestry task approve`.

**Added (before the existing `orchestry task approve` call):**
```python
# Promote to main via cherry-pick — AgentOS-NG is the only path to main
task_sha = _extract_task_commit_sha(task_id, root)
if task_sha:
    rc_cp = _cherry_pick_to_main(task_sha, task_id, root)
    if rc_cp != 0:
        return _block(
            f"BLOCKED — cherry-pick of {task_sha[:8]} to main failed. "
            f"Resolve conflicts then retry."
        )
    _, head_main, _ = run_cmd(["git", "rev-parse", "main"], cwd=root)
    print(f"[merge] promoted to main: {head_main.strip()[:12]}")
else:
    print(f"[merge] WARNING: could not extract task commit SHA — skipping cherry-pick to main", file=sys.stderr)
```

**Purpose:** BLOCKER 1 — when SHA is available (real ORCH agent run), AgentOS-NG cherry-picks the specific task commit to main before approving the ORCH task. This is the authoritative path from integration to main.

---

### Change 5 — Updated `_run_mco_review()`: commit_sha-based diff (lines ~1527–1550)

**Location:** Inside `_run_mco_review()`, diff-base logic section.

**Changed:** Refactored diff-base selection to prefer `commit_sha^` when the SHA is available (task already auto-merged by ORCH), falling back to worktree live diff, then HEAD~1.

```python
commit_sha = _extract_task_commit_sha(task_id, root)
if worktree_live and not commit_sha:
    cwd = Path(worktree_cwd)
    diff_base = "main"
    diff_source = "worktree (live branch diff vs main)"
elif commit_sha:
    cwd = root
    diff_base = f"{commit_sha}^"
    diff_source = f"proof commit {commit_sha[:8]}^ (task-specific diff)"
elif worktree_live:
    cwd = Path(worktree_cwd)
    diff_base = "main"
    diff_source = "worktree (live branch diff vs main, SHA not found)"
else:
    cwd = root
    diff_base = "HEAD~1"
    diff_source = "HEAD~1 fallback (proof SHA not found, worktree gone)"
```

**Purpose:** Ensures MCO review diffs only the specific task's changes, not the accumulated integration branch state.

---

### Change 6 — `cmd_validate()`: false completion check (lines 1251–1263)

**Location:** Inside `cmd_validate()`, after `changed_files` is loaded, before the scope-check loop.

**Added:**
```python
# False completion check: fail if no files changed but expected changes are non-empty
expected_changed_paths = packet.get("expected_changed_paths", []) or []
if expected_changed_paths and not changed_files:
    scope_violations.append(
        f"empty diff: 0 files changed but expected_changed_paths lists "
        f"{len(expected_changed_paths)} file(s): {expected_changed_paths}"
    )
    scope_ok = False
    print(
        f"[validate] FAIL: empty diff — expected changes in {expected_changed_paths} "
        f"but no files were changed. Task appears to be a false completion.",
        file=sys.stderr,
    )
```

**Purpose:** BLOCKER 3 — detects tasks that self-report as complete but produced no file changes. Prevents false completions from progressing to merge.

---

## File: classifier.py (857 lines total)

### Change 7 — Producer-before-consumer check in `build_schedule_plan()` (lines 744–767)

**Location:** Inside `build_schedule_plan()`, after the hotspot concurrency limit check, before `selected.append(task_id)`.

**Added:**
```python
# Producer-before-consumer check: if this task consumes a contract, its producer
# must already be in selected before we allow the consumer.
consumes = pkt.get("consumes_contracts") or []
producer_blocked = False
for contract in consumes:
    for other_pkt in todo_packets:
        other_id = other_pkt.get("id", "")
        if other_id == task_id:
            continue
        if contract in (other_pkt.get("produces_contracts") or []):
            if other_id not in selected:
                exclusion_reasons[task_id] = (
                    f"producer {other_id} must be selected/completed before consumer {task_id}"
                )
                producer_blocked = True
            break
    if producer_blocked:
        break

if producer_blocked:
    excluded.append(task_id)
    continue
```

**Purpose:** BLOCKER 2 — ensures that when a consumer task (one with `consumes_contracts`) is being considered for selection, its producer (a task with the matching entry in `produces_contracts`) must already be in `selected`. If not, the consumer is excluded with a named reason.

---

### Change 8 — Added `waiting_on_producer` to return dict (lines 796–812)

**Location:** End of `build_schedule_plan()`, return dict.

**Added:**
```python
waiting_on_producer = [
    tid for tid, reason in exclusion_reasons.items()
    if "must be selected/completed before consumer" in reason
]

return {
    ...
    "waiting_on_producer": waiting_on_producer,
}
```

**Purpose:** BLOCKER 2 — makes the consumer-waiting-for-producer status explicitly surfaced in the return value, enabling callers and tests to inspect which tasks are blocked by producer ordering.

---

## Verification

All 8 changes verified present in source files via `grep`:
- Line 37: `INTEGRATION_BRANCH = "agentos-ng-integration"` ✓
- Lines 1456–1475: `_ensure_integration_branch()` ✓
- Lines 1478–1497: `_cherry_pick_to_main()` ✓
- Lines 1711–1724: cherry-pick block in `cmd_merge()` ✓
- Lines 1251–1263: false completion check in `cmd_validate()` ✓
- Lines 744–767: producer-before-consumer check in `classifier.py` ✓
- Lines 796–812: `waiting_on_producer` in return dict ✓
- (MCO diff-base logic updated in `_run_mco_review()` — verified by inspecting _run_mco_review body)
