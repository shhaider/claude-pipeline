# Step 1 — Evidence Adequacy Assessment

**State machine:** Write `current_state: EVIDENCE_ADEQUACY_IN_PROGRESS` to CURRENT_STATE.yaml at entry. If this is a new cycle (not the first), increment `cycle_count` by 1 and add a new cycle block to `cycles`.

## Why this runs first

A sophisticated review process is useless over a weak evidence base. Before any reviewers run, you must decide whether the just-completed work has enough real-world evidence to be reviewable. If not, you build or upgrade the evidence first.

## Output file to create

```
reports/<task_area>/EVIDENCE_ADEQUACY_ASSESSMENT.md
```

Use the required format at the bottom of this file.

## Decision — return exactly one of

```
EVIDENCE_ALREADY_ADEQUATE
EVIDENCE_UPGRADE_REQUIRED
EVIDENCE_BLOCKED_REQUIRES_HUMAN
```

### EVIDENCE_ALREADY_ADEQUATE
All relevant adequacy criteria below are already met. Name the existing evidence files and explain why no new tests/evidence are needed.

### EVIDENCE_UPGRADE_REQUIRED
Evidence is missing, too shallow, stale, non-real-world, not automated where it should be, lacks raw output, lacks exit code capture, or does not cover the actual behavior changed. **This is the default if unsure.**

### EVIDENCE_BLOCKED_REQUIRES_HUMAN
Adequate evidence cannot be created within the allowed scope — requires forbidden files, later phases, unavailable credentials, production-only access, or a human decision. Still create the best safe evidence possible and clearly mark the remaining gap.

---

## Evidence adequacy criteria

Evidence is adequate only if ALL of the following are true:

1. **Relevant** — tests the actual requirement that changed, not a nearby or easier behavior
2. **Real-path** — uses the real public/internal entrypoint that production/callers rely on
3. **Behavioral** — checks observable behavior or generated artifacts, not source strings or implementation shape
4. **Specific** — would fail if the new behavior were absent, unwired, stale, or only mocked
5. **Regression-oriented** — where relevant, represents the old-bad behavior the task was meant to eliminate
6. **Failure-aware** — where relevant, covers malformed input, missing fields, retry/fallback, edge paths named in the task
7. **Repeatable** — can be rerun by a future reviewer without reconstructing hidden manual steps
8. **Raw-output-backed** — commands, outputs, counts, and exit codes saved to files
9. **Package-visible** — all evidence files needed for review are in the export package or explicitly labeled repo-present/not-exported with justification
10. **Cross-artifact-consistent** — evidence agrees with handoff, manifest, diff, snapshots, package listing, RTM, and final git state

---

## What counts as real-world evidence by task type

Pick the applicable types. Do not create irrelevant evidence just to satisfy volume.

**Code/runtime behavior**
- Active test calling the same function/CLI/API/process that real callers use
- Integration test reading the actual persisted artifact from disk
- Failure-path test forcing the old bug condition
- Regression test that would fail if code were exported but not wired

**Evidence/package/reporting work**
- `zipinfo -1` or `find` package listing saved to a file
- Manifest-vs-package presence table
- HEAD/SHA reconciliation table
- Raw output files with `EXIT_CODE:0`

**Prompt/agent behavior**
- Fixture input forcing required JSON fields
- Parser/validator test over a generated agent response
- Active test proving fields reach downstream handoff, not just prompt text

**GUI/user-facing behavior**
- Playwright deterministic flow test
- Screenshot/trace on failure where supported
- Error/retry/status scenario if user trust display changed

**Content generation pipeline**
- Fixture corpus through the actual pipeline stage
- Voice/style fidelity check against stored exemplars
- Before/after comparison with rubric score

**Deployment/ops**
- Dry-run deployment artifact
- Rollback command proof or simulation
- Post-deploy health-check output

**Documentation-only**
- File inventory proving expected docs exist
- Link/path check
- No-placeholder/stale-language scan

---

## Enforcement/control tasks — additional adequacy requirements

If the task involves enforcement, gating, blocking, or control of any protected action, evidence is adequate **only if it proves both**:

1. **Detection** — the invalid condition was identified
2. **Prevention** — the protected side effect did not occur

Detection alone is not adequate. Examples:

| Insufficient (detection only) | Adequate (detection + prevention) |
|---|---|
| "Validation failed" | "Validation failed AND merge/unblock/release did not occur" |
| "Plan excluded task" | "Plan excluded task AND runner did not start it" |
| "Review gate returned BLOCKED" | "Review returned BLOCKED AND merge/release was structurally prevented" |
| "Classifier says hard_block" | "hard_block AND dependent task remained unscheduled until producer reached gate" |

**Minimum evidence for enforcement tasks** (in addition to the standard bundle):

- protected action definition (what exact action is being prevented)
- authority map (which component truly controls the protected action)
- bypass path inventory (all ways the action can occur without the gate)
- negative side-effect test (attempted the unsafe action, checked source of truth)
- before/after source-of-truth proof (git log, task status, artifact listing — not tool report)
- final state proof (the source of truth confirms the unsafe action did not occur)

If any of these are absent for an enforcement task, the decision must be `EVIDENCE_UPGRADE_REQUIRED`.

---

## Minimum evidence bundle

Every nontrivial task must produce or identify:

- final repo-state capture
- final diff
- changed-file snapshots for changed source/test/prompt files
- raw test/probe/check output files with exact commands and exit codes
- requirement traceability matrix or equivalent
- final manifest
- final handoff
- package file listing if exporting a package
- known risks and not-tested items

If any item is not applicable, explain why in `EVIDENCE_ADEQUACY_ASSESSMENT.md`.

---

## Required output format

```
# Evidence Adequacy Assessment

## Decision
EVIDENCE_ALREADY_ADEQUATE | EVIDENCE_UPGRADE_REQUIRED | EVIDENCE_BLOCKED_REQUIRES_HUMAN

## Existing evidence inspected
- [list files inspected]

## Evidence gaps found
| requirement/behavior | existing evidence | adequacy issue | action | blocker? |

## Evidence created or upgraded
| requirement/behavior | new/updated evidence | command | raw output path | exit code |

## Evidence skipped as already adequate
| requirement/behavior | evidence path | why sufficient |

## Remaining evidence limitations
- [list any gaps that could not be closed]

## Ready for Evidence Consistency Preflight?
YES / NO
```

**Hard rule:** If `Ready for Evidence Consistency Preflight?` is `NO`, do not proceed to the reviewers. Either upgrade the evidence or return a blocked handoff.

---

## Routing

Write the decision to CURRENT_STATE.yaml before routing:
```yaml
cycles:
  <N>:
    evidence_adequacy_decision: <decision>
```

| Decision | State to write | Next file |
|---|---|---|
| `EVIDENCE_ALREADY_ADEQUATE` | `EVIDENCE_ALREADY_ADEQUATE` | `03_EVIDENCE_CONSISTENCY.md` |
| `EVIDENCE_UPGRADE_REQUIRED` | `EVIDENCE_UPGRADE_REQUIRED` | `02_TEST_AND_EVIDENCE_PLAN.md` |
| `EVIDENCE_BLOCKED_REQUIRES_HUMAN` | `EVIDENCE_BLOCKED_REQUIRES_HUMAN` | `13_BLOCKED_HANDOFF.md` |
