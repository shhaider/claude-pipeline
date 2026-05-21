# Dirty Worktree Recurrence Register

**Last updated:** [ISO timestamp]
**Updated by task:** [task_id]

---

## Purpose

Tracks every path that has appeared as uncommitted/untracked across gate runs. When a path appears twice, a hygiene task must be created to permanently resolve it.

## Gate 5.2-R1 approved classification labels

Every dirty path from `git_status_final.txt` MUST be classified with one of these labels.
Unclassified paths fire `DIRTY_PATH_NOT_CLASSIFIED`. The label `UNKNOWN_REQUIRES_HUMAN`
fires `UNKNOWN_REQUIRES_HUMAN_BLOCKER` (intentional escape hatch — the gate must surface
the row for human review rather than auto-pass).

| Label | Use when |
|---|---|
| `UNRELATED_EXTERNAL_WORK` | Path belongs to another repo or external scratch area unrelated to this task |
| `ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH` | A concurrent agent or sprint is actively editing this path under a tracked sprint folder; this lane must not touch it |
| `AMBIENT_UNRELATED_DOC_COMMIT` | Doc-only commit (e.g. CHANGELOG entry) committed alongside but unrelated to the audited change |
| `UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN` | External change unrelated to this task that must be reviewed by a human before merge but does not block this gate |
| `UNKNOWN_REQUIRES_HUMAN` | Agent could not determine origin/scope of this dirty path; gate MUST block until human classifies |

Always-blocking paths (regardless of label):

- `node_modules/`
- `.run_artifacts/`
- `raw_test_output*` / `raw_outputs/`
- `DOC_FRESHNESS_REPORT.md` (generated, do not commit)
- Any path that is task-relevant (matches files in this task's diff)

## Example multi-row classification

| Path | Label | Reason |
|---|---|---|
| kills/newsroom/gui/client/src/components/AppShell.vue | ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH | GUI sprint gui-pipeline-ui-2026-05-01 is actively editing this file |
| docs/changelog/CHANGELOG_2026-04-30.md | AMBIENT_UNRELATED_DOC_COMMIT | Doc-only changelog entry; unrelated to merge under audit |
| ../external-scratch/notes.md | UNRELATED_EXTERNAL_WORK | Belongs to operator's external scratch repo |
| scripts/research/forgotten.dat | UNKNOWN_REQUIRES_HUMAN | Origin unclear; needs human inspection before gate can pass |

---

## Recurrence register

| Path | First seen | Last seen | Recurrence count | Likely source | Current policy | Follow-up ticket |
|---|---|---|---|---|---|---|
| `docs/DOC_FRESHNESS_REPORT.md` | [date] | [date] | [N] | Auto-generated doc freshness | gitignore or commit | [ticket or "none"] |
| `node_modules/` | [date] | [date] | [N] | npm install | gitignore (already handled) | N/A |
| `.run_artifacts/` | [date] | [date] | [N] | Test runner output | gitignore | [ticket or "none"] |
| [path] | [date] | [date] | [N] | [source] | [policy] | [ticket or "none"] |

---

## Audit for this gate run

**Gate run:** [gate_run_id]
**Task ID:** [task_id]
**Date:** [ISO timestamp]

**Currently dirty paths (from `git status --short`):**
```
[paste git status --short output here]
```

**Recurrence findings:**

| Path | In register? | Recurrence count | Action required |
|---|---|---|---|
| [path] | YES/NO | [N] | [add to register / increment count / create hygiene ticket] |

**Hygiene tickets created:**
- [ticket ID] — [path] — [description of fix needed]

---

## Verdict

```
DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS | DIRTY_WORKTREE_RECURRENCE_BLOCKER
```
