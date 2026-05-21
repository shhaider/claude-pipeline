# Step 17 — Execution Context Audit

**State machine:** Write `current_state: EXECUTION_CONTEXT_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry, OR `current_state: EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` if applicability check below returns NO.

You are here because `16_CANONICAL_HANDOFF_AUDIT.md` returned `CANONICAL_HANDOFF_AUDIT_PASS`.

This step exists because a command can run correctly and produce real output — while running in the wrong branch, directory, worktree, or against the wrong artifact. A test log without branch/HEAD proof is not proof that tests ran on main. A package listing generated from local paths is not proof that the uploaded package contains those files.

**The failure this catches:** An AgentOS-NG packet claimed post-merge tests ran on main. The tests passed. But the test log showed the active branch was `agentos-ng-integration`, not `main`. The gate passed; the claim was false. This step makes branch/HEAD proof a required field for any context-sensitive claim.

---

## Applicability

Run this step if the task's reports make any of the following claims:

| Claim type | Example |
|---|---|
| Tested on a specific branch | "post-merge tests ran on main" |
| Package listing from final export | "package listing generated from uploaded zip" |
| Branch stayed unchanged | "main stayed unchanged after merge" |
| Merge was scoped | "ORCH merged only into integration" |
| Final state was clean | "final git status was clean" |
| Smoke test after merge | "smoke test ran after merge on main" |
| Any source-of-truth was checked | "checked git log on main" / "confirmed commit absent from main" |

If **none** of these claims appear in any document in the package:
- Set `execution_context_audit_applicable: false`
- Write `current_state: EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` to CURRENT_STATE.yaml
- Route to `12_PASS_HANDOFF.md`

---

## Output file to create

```
reports/<task_area>/EXECUTION_CONTEXT_AUDIT.md
```

---

## Required output format

```markdown
# Execution Context Audit

## Applicability
- Does this task make claims about where commands ran? YES / NO
- If NO, justification: [one sentence — stop here, mark NOT_APPLICABLE]
- Claims identified: [list each claim]

## Context proof table

| claim | command | cwd | branch | git_head | source_of_truth_checked | raw_output_path | pass/fail |
|---|---|---|---|---|---|---|---|

## Required context checks
```

---

## What each claim type requires

### "Tests ran on main" / "post-merge tests ran on main"

The raw output tied to this claim must contain ALL of:

```
pwd: <working directory — must not be integration branch worktree>
git branch --show-current: main
git rev-parse HEAD: <sha>
git log -1 --oneline: <sha> <message>
<exact test command>
<test output>
```

If `git branch --show-current` shows anything other than `main`, the claim is false — regardless of whether the tests passed.

### "Package listing generated from uploaded package" / "package listing matches export"

The raw output must contain ALL of:

```
package filename: <actual filename>
package sha256: <hash>
zipinfo -1 <package> OR tar -tzf <package>: <listing>
```

A listing containing `/Users/...` or `/home/...` absolute paths is a listing of local files, not the package contents. That is `FAIL_AUTOFIX_REQUIRED` — the listing must be regenerated from the actual exported file using `zipinfo -1` or `tar -tzf`.

### "Main stayed unchanged" / "main was not modified"

Raw output must contain:

```
git log main --oneline (before): <sha> <message>
git log main --oneline (after): <sha> <message>
git rev-parse main (before): <sha>
git rev-parse main (after): <sha>
comparison: IDENTICAL (same SHA both times)
```

If only the "after" is shown, the claim is unverifiable — `FAIL_AUTOFIX_REQUIRED`.

### "ORCH merged only into integration" / "merge scoped to integration"

Raw output must contain:

```
current branch before ORCH run: <branch>
integration branch log after: <commits showing the expected merge>
main branch log after: <commits NOT showing the merge commit>
proof: <expected commit SHA absent from main>
```

### "Final git status was clean"

Raw output must contain:

```
git status --short: (empty or explained)
```

Any untracked or modified file must be explained:
- Intentionally untracked: show `.gitignore` entry
- Runtime artifact: name it explicitly
- Unexplained modified/untracked file: `FAIL_AUTOFIX_REQUIRED`

### Any "source of truth was checked" claim

Must include:
- Which command was used to check the source of truth
- The exact output of that command (as a file path, not inline)
- The branch/cwd at the time of the check

---

## Findings format

For each finding:

```
Claim: [exact text of the claim from the source document]
Source document: [filename and section]
Required context: [what proof was needed]
Observed context: [what was actually in the raw output]
Evidence: [exact file/path/output excerpt]
Blocking: YES / NO
Required fix: [what must change]
```

---

## Verdict and CURRENT_STATE.yaml write

Write to CURRENT_STATE.yaml:
```yaml
cycles:
  <N>:
    execution_context_audit_applicable: true
    execution_context_audit_result: PASS | FAIL_AUTOFIX_REQUIRED | FAIL_BLOCKED_REQUIRES_HUMAN
```

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| NOT_APPLICABLE | `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE` | `12_PASS_HANDOFF.md` |
| PASS | `EXECUTION_CONTEXT_AUDIT_PASS` | `12_PASS_HANDOFF.md` |
| FAIL_AUTOFIX_REQUIRED | `EXECUTION_CONTEXT_AUDIT_FAIL` | Fix the gap → re-run this step from the context proof table. For "ran on main" claims: re-run the test on main and save new raw output. For "package listing" claims: re-run `zipinfo -1` on the actual export and save output. |
| FAIL_BLOCKED_REQUIRES_HUMAN | `EXECUTION_CONTEXT_AUDIT_FAIL` | `13_BLOCKED_HANDOFF.md` |

**PASS_HANDOFF_COMPLETE is blocked by state machine constraint:** `12_PASS_HANDOFF.md` requires `execution_context_audit_result: PASS or NOT_APPLICABLE` before issuing the handoff. The gate enforces this through agent instruction compliance — an agent that recorded FAIL here must not proceed to Step 12.
