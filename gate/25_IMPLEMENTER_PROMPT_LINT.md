# Step 25 — Implementer Prompt Lint

**State machine:** Write `current_state: IMPLEMENTER_PROMPT_LINT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for:** Preplanning packages that include implementation prompts for downstream implementers.

**Skip when:** No implementation prompts are included in the package. Produce `IMPLEMENTER_PROMPT_LINT_NOT_APPLICABLE.md`.

---

## Why this step exists

An implementation prompt with a syntactically invalid code snippet, a reference to a non-existent file, or a `TODO` placeholder will be faithfully executed by an implementer agent — producing broken code, missed steps, or confused behavior. Catching these issues before the prompt reaches the implementer is far cheaper than the fix cycle they would trigger.

---

## Output file

Copy `IMPLEMENTER_PROMPT_LINT_TEMPLATE.md` to `reports/<task_area>/IMPLEMENTER_PROMPT_LINT.md`.

---

## Checks

### Check 1 — No invalid code snippets

For every code snippet in every implementation prompt:
1. Is the syntax valid for the stated language?
2. Do all referenced functions/methods/classes exist in the codebase?
3. Do all import paths resolve to files that exist?
4. Are all variables used in the snippet in scope?

Flag: `INVALID_CODE_SNIPPET`

### Check 2 — No unquoted JS identifiers used as values

A common mistake: `model: claude-sonnet-4-6` (unquoted, parsed as subtraction). All string values in code snippets must be properly quoted.

Flag: `UNQUOTED_JS_IDENTIFIER`

### Check 3 — No impossible tests

For every test described or scaffolded in the prompt:
1. Is the test technically feasible given the allowed file-touch map?
2. Does the test reference a function that will exist after the implementation?
3. Does the test assume a specific import path that matches the planned module location?

Flag: `IMPOSSIBLE_TEST`

### Check 4 — No TODO or fill-later placeholders

Any `TODO`, `FIXME`, `fill in`, `replace this`, `placeholder`, or `[...]` in a code snippet that the implementer is expected to use as-is is a defect in the prompt.

Flag: `TODO_PLACEHOLDER_IN_SNIPPET`

### Check 5 — No forbidden file in allowed list

Verify the prompt's allowed file-touch map does not include:
- Gate files (any file under `gate/`) unless the task is explicitly a gate upgrade
- Hot files that are not acknowledged as hot with appropriate warnings
- Files that are out of scope for this sprint

Flag: `FORBIDDEN_FILE_IN_ALLOWED_LIST`

### Check 6 — Exact tests and raw output paths present

For every required test the implementer must run:
1. Is the exact test file path specified?
2. Is the exact command specified?
3. Is the expected raw output path specified?

"Run the tests" without specifying which tests is insufficient for D2+ tasks.

Flag: `TEST_SPEC_INCOMPLETE`

### Check 7 — Final status enum matches true scope

The final status enum in the prompt (e.g., `LIVE_BEHAVIOR_FIXED`, `INFRASTRUCTURE_READY_NOT_WIRED`) must match what the implementer can actually achieve given the allowed file-touch map and scope constraints.

Flag: `STATUS_ENUM_OVERCLAIMS_SCOPE`

### Check 8 — Model/tier recommendation present

For D2+ prompts: is the recommended model and effort tier specified?

Flag: `MISSING_MODEL_TIER_RECOMMENDATION`

### Check 9 — Generated-evidence-outside-repo rule present

Does the prompt specify where the implementer must store generated evidence (raw outputs, logs, manifests)?

Flag: `MISSING_EVIDENCE_LOCATION_RULE`

### Check 10 — No overclaiming

Does the prompt claim behaviors, states, or conditions that are not yet true?

Flag: `PROMPT_OVERCLAIMS`

---

## Hard rules

1. A prompt with any `INVALID_CODE_SNIPPET` finding is always a blocker — the implementer will produce broken code.
2. A prompt with any `TODO_PLACEHOLDER_IN_SNIPPET` is a blocker — the implementer will either fail or invent the missing content.
3. A prompt with `STATUS_ENUM_OVERCLAIMS_SCOPE` is a blocker — the implementer will claim a status the evidence cannot support.

---

## Routing

| Outcome | State to write | Next action |
|---|---|---|
| All checks pass | `IMPLEMENTER_PROMPT_LINT_PASS` | Continue gate |
| Any blocking check fails | `IMPLEMENTER_PROMPT_LINT_FAIL` | Return to prompt-architect for revision |
