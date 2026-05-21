# Gate Profile Selection

**Task ID:** GATE-SM-UPGRADE-2026-05-01
**Task area:** gate-state-machine-upgrade-session-2026-05-01
**Gate run ID:** gate-2026-05-01T00:00:00Z
**Selection completed at:** 2026-05-01T00:02:00Z

---

## Risk Tier Assessment

**Files in task file-touch map:**
- `/Users/syedhaider/Downloads/gate/00_START.md` (updated)
- `/Users/syedhaider/Downloads/gate/STATE_MACHINE.md` (new)
- `/Users/syedhaider/Downloads/gate/TRANSITION_RULES.md` (new)
- `/Users/syedhaider/Downloads/gate/STATE_SCHEMA.md` (new)
- `/Users/syedhaider/Downloads/gate/STATE_FILE_TEMPLATE.yaml` (new)
- `/Users/syedhaider/Downloads/gate/CLAIMS_LEDGER_TEMPLATE.yaml` (new)
- `/Users/syedhaider/Downloads/gate/EVIDENCE_LEDGER_TEMPLATE.yaml` (new)
- `/Users/syedhaider/Downloads/gate/PACKAGE_MANIFEST_TEMPLATE.md` (new)
- `/Users/syedhaider/Downloads/gate/STALE_FILE_POLICY.md` (new)
- `/Users/syedhaider/Downloads/gate/STALE_FILE_REGISTER_TEMPLATE.yaml` (new)
- `/Users/syedhaider/Downloads/gate/15_FINAL_PACKAGE_AUDIT.md` (new)
- `/Users/syedhaider/Downloads/gate/16_CANONICAL_HANDOFF_AUDIT.md` (new)
- `/Users/syedhaider/Downloads/gate/17_EXECUTION_CONTEXT_AUDIT.md` (new)
- `/Users/syedhaider/Downloads/gate/STATE_MACHINE_EXAMPLES.md` (new)
- `/Users/syedhaider/Downloads/gate/SCRIPT_SPEC_check_gate_package.md` (new)
- `/Users/syedhaider/Downloads/gate/SELF_TEST_GATE_STATE_MACHINE.md` (new)
- `/Users/syedhaider/Downloads/gate/06_R2_ACTIVE_PROOF.md` (updated)
- `/Users/syedhaider/Downloads/gate/07_R3_AI_PATTERNS.md` (updated)
- `/Users/syedhaider/Downloads/gate/08_R4_HANDOFF.md` (updated)
- `/Users/syedhaider/Downloads/gate/10_GATE_VERDICT.md` (updated)
- `/Users/syedhaider/Downloads/gate/12_PASS_HANDOFF.md` (updated)
- `/Users/syedhaider/.claude/skills/gate/SKILL.md` (new)
- `tests/gate_state_machine/fixtures/bad_right_command_wrong_branch/` (4 files, new)
- `tests/gate_state_machine/fixtures/bad_local_path_package_listing/` (2 files, new)

**Hot files found in touch map:**
- `00_START.md` — reason: explicitly listed as hot file ("Gate and review logic" category)
- `STATE_MACHINE.md` — reason: explicitly listed as hot file
- `TRANSITION_RULES.md` — reason: explicitly listed as hot file
- `STATE_SCHEMA.md` — reason: explicitly listed as hot file
- `15_FINAL_PACKAGE_AUDIT.md` — reason: "Any file under gate/ that defines state transitions or verdicts"
- `16_CANONICAL_HANDOFF_AUDIT.md` — reason: same
- `17_EXECUTION_CONTEXT_AUDIT.md` — reason: same
- `10_GATE_VERDICT.md` — reason: same
- `12_PASS_HANDOFF.md` — reason: same

**Migration files found:** none

**Live-behavior claims in task prompt:** none — this is a documentation/specification task

**Escalation triggers fired:**
- "Diff touches any hot file → At least GATE_FULL" — 9 hot files in touch map
- "Modifies gate files, handoff packages, or review logic → D3" — task modifies state machine, transition rules, and all verdict steps

**Determined risk tier:** D3

**Risk tier rationale:** Task modifies gate core files (STATE_MACHINE.md, TRANSITION_RULES.md, STATE_SCHEMA.md, 00_START.md) and 5+ additional gate step files that define verdicts and routing — exactly matching the D3 definition "Modifies gate files, handoff packages, or review logic."

---

## Profile Selection

**Operator-specified profile (from task prompt):** not specified

**Default profile for this risk tier:** GATE_FULL (D3 → GATE_FULL per selector table)

**Selected profile:** GATE_FULL

**Profile override required:** NO

---

## Domain Addenda

**Addenda applicable to this task:** none
- No LLM model routing or provider selection changes
- No multi-tenant data isolation
- No security-sensitive path
- No financial/billing system
- No medical/safety-critical
- No explicit addendum in task prompt

**Addendum files missing (blocking):** none

---

## Human Decision Assessment

**Human decision required:** NO

**Reason:** Risk tier is unambiguously D3 — multiple explicitly-named hot files in touch map, task description clearly matches the D3 definition. No contradicting triggers. No ambiguity about file scope.

---

## Required States for This Gate Run

Based on profile GATE_FULL:

**States required (mandatory):**
- GATE_PROFILE_SELECTION_COMPLETE
- EVIDENCE_ADEQUACY_IN_PROGRESS
- EVIDENCE_CONSISTENCY_IN_PROGRESS
- PANEL_ENTRY_VERIFIED
- R1 through R5 (all five reviewers)
- GATE_VERDICT_ISSUED
- FINAL_PACKAGE_AUDIT_IN_PROGRESS
- CANONICAL_HANDOFF_AUDIT_IN_PROGRESS
- EXECUTION_CONTEXT_AUDIT_* (conditional — run if context claims present)
- PROMPT_CONTRACT_REVIEW_* (mandatory for GATE_FULL)
- PRODUCTION_CALLER_AUDIT_* (mandatory for GATE_FULL)
- CONSUMER_API_PROOF_AUDIT_* (mandatory for GATE_FULL)
- STRANDED_HELPER_AUDIT_* (mandatory)
- EXPORT_CHANNEL_AUDIT_* (mandatory)
- DIFF_BASE_SCOPE_AUDIT_* (mandatory)
- NEXT_PROMPT_DECISION_* (mandatory)
- CTO_OPERATOR_INSIGHT_REVIEW_* (mandatory)
- GATE_EFFECTIVENESS_LOG_*
- MANIFEST_FINALIZATION_AUDIT_*
- IMPLEMENTER_PROMPT_LINT_* (applicable — SKILL.md is a prompt artifact)
- DOWNSTREAM_CONSUMER_READINESS_AUDIT_*

**States NOT APPLICABLE (produce _NOT_APPLICABLE.md proof file):**
- ENFORCEMENT_AUDIT_* — NOT_APPLICABLE: task is doc-only, no new programmatic enforcement created
- WARNING_OUTPUT_AUDIT_* — NOT_APPLICABLE: no test output in this task
- REQUIRED_TEST_SET_EXACTNESS_* — NOT_APPLICABLE: no test suite
- MIGRATION_RUNNER_PROOF_* — NOT_APPLICABLE: no DB/schema migrations
- DIRTY_WORKTREE_RECURRENCE_AUDIT_* — NOT_APPLICABLE: gate folder has no git repo
- WORK_ALLOCATION_AUDIT_* — NOT_APPLICABLE: single agent worked on task
- FLAKE_TIMEOUT_AUDIT_* — NOT_APPLICABLE: no test suite
- CONCURRENCY_ASSUMPTIONS_AUDIT_* — NOT_APPLICABLE: no shared runtime state

**NOTE — Gap in gate spec found during Step 18:**
GATE_PROFILES.md requires `ARTIFACT_LIFECYCLE_TIMING_AUDIT_*` for GATE_FULL, but no step file (19_ARTIFACT_LIFECYCLE_TIMING_AUDIT.md or similar) exists. Template exists at `ARTIFACT_LIFECYCLE_TIMING_AUDIT_TEMPLATE.md`. This is flagged as a gap in the gate spec itself — will surface in R1 review.

---

## YAML Selector Output

```yaml
gate_profile: GATE_FULL
risk_tier: D3
domain_addenda: []
rationale:
  - "Task modifies STATE_MACHINE.md, TRANSITION_RULES.md, STATE_SCHEMA.md, 00_START.md (all explicitly hot files), plus 5 additional gate step files that define verdicts and routing"
  - "D3 definition exactly matched: 'Modifies gate files, handoff packages, or review logic'"
  - "GATE_FULL required: hot file escalation trigger fired on 9 files"
profile_override_required: false
human_decision_required: false
```

---

## Next step

Write `current_state: GATE_PROFILE_SELECTION_COMPLETE` to CURRENT_STATE.yaml.

Route to `01_EVIDENCE_ADEQUACY.md`.
