# Stale File Policy

A stale file is any file that was produced during a gate run but is no longer the current, authoritative version of what it claims to represent. Stale files left in a package without clear labeling are a named failure mode — they cause reviewers and downstream agents to act on superseded information.

---

## What makes a file stale

A file becomes stale when ANY of the following are true:

1. A newer cycle has produced an updated version of the same report (e.g., CYCLE2_COLD_REVIEW_ADJUDICATION.md supersedes COLD_REVIEW_ADJUDICATION.md from cycle 1)
2. The file's verdict (PASS, FAIL, BLOCKED) has been superseded by the gate's current outcome
3. The file was produced in a cycle that was subsequently failed and re-run
4. The file is a BLOCKED_HANDOFF.md but the gate ultimately passed
5. The file contains a pending/incomplete status that was later resolved

---

## Stale file classification

| Classification | Description | Action |
|---|---|---|
| `HISTORICAL_PRIOR_CYCLE` | Report from cycle N, superseded by cycle N+1 | Label with HISTORICAL banner; move to `prior_cycles/` subfolder if possible |
| `HISTORICAL_OVERRIDDEN_VERDICT` | File claimed PASS/FAIL but gate reached a different final verdict | Label with HISTORICAL banner and reference the authoritative file |
| `HISTORICAL_BLOCKED_HANDOFF` | BLOCKED_HANDOFF.md from a gate run that subsequently passed | Must have STATUS: HISTORICAL banner; must NOT be in final package root |
| `ACTIVE` | Current, authoritative version | No action needed |
| `SUPERSEDED` | Replaced by a newer file with the same logical role | Same as HISTORICAL_PRIOR_CYCLE |

---

## Required HISTORICAL banner

Any stale file that remains in the package must have this banner at the very top of the file:

```markdown
---
## ⚠️ STATUS: HISTORICAL — NOT THE FINAL HANDOFF / VERDICT / REPORT

This file was produced during **Cycle [N]** of the gate run.
It has been superseded by: **[name of current authoritative file]**
Final gate verdict: **[PASS_FOR_HANDOFF | FAIL_BLOCKED_REQUIRES_HUMAN]**

Do not act on the verdict in this file. It is retained for audit trail purposes only.
---
```

---

## STALE_FILE_REGISTER.yaml

Every gate run must maintain a stale file register at `reports/<task_area>/STALE_FILE_REGISTER.yaml`. This register is initialized empty at `CYCLE_TRACKER_INITIALIZED` and updated whenever a file becomes stale.

Template: `STALE_FILE_REGISTER_TEMPLATE.yaml`

---

## When stale files must be registered

| Event | Files to register as stale |
|---|---|
| Cycle N fails → Cycle N+1 starts | All reviewer reports from Cycle N; COLD_REVIEW_ADJUDICATION.md from Cycle N; EVIDENCE_ADEQUACY_ASSESSMENT.md from Cycle N |
| Gate ultimately passes after prior BLOCKED_HANDOFF.md was written | BLOCKED_HANDOFF.md; any FAIL-verdict cycle reports |
| EVIDENCE_CONSISTENCY_REGISTER.md is regenerated | Prior version of EVIDENCE_CONSISTENCY_REGISTER.md |

---

## What 16_CANONICAL_HANDOFF_AUDIT.md checks

The canonical handoff audit verifies:
1. `STALE_FILE_REGISTER.yaml` exists and every registered file has a HISTORICAL banner
2. No stale files are in the package root without a banner
3. BLOCKED_HANDOFF.md, if present, is either:
   - Labeled `STATUS: HISTORICAL` if the gate passed, OR
   - The active blocked handoff if the gate failed
4. There is exactly one active HANDOFF.md (or BLOCKED_HANDOFF.md) without a HISTORICAL banner
5. The active handoff's status matches `current_state` in CURRENT_STATE.yaml
