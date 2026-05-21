# Gate Profile Selection

**Task ID:** SYSTEM-GAP-ANALYST-001
**Task area:** system-gap-analyst
**Gate run ID:** gate-2026-05-21T00:00:00Z
**Selection completed at:** 2026-05-21T00:00:03Z

---

## Risk Tier Assessment

**Files in task file-touch map:**
- `prompts/metabuilder/35_system_gap_analyst.md` (new)
- `src/claude_pipeline/nodes/system_gap_analyst.py` (new)
- `src/claude_pipeline/state.py` (modified — append TypedDicts and one field)
- `src/claude_pipeline/graph.py` (modified — add node and rewire one edge)
- `src/claude_pipeline/nodes/plan.py` (modified — add `_render_gap_blocks` and one `{gap_blocks}` placeholder)
- `tests/__init__.py` (new — empty)
- `tests/test_system_gap_analyst.py` (new)
- `README.md` (modified — diagram, layout, new subsection)
- `conftest.py` (new — registers `src/` on sys.path for pytest)

**Hot files found in touch map:**
- none — no entries from `GATE_PROFILE_SELECTOR.md` hot files list are touched. `state.py` is appended-to (not refactored). `graph.py` adds a single node and one edge swap in two functions; both call sites are mirrored.

**Migration files found:**
- none — no SQL, no schema migration registry, no checkpoint format change.

**Live-behavior claims in task prompt:**
- none — the task explicitly notes the contract/planner split has NOT landed yet and that this is an additive pre-lane. No claim that production behaviour is fixed; no claim that any existing run is unblocked.

**Escalation triggers fired:**
- none — task is additive, read-only-at-runtime (the new node consumes intake + research and produces advisory output), no concurrency, no auth, no provider routing change.

**Determined risk tier:** D2

**Risk tier rationale:** Moderate, additive change — five tracked files plus tests and prompt; no hot files, no migration, no runtime-state mutation. Solidly D2 per `GATE_PROFILE_SELECTOR.md`.

---

## Profile Selection

**Operator-specified profile (from task prompt):** not specified

**Default profile for this risk tier:** GATE_STANDARD (D2 + task_kind=normal_impl per `required_min_profile` in `check_gate_package.py`)

**Selected profile:** GATE_STANDARD

**Profile override required:** NO

**Override warning (if YES):** not applicable

---

## Domain Addenda

**Addenda applicable to this task:**
- none applicable — no LLM provider routing change (the new node sets only `model=` because the existing `claude --print` transport doesn't expose temperature/max_tokens), no multi-tenant boundary, no security-sensitive path, no financial/safety-critical surface.

**Addendum files missing (blocking):**
- none

---

## Human Decision Assessment

**Human decision required:** NO

**Reason (if YES):** not applicable

---

## Required States for This Gate Run

Based on profile GATE_STANDARD:

**States required:**
- GATE_PROFILE_SELECTION
- EVIDENCE_ADEQUACY
- EVIDENCE_CONSISTENCY
- PANEL (R1, R2, R3, R4, R5)
- GATE_VERDICT
- FINAL_PACKAGE_AUDIT (15)
- CANONICAL_HANDOFF_AUDIT (16)
- FINAL_PACKET_AUDITOR (37)
- EXPORT_CHANNEL_AUDIT (29)
- DIFF_BASE_SCOPE_AUDIT (30)
- NEXT_PROMPT_DECISION (34)
- WARNING_OUTPUT_AUDIT (22)
- REQUIRED_TEST_SET_EXACTNESS (23)

**States NOT APPLICABLE (produce `_NOT_APPLICABLE.md` proof file):**
- DIRTY_WORKTREE_RECURRENCE_AUDIT
- CONCURRENCY_ASSUMPTIONS_AUDIT
- CTO_OPERATOR_INSIGHT_REVIEW
- GATE_EFFECTIVENESS_LOG

---

## YAML Selector Output

```yaml
gate_profile: GATE_STANDARD
selected_profile: GATE_STANDARD
risk_tier: D2
task_kind: normal_impl
profile_selection_rationale: "Additive D2-class implementation of a new LangGraph pre-lane node; no hot files, no migration, no runtime-state mutation, no live-behaviour claim. risk_tier=D2 + task_kind=normal_impl yields GATE_STANDARD as the minimum required profile per check_gate_package.py."
domain_addenda: []
profile_override_required: false
human_decision_required: false
```

---

## Next step

Wrote `current_state: GATE_PROFILE_SELECTION_COMPLETE` to `CURRENT_STATE.yaml` (see `state_history`). Routed to `01_EVIDENCE_ADEQUACY.md`.
