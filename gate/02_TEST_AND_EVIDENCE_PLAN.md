# Step 2 — Test and Evidence Plan

**State machine:** Write `current_state: TEST_PLAN_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

You are here because `01_EVIDENCE_ADEQUACY.md` returned `EVIDENCE_UPGRADE_REQUIRED`.

## Output files to create

```
reports/<task_area>/TEST_AND_EVIDENCE_PLAN.md
```

Then run the evidence and update:

```
reports/<task_area>/EVIDENCE_ADEQUACY_ASSESSMENT.md   ← update with what was built
```

---

## Evidence build workflow

1. Identify every behavior, artifact, or promise that needs proof (use the gaps table from `EVIDENCE_ADEQUACY_ASSESSMENT.md`).

2. Create `TEST_AND_EVIDENCE_PLAN.md` with one row per gap:

```
| requirement/behavior | evidence type | file/test/probe to create or update | command to run | expected output/failure signal | raw output path | proof type |
```

Proof type options: `active-path` / `artifact-proof` / `GUI-proof` / `content-eval` / `deployment-proof` / `package-proof` / `enforcement-proof`

### Enforcement/control tasks — required additional rows

For every claimed enforcement mechanism, the plan must include at least one row per protected action:

```
| protected action | invalid condition | attempted bypass path | expected blocked side effect | final source-of-truth check | raw output path |
```

Each row must:
- name the exact unsafe action being prevented (not "validation fails" — what does the unsafe action DO)
- name the bypass path being tested (the lower-level tool or parallel system)
- name what the source of truth will show after the attempt (git log, task log, artifact listing — not tool report)

**Examples:**

| protected action | invalid condition | attempted bypass path | expected blocked side effect | final source-of-truth check | raw output path |
|---|---|---|---|---|---|
| merge to main | review missing | agentos-ng merge TASK | commit absent from main | git log main before/after | raw/T004_git_log_after.txt |
| merge to main | validation failed | ORCH auto-merge path | commit absent from main | git log main before/after | raw/T009_git_log_after.txt |
| task launch | consumer before producer | run-all with T-008 before T-007 | T-008 not started | ORCH status / task runner log | raw/run_all_task_log.txt |
| task completion | false worker report | validate task with missing artifacts | task not unblocked | validation status / task state | raw/false_complete_validation.txt |
| file write | Edit hook block | Bash write attempt | file content unchanged | file hash before/after | raw/file_hash_check.txt |
| package inclusion | manifest excludes file | zip command | file absent from zip | zipinfo -1 output | raw/package_listing.txt |

3. Add or update the smallest sufficient tests/probes/checks within the allowed task scope. **Prefer modifying weak tests into active tests over adding redundant shallow tests.**

4. Run every test/probe/check in the plan.

5. Save raw outputs with exact commands and exit codes. Do not paste output inline — save to files.

6. Update snapshots, diffs, manifests, handoffs, and RTMs to reflect the new evidence.

7. Update `EVIDENCE_ADEQUACY_ASSESSMENT.md` — fill in the "Evidence created or upgraded" table and set `Ready for Evidence Consistency Preflight?` to `YES` (or explain why still blocked).

---

## Hard rules

- Do not create evidence that only tests a nearby or easier behavior.
- Do not use mock paths as final evidence when the real path is available.
- Do not substitute a one-off manual command for a repeatable test when the task requires regression coverage.
- If evidence creation itself is blocked (forbidden files, later phase, unavailable credentials), update the EVIDENCE_ADEQUACY_ASSESSMENT decision to `EVIDENCE_BLOCKED_REQUIRES_HUMAN` and go to `13_BLOCKED_HANDOFF.md`.

---

## Routing

Write to CURRENT_STATE.yaml before routing:

| Outcome | State to write | Next file |
|---|---|---|
| Evidence built, `EVIDENCE_ADEQUACY_ASSESSMENT.md` says `YES` | `TEST_PLAN_COMPLETE` | `03_EVIDENCE_CONSISTENCY.md` |
| Evidence creation blocked | `EVIDENCE_BLOCKED_REQUIRES_HUMAN` | `13_BLOCKED_HANDOFF.md` |
