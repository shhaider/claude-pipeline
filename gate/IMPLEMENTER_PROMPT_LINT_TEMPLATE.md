# Implementer Prompt Lint

**Task ID:** [task_id]
**Task area:** [task_area]
**Prompts linted:** [list of prompt file names]
**Lint completed at:** [ISO timestamp]

---

## Prompts inspected

| Prompt file | Purpose | Risk tier |
|---|---|---|
| [path/to/P01_name.md] | [impl node description] | [D2/D3/etc.] |

---

## Check results per prompt

### Prompt: [filename]

| Check | Finding | Flag | Blocking? |
|---|---|---|---|
| 1 — Invalid code snippets | [count issues] | INVALID_CODE_SNIPPET | YES/NO |
| 2 — Unquoted JS identifiers | [count issues] | UNQUOTED_JS_IDENTIFIER | YES/NO |
| 3 — Impossible tests | [count issues] | IMPOSSIBLE_TEST | YES/NO |
| 4 — TODO placeholders | [count issues] | TODO_PLACEHOLDER_IN_SNIPPET | YES/NO |
| 5 — Forbidden file in allowed list | [count issues] | FORBIDDEN_FILE_IN_ALLOWED_LIST | YES/NO |
| 6 — Test spec completeness | [count issues] | TEST_SPEC_INCOMPLETE | YES/NO |
| 7 — Status enum scope | [count issues] | STATUS_ENUM_OVERCLAIMS_SCOPE | YES/NO |
| 8 — Model/tier recommendation | [count issues] | MISSING_MODEL_TIER_RECOMMENDATION | YES/NO |
| 9 — Evidence location rule | [count issues] | MISSING_EVIDENCE_LOCATION_RULE | YES/NO |
| 10 — Overclaiming | [count issues] | PROMPT_OVERCLAIMS | YES/NO |

**Blocking findings in this prompt:** [count]

---

## Blocking findings detail

For each blocking finding:

**Flag:** [flag name]
**Prompt:** [filename]
**Location:** [section or line reference]
**Evidence:** [exact quote or snippet]
**Why blocking:** [one sentence]
**Required fix:** [what must change]

---

## Summary

| Prompt | Total findings | Blocking findings | Pass/Fail |
|---|---|---|---|
| [filename] | [count] | [count] | PASS / FAIL |

**All prompts pass:** YES / NO

---

## Verdict

```
IMPLEMENTER_PROMPT_LINT_PASS | IMPLEMENTER_PROMPT_LINT_FAIL
```

**Return to:** [prompt-architect name or "operator"] for revision of: [list of failing prompts]
