# Step 19 — Prompt Contract Review

**State machine:** Write `current_state: PROMPT_CONTRACT_REVIEW_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for:** D2-hot / D3 / D4 work, preplanning packages, hot file tasks, repeated correction loops (cycle 3+ reached in prior attempt).

**Optional for:** D2 tasks when the prompt is simple and self-contained.

**Skip for:** D0 / D1 / GATE_LITE profile. Produce `PROMPT_CONTRACT_REVIEW_NOT_APPLICABLE.md`.

---

## What this step does

The prompt contract review examines the task prompt for issues that will cause the implementer to produce incorrect, incomplete, or overclaiming work — before any evidence is collected. Catching contract issues here is far cheaper than catching them in R1–R5 or after a failed handoff.

---

## Output file

Copy `PROMPT_CONTRACT_REVIEW_TEMPLATE.md` to `reports/<task_area>/PROMPT_CONTRACT_REVIEW.md`.

---

## Checks — run all of these

### Check 1 — Ambiguous terms

Scan the prompt for terms that could be interpreted multiple ways:
- "fix" — does this mean detect, prevent, or repair?
- "wire" — does this mean add an import, register with a dispatcher, or both?
- "test" — unit test, integration test, end-to-end test, or manual verification?
- "complete" — feature-complete, test-complete, evidence-complete, or merge-complete?
- "production" — production code path, production deployment, or just "non-test code"?

Record each ambiguous term and the interpretation required for the task to succeed.

### Check 2 — Hidden assumptions

Identify assumptions the prompt makes that are not stated:
- Assumes a specific branch is already checked out
- Assumes a dependency is already installed or registered
- Assumes a prior sprint task is complete
- Assumes the implementer has access to a specific host, VPS, or database
- Assumes a specific file exists at a stated path

### Check 3 — Lifecycle timing ambiguity

Does the prompt require artifacts or git states to be captured at a specific point in time? Check for:
- "collect the head SHA before the commit" — is this stated explicitly or assumed?
- "generate the manifest after all files exist" — does the prompt enforce this ordering?
- "run tests after the migration completes" — is the ordering requirement clear?
- "validate the handoff before tests complete" — this ordering is wrong; flag it

### Check 4 — Forbidden interpretations

State explicitly what the task is NOT:
- What files must NOT be modified
- What behaviors must NOT change
- What phases must NOT be started
- What the implementer must NOT do if the primary task fails

If any forbidden interpretation is missing from the prompt: add it to the contract review finding.

### Check 5 — Missing proof specifications

Does the prompt specify exactly what evidence is required?
- If the task claims a behavior is fixed: is a production caller proof required?
- If the task adds a new API: is consumer-API proof required?
- If the task runs tests: are exact test file names, commands, and expected counts specified?
- If the task produces a package: is the manifest format and hash requirement specified?

### Check 6 — Unclear allowed/forbidden files

Does the prompt list the allowed file-touch map clearly?
- Are hot files explicitly acknowledged?
- Is there a statement of what files must NOT be touched?
- Are test files included in the allowed list?
- Are gate files (if any) included or explicitly excluded?

### Check 7 — Missing model/tier recommendation

For D2+ tasks: does the prompt specify which model/tier should run the implementation?
- Without a model recommendation, the implementer may choose a model that is too weak for the task complexity.
- Flag if missing for D3/D4 tasks.

### Check 8 — Missing repo cleanliness rule

Does the prompt specify the expected repo state at completion?
- "Final git status must be clean" vs. "untracked raw output files are expected"
- Missing: flag it.

### Check 9 — Missing generated-evidence-outside-repo rule

If the task generates evidence files (raw outputs, manifests, signouts): does the prompt specify where they must live?
- Must they be generated inside the repo and committed?
- Must they be generated outside the repo (e.g., `/tmp/`, `reports/` which is gitignored)?
- Missing: flag it.

### Check 10 — Invalid code snippets

If the prompt includes code snippets:
- Are they syntactically valid?
- Do they reference functions, variables, or files that actually exist?
- Do they reference non-existent imports or undeclared identifiers?
- Could they cause confusion if the implementer treats them as copy-pasteable?

### Check 11 — References to non-existent files or tests

Does the prompt reference:
- A test file that does not exist at the stated path?
- A fixture file that has not been created?
- A raw output file from a prior run that may be stale?
- A snapshot that was superseded?

### Check 12 — Overclaims in the prompt itself

Does the prompt claim something that is not yet true (as of the time it was written)?
- "The migration is already registered" — is this verified?
- "Tests currently pass" — when was this last verified?
- "The feature is live" — is production caller proof available?

---

## Verdict

| Verdict | Meaning |
|---|---|
| `PROMPT_CONTRACT_PASS` | All 12 checks pass or have justified non-applicability. The implementer can proceed. |
| `PROMPT_CONTRACT_NEEDS_REVISION` | One or more checks found issues that would cause incorrect implementation. Return to operator for revision. |
| `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY` | The prompt contains ambiguities that cannot be resolved without human decision. Block the gate. |

---

## Routing

| Outcome | State to write | Next action |
|---|---|---|
| PROMPT_CONTRACT_PASS | `PROMPT_CONTRACT_PASS` | Write to CURRENT_STATE.yaml; proceed to `EVIDENCE_ADEQUACY_IN_PROGRESS` |
| PROMPT_CONTRACT_NEEDS_REVISION | `PROMPT_CONTRACT_NEEDS_REVISION` | Return the finding to operator; do not proceed with evidence collection |
| PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY | `PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY` | Write to CURRENT_STATE.yaml; route to `GATE_PROFILE_SELECTION_BLOCKED` |
