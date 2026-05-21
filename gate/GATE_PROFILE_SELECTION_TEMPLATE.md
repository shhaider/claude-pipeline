# Gate Profile Selection

**Task ID:** [task_id]
**Task area:** [task_area]
**Gate run ID:** [gate_run_id]
**Selection completed at:** [ISO timestamp]

---

## Risk Tier Assessment

**Files in task file-touch map:**
- [file 1]
- [file 2]
- [...]

**Hot files found in touch map:**
- [file] — reason: [why it is hot]
- OR: none

**Migration files found:**
- [file] — reason: [SQL migration / migration registry]
- OR: none

**Live-behavior claims in task prompt:**
- "[exact quote from prompt]"
- OR: none

**Escalation triggers fired:**
- [trigger name] — reason: [...]
- OR: none

**Determined risk tier:** D0 | D1 | D2 | D2-hot | D3 | D4

**Risk tier rationale:** [one sentence]

---

## Profile Selection

**Operator-specified profile (from task prompt):** [GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS_DOMAIN_ADDENDUM | "not specified"]

**Default profile for this risk tier:** [profile]

**Selected profile:** [profile]

**Profile override required:** YES / NO

**Override warning (if YES):** The operator specified [X] but the risk tier requires [Y]. Running at [stronger profile]. If you intended [weaker profile], explicitly acknowledge the override risk in the task prompt.

---

## Domain Addenda

**Addenda applicable to this task:**
- [addendum name] — reason: [why applicable] — file: `gate/domain_addenda/<name>.md` — EXISTS: YES/NO
- OR: none applicable

**Addendum files missing (blocking):**
- [file path] — MISSING — gate halted
- OR: none

---

## Human Decision Assessment

**Human decision required:** YES / NO

**Reason (if YES):**
- [reason]

---

## Required States for This Gate Run

Based on profile [GATE_PROFILE]:

**States required:**
- [state name]
- [state name]
- [...]

**States NOT APPLICABLE (produce _NOT_APPLICABLE.md proof file):**
- [state name]
- [state name]
- [...]

---

## YAML Selector Output

The Gate 5.2-R1 checker requires all four fields below to be present, regardless of which
profile is selected (including `GATE_LITE`):

```yaml
gate_profile: GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS_DOMAIN_ADDENDUM
selected_profile: GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS_DOMAIN_ADDENDUM
risk_tier: D0 | D1 | D2 | D2_HOT | D3 | D4
task_kind: docs | tiny_test | normal_impl | hot_file | migration | runtime_state |
           merge_verification | release_verification | production_wiring |
           provider_model_routing | gate_change | prompt_authoring | evidence_package
profile_selection_rationale: "[non-empty rationale combining risk tier and profile selection reasoning]"
domain_addenda: []
profile_override_required: false
human_decision_required: false
```

Missing any of `selected_profile`/`gate_profile`, `risk_tier`, `task_kind`, or
`profile_selection_rationale`/`reason` triggers a blocking flag from the Gate 5.2-R1
checker (`MISSING_GATE_PROFILE_SELECTION`, `MISSING_RISK_TIER`, `MISSING_TASK_KIND`,
`MISSING_PROFILE_REASON`).

---

## Next step

Write `current_state: GATE_PROFILE_SELECTION_COMPLETE` (or `GATE_PROFILE_SELECTION_BLOCKED`) to CURRENT_STATE.yaml.

Route to `01_EVIDENCE_ADEQUACY.md`.
