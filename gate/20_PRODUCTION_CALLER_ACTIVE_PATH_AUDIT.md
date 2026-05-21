# Step 20 — Production Caller / Active Path Claim Audit

**State machine:** Write `current_state: PRODUCTION_CALLER_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory when the task claims any of the following:**
- Live behavior fixed
- Production wiring complete
- Runtime behavior changed
- "Now operational"
- Crash recovery in place
- Gate enforcement active
- Branch governance enforced
- Model/provider routing updated
- State/resume behavior changed
- "Users will now see..."
- "The system will now..."

**Skip for GATE_LITE.** Produce `PRODUCTION_CALLER_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

Tests can pass and code can be correct while the feature is never reachable in production. A helper that is only imported by tests is not "live." A module that is exported but never imported by a production entry point is infrastructure — not wiring. This audit forces the agent to prove that a production caller exists before labeling anything as `LIVE_BEHAVIOR_FIXED`.

---

## Output file

Copy `PRODUCTION_CALLER_ACTIVE_PATH_AUDIT_TEMPLATE.md` to `reports/<task_area>/PRODUCTION_CALLER_AUDIT.md`.

---

## Required table

For every claimed live behavior:

| Claimed live behavior | Function / module changed | Production caller found? | Caller evidence | Test-only? | Verdict |
|---|---|---|---|---|---|
| [behavior] | [file:function] | YES / NO | [grep result or import trace] | YES / NO | LIVE_BEHAVIOR_FIXED / INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY |

---

## How to find production callers

1. Identify the entry-point function or module that was changed.
2. Search for imports of that module in non-test code:
   ```bash
   grep -RIn "require\|import" src/ app/ lib/ --include="*.js" --include="*.ts" | grep "[module_name]" | grep -v "test\|spec\|__mocks__"
   ```
3. Trace the import chain upward to a production entry point (e.g., `app.js`, `server.js`, `index.js`, a route handler, a cron job, a CLI binary).
4. If the chain terminates at a test file or a test helper: the module is test-only.
5. If the chain terminates at a production entry point: record the caller path and mark `LIVE_BEHAVIOR_FIXED`.

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `LIVE_BEHAVIOR_FIXED` | Production caller exists AND the caller is reachable from a live entry point |
| `INFRASTRUCTURE_READY_NOT_WIRED` | Code is correct and tests pass, but no production caller exists yet |
| `TEST_HELPER_ONLY` | Module is imported only by test files; not reachable from production |

---

## Hard rule

If no production caller is proven, the final status must be `INFRASTRUCTURE_READY_NOT_WIRED`, `TEST_HELPER_ONLY`, or `DOCS_ONLY`. The status must NEVER be `LIVE_BEHAVIOR_FIXED` without a demonstrated production import chain.

This rule applies even when:
- All tests pass
- The code is correct
- The feature works when manually invoked
- A prior sprint said it was wired

Proof must be in the current package. Prior sprint claims are not forward-binding evidence.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| All claimed behaviors have production callers | `PRODUCTION_CALLER_AUDIT_PASS` | `GATE_VERDICT_ISSUED` |
| One or more behaviors lack production callers | `PRODUCTION_CALLER_AUDIT_FAIL` | `FIX_CYCLE_IN_PROGRESS` (fix the overclaim or wire the caller) |
