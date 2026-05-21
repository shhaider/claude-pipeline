# Gate 4.1 Usage Guide

This guide is for operators, orchestrators, and agents using the Gate 4.1 risk-tiered state machine.

---

## When to use each profile

### GATE_LITE

Use when:
- The task is documentation-only (no code changes)
- The task is a single-line fix to a non-hot leaf module
- No downstream consumers can break
- No new exports, no migrations, no runtime state changes
- Hot files are not in the diff

Time estimate: fastest gate run. Skips most Gate 4.1 additional checks.

### GATE_STANDARD

Use when:
- The task is a normal D2 implementation slice
- New features in non-hot modules
- New test coverage
- The task adds new helpers or exports that need to be verified as wired
- No hot files, no migrations, no live-behavior claims

Time estimate: moderate gate run. Runs production caller audit, consumer API audit, warning audit, test set exactness, export channel, diff scope, next prompt decision.

### GATE_FULL

Use when:
- The task touches any hot file
- The task involves a DB migration
- The task claims "live behavior is fixed"
- Multiple agents are coordinating on shared files
- The gate cycle count reached 3 or higher in a prior attempt
- The task modifies gate logic, handoff packages, or branch governance
- LLM model routing or provider selection is involved

Time estimate: most thorough gate run. All Gate 4.1 checks plus CTO operator insight review and gate effectiveness log.

### GATE_FULL_PLUS_DOMAIN_ADDENDUM

Use when:
- Everything that requires GATE_FULL, plus
- A specific domain addendum applies (model ID validation, data boundary, threat model, etc.)

Time estimate: same as GATE_FULL plus addendum-specific checks.

---

## How the operator specifies the profile in a task prompt

Add a gate instruction at the top of the task prompt:

```
Gate: GATE_STANDARD
```

```
Gate: GATE_FULL — touches fallback_state_manager.js (hot file)
```

```
Gate: GATE_FULL_PLUS_DOMAIN_ADDENDUM — addenda: [model_id_validation]
Note: This task changes LLM model routing. Run model ID validation addendum.
```

```
Gate: auto — let profile selector decide based on file-touch map
```

If no gate instruction is present, the agent uses `Gate: auto` and runs `18_GATE_PROFILE_SELECTION.md` to determine the profile.

---

## What the agent does when no profile is specified

1. Run `18_GATE_PROFILE_SELECTION.md`
2. Identify all files in the task's file-touch map
3. Check each against the hot files list in `GATE_PROFILE_SELECTOR.md`
4. Apply escalation triggers
5. Select the default profile for the determined risk tier
6. Record `gate_profile`, `risk_tier`, and `profile_selection_rationale` in CURRENT_STATE.yaml
7. Proceed to evidence adequacy assessment

If the task prompt is ambiguous about which files will be touched, stop and ask the operator before proceeding.

---

## How to include gate proof files in signouts

The final package must include:
1. `reports/<task_area>/GATE_PROFILE_SELECTION.md` — profile selection decision
2. All required proof files for the selected profile (see `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`)
3. A `STATE_NAME_NOT_APPLICABLE.md` file for every state skipped due to profile
4. For GATE_FULL: `reports/<task_area>/gate_used/` — a copy or reference to the gate source used

When generating the zip, include the gate folder:
```bash
cd /path/to/project
zip -r PACKAGE.zip reports/<task_area>/ gate/  # include gate/ for GATE_FULL
```

For GATE_LITE and GATE_STANDARD, including the gate folder is recommended but not blocking.

---

## How to record gate effectiveness

After each gate run with GATE_FULL profile:
1. Run `36_GATE_EFFECTIVENESS_LOG.md`
2. Fill in `GATE_EFFECTIVENESS_LOG_TEMPLATE.md`
3. Append a row to `gate/GATE_EFFECTIVENESS_REGISTER.md`

The effectiveness register is the feedback loop that allows the gate to improve. Review it monthly to tune the profile selector and hot files list.

---

## Example prompt snippets for each profile

### GATE_LITE example prompt
```markdown
**Task:** Fix typo in CHANGELOG.md — "recieved" → "received" (line 47)
**Gate:** GATE_LITE
**Risk tier:** D0
**File-touch map:** CHANGELOG.md
**Success:** CHANGELOG.md updated, no other files changed
```

### GATE_STANDARD example prompt
```markdown
**Task:** Add `getSessionCount()` to sessionRepository.js
**Gate:** GATE_STANDARD
**Risk tier:** D2
**File-touch map:** src/repositories/sessionRepository.js, tests/repositories/session.test.js
**Success criteria:**
- `getSessionCount(userId)` implemented and tested
- Consumer API tested through repository method (not raw SQL)
- Production caller present (verify in route handler)
- Tests: tests/repositories/session.test.js — all pass, EXIT_CODE: 0
- Final outcome label: LIVE_BEHAVIOR_FIXED (if wired) or INFRASTRUCTURE_READY_NOT_WIRED (if not yet)
```

### GATE_FULL example prompt
```markdown
**Task:** Update LLM fallback tier routing in fallback_state_manager.js
**Gate:** GATE_FULL — hot file
**Risk tier:** D2-hot (fallback_state_manager.js is a listed hot file)
**Domain addenda:** model_id_validation
**File-touch map:** src/llm/fallback_state_manager.js, tests/llm/fallback_state_manager.test.js
**Hot file acknowledgment:** fallback_state_manager.js is in the hot files list. Gate must run at GATE_FULL.
**Success criteria:**
- Routing logic updated per spec
- All model IDs validated via model ID validation addendum
- Production caller proven (LLM dispatch route)
- Tests: exact test file required — tests/llm/fallback_state_manager.test.js
- Final outcome label: LIVE_BEHAVIOR_FIXED (after production caller proven)
**Forbidden files:** Do not touch scribbli_model_policy.js — separate sprint
```

---

## How to handle "Claude/Codex/Kimi produced work but a separate agent selects the gate lane"

This is the standard pattern when an implementer agent and a gate agent are separate:

1. **Implementer agent** produces the implementation and evidence
2. **Gate agent** (separate spawn, cold) reads the package and selects the gate lane independently
3. The gate agent must NOT be told which profile to use — it should derive it from the evidence
4. If the gate agent derives a different profile than the implementer used: this is a signal that either the implementer underestimated the risk (escalate) or the gate agent is overcalibrated (record in effectiveness log)

The gate agent's profile selection is independent and authoritative. The implementer's profile suggestion (if any) is advisory.

---

## Example operator instruction (standing instruction)

Include this in the system prompt for any orchestrator managing Gate 4.1 tasks:

```
Use Gate Standard unless the file touch map includes hot files (see GATE_PROFILE_SELECTOR.md hot files list). If uncertain, run Gate Profile Selection with a fresh subagent and follow its lane decision. Always include GATE_PROFILE_SELECTION.md in the package. For GATE_FULL runs, include the gate_used/ folder. Record gate effectiveness after every GATE_FULL run.
```
