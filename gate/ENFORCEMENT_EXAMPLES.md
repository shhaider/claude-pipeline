# Enforcement Authority — Examples and Anti-Patterns

Reference this file when filling out `14_ENFORCEMENT_AUTHORITY_AUDIT.md` or when R3 is checking for enforcement-related AI failure patterns.

---

## Example 1 — AgentOS-NG / ORCH auto-merge bypass

### Scenario

AgentOS-NG reports that MCO review failed for T-004 and T-009. The MCO review verdict says "blocked." But ORCH subsequently auto-merges both tasks into main anyway.

### Why this is a blocker

AgentOS-NG is advisory, not authoritative. It wraps ORCH and reports outcomes, but ORCH has its own independent auto-merge capability. When ORCH auto-merges, it does not consult AgentOS-NG's verdict. The governance layer is a reporting layer, not an enforcement layer.

### What evidence reveals it

```
Before blocked verdict:
  git log main  → [commit list, T-004 absent, T-009 absent]

AgentOS-NG verdict: MCO review BLOCKED T-004, T-009

After blocked verdict:
  git log main  → [same commits + T-004 commit + T-009 commit]
```

The commit appearing in `git log main` after a "blocked" verdict is definitive proof of bypass.

### What the correct test looks like

```
Test: T-004 blocked merge does not reach main
  Step 1: capture git log --oneline main → save to raw/T004_before_git_log.txt
  Step 2: MCO review returns BLOCKED for T-004
  Step 3: observe whether ORCH auto-merge fires
  Step 4: capture git log --oneline main → save to raw/T004_after_git_log.txt
  Step 5: confirm T-004 commit SHA absent from T004_after_git_log.txt
  Expected: T-004 SHA absent from main after blocked verdict
  Observed: T-004 SHA present → FAIL
```

### Why "validation failed" alone is insufficient

The MCO review correctly detected the problem and correctly reported it. That is detection. The test asked only "did validation fail?" — it did. But it did not ask "did main stay clean?" ORCH answered that question without being asked, and the answer was no.

### R3 classification

- **advisory gate mistaken for enforcement** — the wrapper reported a block but could not enforce it
- **auto-merge bypass** — ORCH merged independently after a governance block
- **detection-without-prevention** — MCO detected violations but did not prevent the merge

---

## Example 2 — Hook blocks Edit, Bash writes the file

### Scenario

A hook is installed that blocks the Edit tool from writing to protected paths. A test confirms "Edit was blocked." But the same agent writes the file using `Bash: echo content > path`.

### Why this is a blocker

The Edit hook is advisory with respect to Bash. It controls one tool but not the shell. An agent with Bash access can bypass the Edit gate entirely.

### What evidence reveals it

```
Test: attempt Edit on protected path → returns "permission denied" ✓
Test: attempt Bash write on protected path → succeeds, file written ✗
Final state: file content changed despite Edit block
```

### Correct test

```
Test: protected path write blocked via all available paths
  Step 1: capture hash of protected file
  Step 2: attempt Edit → confirm blocked
  Step 3: attempt Bash write → confirm blocked (or: note Bash is not available to agent)
  Step 4: capture hash of protected file → confirm unchanged
```

### R3 classification

- **lower-layer bypass** — Bash bypasses the Edit hook
- **advisory gate mistaken for enforcement** — the hook controls one surface, not the primitive

---

## Example 3 — Package manifest excludes file, zip includes it

### Scenario

A package manifest says `exclude: secrets.env`. The packaging script reads the manifest. But the final zip was created with `zip -r package.zip .` and `secrets.env` is present in the working directory.

### Why this is a blocker

The manifest is advisory to the packaging script. The zip command has no knowledge of the manifest's exclusion rules unless the script explicitly passes `--exclude secrets.env` to the zip invocation. If it doesn't, the file ships.

### What evidence reveals it

```
Manifest says: secrets.env excluded
zipinfo -1 package.zip | grep secrets → secrets.env  ← file is present
```

### Correct test

```
Test: excluded file absent from package
  Step 1: note manifest exclusion: secrets.env
  Step 2: build package
  Step 3: run zipinfo -1 package.zip | sort > raw/package_listing.txt
  Step 4: confirm grep 'secrets.env' raw/package_listing.txt returns empty
  Expected: empty (file absent)
  Observed: secrets.env found → FAIL
```

### R3 classification

- **advisory gate mistaken for enforcement** — manifest states intent, does not control zip
- **detection-without-prevention** — manifest detected the file should be excluded but did not prevent inclusion

---

## Example 4 — CI check fails, release job still publishes

### Scenario

A CI check gate runs before the release job and returns failure. The release job is configured with `continue-on-error: true` (or the pipeline is `needs: [check]` with `if: always()`). The release publishes anyway.

### Why this is a blocker

The CI check is advisory. Its failure verdict does not propagate to the release job unless the pipeline is explicitly configured to gate on it. `continue-on-error` and `if: always()` are bypass paths that must be tested.

### What evidence reveals it

```
CI run log:
  check_gate: FAILED
  release_job: started (condition: always()) → published v1.2.3
Release artifact listing: v1.2.3 present
```

### Correct test

```
Test: failed CI check blocks release
  Step 1: configure check to fail
  Step 2: run pipeline
  Step 3: inspect release artifact listing
  Step 4: confirm v1.2.3 absent from release listing
  Expected: release not published
  Observed: release published → FAIL
```

### R3 classification

- **advisory gate mistaken for enforcement** — CI check does not structurally gate the release job
- **auto-merge bypass** (release variant) — release proceeds independently of the check verdict

---

## Example 5 — Task planner excludes task, lower-level runner starts it

### Scenario

A scheduler's plan excludes T-008 because T-007 has not reached the required gate. The plan output says "T-008 excluded." But `run-all` invokes all tasks by reading the task list, not the plan. T-008 starts anyway.

### Why this is a blocker

The scheduler controls the plan output but not the runner. The runner has independent start authority. The task board says blocked; the runner does not check the task board.

### What evidence reveals it

```
Plan output: T-008 excluded (consumer before producer gate)
run-all log: starting T-008...
T-008 process: running
```

### Correct test

```
Test: T-008 does not start before T-007 reaches gate
  Step 1: configure T-007 as not-at-gate
  Step 2: run run-all
  Step 3: inspect process list / task runner log
  Step 4: confirm T-008 not started
  Expected: T-008 absent from running tasks
  Observed: T-008 running → FAIL
```

### R3 classification

- **consumer-before-producer scheduling** — consumer ran before producer reached gate
- **advisory gate mistaken for enforcement** — planner does not control the runner

---

## Quick reference — R3 patterns added for enforcement tasks

| Pattern name | What it means |
|---|---|
| `advisory gate mistaken for enforcement` | Gate reports a block but cannot structurally prevent the unsafe action |
| `lower-layer bypass` | Wrapper controls one tool; underlying primitive still has independent authority |
| `split-brain lifecycle` | Two systems track the same state independently and disagree |
| `detection-without-prevention` | System detects violation but does not prevent merge/unblock/release |
| `negative-test-without-side-effect-check` | Test checks exit code / tool report but not the source-of-truth final state |
| `auto-merge bypass` | Orchestrator or CI merges/releases independently after a governance block |
| `consumer-before-producer scheduling` | Planner excludes producer, but consumer starts before producer gate is reached |
| `false-completion trust` | Worker self-report accepted as complete; missing diff/tests/artifacts not detected |
