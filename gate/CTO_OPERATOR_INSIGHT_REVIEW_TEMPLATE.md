# CTO / Operator Insight Review

**Task ID:** [task_id]
**Task area:** [task_area]
**Risk tier:** [D2-hot / D3 / D4]
**Review completed at:** [ISO timestamp]

---

## Q1 — What did this task reveal?

**About the codebase:**
[one paragraph]

**About the architecture:**
[one paragraph]

**About the process:**
[one paragraph]

**About prompt quality:**
[one paragraph — was the task prompt well-specified?]

---

## Q2 — Does it change the next prompt?

**Pre-written next prompt:** [path or "none"]

**Still valid?** YES / NO

If NO:
- What should change: [description]
- Simpler alternative available: YES / NO — [if yes: what]
- Prior art that makes next phase unnecessary: YES / NO — [if yes: what]

---

## Q3 — Does it change the roadmap?

**New tasks to add to roadmap:**
- [task description] — add to roadmap as: [entry]

**Completed roadmap items:**
- [item] — now complete, mark done

**Roadmap items to delete:**
- [item] — reason: [wrong approach / superseded]

**Dependency ordering changes:**
- [A] must now come before [B], not after

---

## Q4 — Adjacent bugs revealed

| Bug / issue | Location | Severity | Scope | Follow-up required |
|---|---|---|---|---|
| [description] | [file:line] | HIGH / MED / LOW | Out-of-scope | [ticket / "add to roadmap"] |

---

## Q5 — Requires human decision?

**Human decision required:** YES / NO

If YES:
- Decision required: [description]
- Options: [A] vs [B]
- Why this cannot be resolved by the agent: [one sentence]

---

## Q6 — Should we stop?

**Recommendation:** CONTINUE / PAUSE / REDESIGN / STOP

**Rationale:** [one paragraph]

---

## Q7 — Should work be simplified, deleted, or replaced?

**Simplification opportunity:** YES / NO — [if yes: description]
**Prior art available:** YES / NO — [if yes: what library/pattern]
**Delete recommendation:** YES / NO — [if yes: what and why]

---

## Summary

```
task_id: [task_id]
cto_recommendation: CONTINUE | CORRECTION | PAUSE | REDESIGN | STOP
roadmap_changes_required: YES | NO
human_decision_required: YES | NO
adjacent_bugs_found: [count]
next_prompt_still_valid: YES | NO
```
