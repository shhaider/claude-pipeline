# Prompt Contract Review

**Task ID:** [task_id]
**Task area:** [task_area]
**Risk tier:** [D0 | D1 | D2 | D2-hot | D3 | D4]
**Review completed at:** [ISO timestamp]

---

## Check 1 — Ambiguous terms

| Term found | Location in prompt | Possible interpretations | Interpretation required |
|---|---|---|---|
| [term] | [quote] | [A] / [B] | [which one and why] |

Ambiguous terms found: [count] | None found

---

## Check 2 — Hidden assumptions

| Assumption | Stated in prompt? | Consequence if wrong |
|---|---|---|
| [assumption] | YES / NO | [what breaks] |

Hidden assumptions found: [count] | None found

---

## Check 3 — Lifecycle timing ambiguity

| Artifact | Required timing | Timing stated in prompt? | Issue |
|---|---|---|---|
| [artifact] | before/after [event] | YES / NO | [if NO: what could go wrong] |

Timing issues found: [count] | None found

---

## Check 4 — Forbidden interpretations

**Files that must NOT be modified (as stated in prompt):**
- [file] — [stated? YES/NO]

**Behaviors that must NOT change:**
- [behavior] — [stated? YES/NO]

**Phases that must NOT be started:**
- [phase] — [stated? YES/NO]

Missing forbidden interpretation statements: [count] | None missing

---

## Check 5 — Missing proof specifications

| Claimed behavior | Proof required | Proof specified in prompt? | Gap |
|---|---|---|---|
| [behavior] | [proof type] | YES / NO | [what is missing] |

Missing proof specifications: [count] | None missing

---

## Check 6 — Unclear allowed/forbidden files

**File-touch map stated:** YES / NO

**Hot files acknowledged:** YES / NO / N/A

**Forbidden files stated:** YES / NO

File map clarity issues: [count] | None found

---

## Check 7 — Missing model/tier recommendation

**Model/tier specified:** YES / NO

**Required for this risk tier:** YES / NO

Missing model recommendation: YES / NO

---

## Check 8 — Missing repo cleanliness rule

**Expected final git status stated:** YES / NO

**Issue:** [what is unclear about expected end state]

---

## Check 9 — Missing generated-evidence-outside-repo rule

**Evidence file locations stated:** YES / NO

**Issue:** [what is unclear about where evidence must live]

---

## Check 10 — Invalid code snippets

| Snippet location | Issue | Severity |
|---|---|---|
| [location] | [invalid syntax / non-existent reference / etc.] | BLOCKING / WARNING |

Invalid snippets found: [count] | None found

---

## Check 11 — References to non-existent files or tests

| Reference | Expected path | Exists? | Status |
|---|---|---|---|
| [reference] | [path] | YES / NO | OK / BLOCKING |

Non-existent references found: [count] | None found

---

## Check 12 — Overclaims in the prompt

| Claim | Can it be verified? | Status |
|---|---|---|
| [claim] | YES / NO | VERIFIED / UNVERIFIED / STALE |

Overclaims found: [count] | None found

---

## Summary

| Check | Issues found | Severity | Blocking? |
|---|---|---|---|
| 1 — Ambiguous terms | [count] | [HIGH/MED/LOW] | YES/NO |
| 2 — Hidden assumptions | [count] | — | YES/NO |
| 3 — Lifecycle timing | [count] | — | YES/NO |
| 4 — Forbidden interpretations | [count] | — | YES/NO |
| 5 — Missing proof specs | [count] | — | YES/NO |
| 6 — Unclear file map | [count] | — | YES/NO |
| 7 — Missing model rec | [count] | — | YES/NO |
| 8 — Missing cleanliness rule | [count] | — | YES/NO |
| 9 — Missing evidence rule | [count] | — | YES/NO |
| 10 — Invalid snippets | [count] | — | YES/NO |
| 11 — Non-existent refs | [count] | — | YES/NO |
| 12 — Overclaims | [count] | — | YES/NO |

**Total blocking issues:** [count]
**Total non-blocking issues:** [count]

---

## Verdict

```
PROMPT_CONTRACT_PASS | PROMPT_CONTRACT_NEEDS_REVISION | PROMPT_CONTRACT_BLOCKED_BY_AMBIGUITY
```

**Rationale:** [one paragraph]

---

## Required revisions (if NEEDS_REVISION or BLOCKED)

1. [specific revision required]
2. [specific revision required]
