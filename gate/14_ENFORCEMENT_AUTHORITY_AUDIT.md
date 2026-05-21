# Step 14 — Enforcement Authority Audit

**State machine:** Write `current_state: ENFORCEMENT_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry, OR `current_state: ENFORCEMENT_AUDIT_NOT_APPLICABLE` if you determine immediately that none of the applicability triggers apply.

You are here because the task involves a component that claims to prevent, block, enforce, serialize, guarantee, own, or control a protected action.

This step exists because enforcement claims are the most commonly faked class of correctness. A system can correctly detect a violation and correctly report it while still allowing the unsafe action to occur through another path. Detection without prevention is not enforcement.

---

## Applicability trigger

Run this step — do not skip — if the task involves any of the following:

- validators, gates, blockers, claim systems, file locks
- task schedulers, dependency schedulers, merge controls
- review controls, permission controls, orchestration systems
- CI/CD gates, package/export gates, safety rails
- supervisor/worker systems, agent governance layers
- anything using the words: prevent, block, enforce, serialize, guarantee, own, control

If none of these apply, record `NOT_APPLICABLE` with a one-sentence justification and route to `04_PANEL_ENTRY.md`.

---

## Output file to create

```
reports/<task_area>/ENFORCEMENT_AUTHORITY_AUDIT.md
```

Use the required format below.

---

## Required output format

```markdown
# Enforcement Authority Audit

## Applicability
- Does this task involve enforcement/gating/blocking/control? YES / NO
- If NO, justification: [one sentence — stop here, route to 04_PANEL_ENTRY.md]

## Protected actions
| action | claimed controlling component | true authority | evidence path |

List every protected action. True authority is the component whose permission is
structurally required — not the component that checks first, but the component that
cannot be bypassed. If no single component has true authority, write NONE_AUTHORITATIVE.

## Source-of-truth map
| domain | source of truth | secondary systems | risk of split-brain | mitigation |

Include every applicable domain:
- task lifecycle (created / running / blocked / complete)
- task readiness (ready / not-ready)
- worktree / branch ownership
- validation status (pass / fail)
- review status (approved / blocked)
- merge status (merged / not merged)
- release / package status (released / not released)
- deployment status (deployed / not deployed)

## Bypass path inventory
| protected action | possible bypass path | tested? | result | evidence path | blocker? |

A bypass path is any path by which the protected action can occur without passing
through the claimed controlling component. List all paths, including:
- lower-level tool invoked directly (e.g., git merge bypasses ORCH wrapper)
- parallel system with independent authority (e.g., GitHub auto-merge)
- shell command available to agents (e.g., Bash can write despite Edit hook)
- CI/CD job triggered independently
- human manual command

For each: tested = YES / NO. Result = BYPASSED / BLOCKED / NOT_TESTED.

## Negative side-effect tests
| test | unsafe action attempted | expected prevention | observed final state | pass/fail | raw output path |

For each claimed enforcement mechanism, at least one row must show:
- what unsafe action was attempted
- what prevention was expected
- what the source of truth showed afterward (not what the tool reported — what the
  source of truth actually contains)

Example: "merge blocked" is not proven by a tool saying "blocked." It is proven by
git log on main showing the blocked commit is absent.

## Before/after authority proof
| action | before state evidence | attempted command/event | after state evidence | conclusion |

Capture state BEFORE the attempted unsafe action, then capture state AFTER. The
after-state must be read from the authoritative source, not the enforcing component.

## Advisory vs authoritative classification
| gate/control | advisory or authoritative | reason | required fix if advisory |

Advisory: the component detects and reports the violation but does not structurally
prevent the unsafe action. Another component can still perform it.

Authoritative: the protected action cannot occur without this component's approval,
regardless of what other components do.

A gate is advisory if ANY of the following are true:
- the lower-level tool can perform the action without consulting it
- another system holds independent merge/run/release authority
- the gate's verdict can be ignored by the orchestrator
- the gate blocks the wrapper but not the underlying primitive

## Findings

For each finding:

Finding: [descriptive name]
Evidence: [exact evidence — file path, git log, command output, line reference]
Impact: [what unsafe action can still occur]
BLOCKING: YES / NO
Required correction: [what must change to make the gate authoritative]

## Enforcement verdict
PASS / FAIL_AUTOFIX_REQUIRED / FAIL_BLOCKED_REQUIRES_HUMAN
```

---

## Mandatory checks — run all that apply

### Check A — Blocked merge proof

If the task claims a merge was blocked:

1. Capture `git log --oneline main` before the attempted merge (save to file)
2. Attempt the merge through the normal claimed path
3. Capture `git log --oneline main` after (save to file)
4. Confirm the blocked commit SHA is absent from main
5. Confirm the gate/validator still shows blocked status

**Detection-only is insufficient.** The merge either happened or it did not. Check the branch.

### Check B — Blocked task launch proof

If the task claims unsafe parallelism is blocked:

1. Trigger run-all or the orchestrator with conflicting tasks configured
2. Capture orchestrator status / task log (save to file)
3. Confirm the excluded task has no start timestamp
4. Confirm the underlying runner (not the wrapper) did not start it

**Checking the planner output is insufficient.** The runner may start it anyway.

### Check C — Blocked validation → downstream prevention

If the task claims a failed validation prevents downstream actions:

1. Trigger the failing validation
2. Attempt to proceed to the downstream action (merge / unblock / release)
3. Confirm the downstream action was structurally prevented
4. Capture the blocked state from the downstream source of truth

**A validation failure that does not propagate is advisory, not authoritative.**

### Check D — Negative control test

For every claimed enforcement mechanism, at least one negative test must exist:

- out-of-scope edit → confirm it was not merged / applied / released
- missing review → confirm merge / release was not possible
- protected path conflict → confirm parallel execution did not occur
- consumer task before producer gate → confirm consumer was not started
- false completion report → confirm it did not unblock or merge

The negative test must check the **side effect**, not just the tool's exit code or report.

### Check E — Lower-layer bypass proof

If a wrapper controls a lower-level tool:

1. Identify whether the lower-level tool has its own independent authority
   (auto-merge, auto-run, auto-release, direct shell access)
2. If yes: test whether it can bypass the wrapper
3. If the lower-level tool can bypass: the gate is advisory, not authoritative
4. Document the result and required fix

Examples:
- AgentOS-NG wraps ORCH → can ORCH auto-merge independently?
- A hook blocks Edit → can Bash still write the file?
- A task scheduler blocks a task → can the provider CLI run it directly?
- A package manifest excludes a file → can the zip command include it anyway?

### Check F — Final source-of-truth proof

The final state must be read from the authoritative source, not the enforcing component.

| Claimed enforcement | Correct source of truth to inspect |
|---|---|
| Merge was blocked | `git log main` — is the commit there? |
| Task was not launched | Orchestrator task log / process list |
| Validation prevented release | Release artifact listing / status endpoint |
| File lock prevented write | Filesystem state / file content |
| Package excluded file | `zipinfo -1` / `find` output |
| Review gate blocked deploy | Deploy status / deployment log |

Narrative statements from the enforcing component are not sufficient final-state proof.

---

## Self-check: would this catch the known failure?

Before writing the verdict, answer all six:

1. Would it catch: ORCH auto-merged T-004 after MCO review blocked it?
   → Yes, if Check A captured git log after the "blocked" verdict.

2. Would it catch: ORCH auto-merged T-009 after validation failed?
   → Yes, if Check A confirmed commit absent from main after validation failure.

3. Would it catch: T-008 selected before T-007 (consumer before producer)?
   → Yes, if Check D included a consumer-before-producer negative test.

4. Would it catch: false completion validation passing?
   → Yes, if Check C proved failed validation structurally blocked downstream.

5. Would it catch: missing verification artifacts?
   → Yes, if the protected-actions table required artifact presence as a prerequisite.

6. Would it block PASS_FOR_HANDOFF until these were fixed?
   → Yes, if enforcement verdict is FAIL, it maps to FAIL_AUTOFIX_REQUIRED in 10_GATE_VERDICT.

---

## Verdict mapping

| Enforcement verdict | Gate impact |
|---|---|
| `PASS` | No impact on gate verdict from this step |
| `FAIL_AUTOFIX_REQUIRED` | Gate verdict becomes `FAIL_AUTOFIX_REQUIRED` minimum |
| `FAIL_BLOCKED_REQUIRES_HUMAN` | Gate verdict becomes `FAIL_BLOCKED_REQUIRES_HUMAN` |

---

## Routing

Write to CURRENT_STATE.yaml before routing:
```yaml
cycles:
  <N>:
    enforcement_audit_applicable: true | false
    enforcement_audit_result: PASS | FAIL_AUTOFIX_REQUIRED | FAIL_BLOCKED_REQUIRES_HUMAN | NOT_APPLICABLE
```

| Outcome | State to write | Next file |
|---|---|---|
| `NOT_APPLICABLE` — no enforcement/gating/control involved | `ENFORCEMENT_AUDIT_NOT_APPLICABLE` | `04_PANEL_ENTRY.md` |
| `PASS` | `ENFORCEMENT_AUDIT_PASS` | `04_PANEL_ENTRY.md` |
| `FAIL_AUTOFIX_REQUIRED` | `ENFORCEMENT_AUDIT_FAIL_AUTOFIX` | Fix the gap, rerun this step (transition back to `ENFORCEMENT_AUDIT_IN_PROGRESS`), then `04_PANEL_ENTRY.md` |
| `FAIL_BLOCKED_REQUIRES_HUMAN` | `ENFORCEMENT_AUDIT_FAIL_BLOCKED` | `13_BLOCKED_HANDOFF.md` |
