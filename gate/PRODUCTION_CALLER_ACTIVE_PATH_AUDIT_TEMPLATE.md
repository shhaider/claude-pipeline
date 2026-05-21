# Production Caller / Active Path Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Live behavior claims found in package

List every claim in the handoff, prompt, or reviewers that asserts a production or live behavior:

1. "[exact quote]" — source: [file:line]
2. "[exact quote]" — source: [file:line]
3. OR: No live behavior claims found — audit NOT_APPLICABLE

---

## Production caller table

| Claimed live behavior | Function / module changed | Production caller found? | Caller evidence | Test-only? | Verdict |
|---|---|---|---|---|---|
| [behavior] | [file:function_name] | YES / NO | [grep result or caller path] | YES / NO | LIVE_BEHAVIOR_FIXED / INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY |

---

## Import chain traces

For each entry where `Production caller found? = YES`:

**Behavior:** [behavior]
**Changed module:** [file]
**Import chain:**
```
[production_entry_point.js]
  imports → [intermediate_module.js]
    imports → [changed_module.js]
      contains → [changed_function]
```
**Evidence:**
```bash
grep -RIn "require\|import" src/ | grep "[module_name]" | grep -v "test"
# Output: [exact grep output]
```

---

## Test-only callers (not production)

For each entry where `Test-only? = YES`:

**Module:** [file]
**Test callers found:**
- [test_file_path] — imports [changed_module]
**No production callers found**
**Correct label:** INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY

---

## Verdict summary

| Claimed behavior | Verdict |
|---|---|
| [behavior] | LIVE_BEHAVIOR_FIXED / INFRASTRUCTURE_READY_NOT_WIRED / TEST_HELPER_ONLY |

**Final outcome label for this task:**
```
LIVE_BEHAVIOR_FIXED | INFRASTRUCTURE_READY_NOT_WIRED | TEST_HELPER_ONLY | DOCS_ONLY
```

---

## Audit verdict

```
PRODUCTION_CALLER_AUDIT_PASS | PRODUCTION_CALLER_AUDIT_FAIL
```

**Rationale:** [one paragraph explaining the verdict]
