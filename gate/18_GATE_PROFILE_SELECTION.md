# Step 18 — Gate Profile Selection

**This is the first step of every gate run.** It runs before evidence adequacy, before the panel, before any reviewers.

**State machine:** Write `current_state: GATE_PROFILE_SELECTION_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

---

## Why profile selection runs first

Without profile selection, the gate has no way to know which states are required, which states are skippable, and which terminal state to target. Running profile selection first locks in these decisions before any evidence is collected or any reviewer runs.

If profile selection is blocked (task prompt too ambiguous to classify), the gate must halt immediately and return `GATE_PROFILE_SELECTION_BLOCKED` rather than running any evidence or review steps.

---

## Inputs

- The task prompt
- The task file-touch map (list of files the task will modify)
- Any explicit gate profile specified by the operator in the task prompt
- `GATE_PROFILE_SELECTOR.md` — risk tier definitions and hot files list
- `GATE_PROFILES.md` — required states per profile

---

## Step 1 — Identify risk tier

Using `GATE_PROFILE_SELECTOR.md`:

1. List every file in the task's file-touch map
2. Check each file against the hot files list
3. Identify whether the task involves migrations, runtime state, or gate/handoff logic
4. Identify whether the task claims live behavior is fixed or production wiring is complete
5. Check all escalation triggers

Record:

```
RISK_TIER_ASSESSMENT
Files in touch map: [count]
Hot files found: [list or "none"]
Migration files: [list or "none"]
Live-behavior claims: [list or "none"]
Escalation triggers fired: [list or "none"]
Determined risk tier: D0 | D1 | D2 | D2-hot | D3 | D4
Rationale: [one sentence]
```

---

## Step 2 — Select profile

Map risk tier to profile:

| Risk tier | Default profile |
|---|---|
| D0 | GATE_LITE |
| D1 | GATE_LITE |
| D2 | GATE_STANDARD |
| D2-hot | GATE_FULL |
| D3 | GATE_FULL |
| D4 | GATE_FULL |
| Any tier with domain addenda | GATE_FULL_PLUS_DOMAIN_ADDENDUM |

If the operator specified a profile in the task prompt:
- If the specified profile matches or exceeds the default: use the specified profile
- If the specified profile is weaker than the default: record `profile_override_required: true`, but treat the eventual package as blocking under Gate 5.2 with `WRONG_GATE_PROFILE`

---

## Step 3 — Identify domain addenda

Check whether any of the following apply:
- LLM model routing or provider selection changes → `model_id_validation` addendum
- Multi-tenant data isolation → `data_boundary` addendum
- Security-sensitive path → `threat_model` addendum
- Financial/billing system → `financial_audit_trail` addendum
- Medical/safety-critical → `safety_critical` addendum
- Explicit addendum named in task prompt → add it

For each addendum: verify that `gate/domain_addenda/<name>.md` exists. If the addendum file is missing, halt: `GATE_PROFILE_SELECTION_BLOCKED` with reason "domain addendum file not found: `gate/domain_addenda/<name>.md`".

Gate 5.4 also requires the final package to export `reports/<task_area>/DOMAIN_ADDENDUM_<name>.md` for every selected addendum.

---

## Step 4 — Check for human decision requirement

If any of the following are true, set `human_decision_required: true`:
- Task prompt is ambiguous about which files will be touched
- Risk tier could be D2 or D4 depending on interpretation
- Escalation triggers contradict each other
- An addendum is required but the addendum file does not exist and cannot be created without human guidance

---

## Step 5 — Write GATE_PROFILE_SELECTION.md

Copy `GATE_PROFILE_SELECTION_TEMPLATE.md` to `reports/<task_area>/GATE_PROFILE_SELECTION.md`.

Fill in all fields. The YAML selector output at the bottom must be complete with no placeholders.

---

## Step 6 — Update CURRENT_STATE.yaml

```yaml
current_state: GATE_PROFILE_SELECTION_COMPLETE
gate_profile: GATE_LITE | GATE_STANDARD | GATE_FULL | GATE_FULL_PLUS_DOMAIN_ADDENDUM
risk_tier: D0 | D1 | D2 | D2-hot | D3 | D4
domain_addenda: []
profile_override_required: false
human_decision_required: false
```

If `human_decision_required: true`:
```yaml
current_state: GATE_PROFILE_SELECTION_BLOCKED
gate_completed: true
```

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Profile selected, no human decision required | `GATE_PROFILE_SELECTION_COMPLETE` | `01_EVIDENCE_ADEQUACY.md` |
| Human decision required | `GATE_PROFILE_SELECTION_BLOCKED` | Return to operator with blocking reason |

---

## Hard rules

1. Profile selection must run before any other gate state.
2. `GATE_NOT_STARTED` → `CYCLE_TRACKER_INITIALIZED` → `GATE_PROFILE_SELECTION_IN_PROGRESS` → `GATE_PROFILE_SELECTION_COMPLETE` is the required sequence before `EVIDENCE_ADEQUACY_IN_PROGRESS`.
3. If profile selection cannot complete (ambiguity, missing addendum file), the gate halts immediately. No evidence collection, no reviewers.
4. Under Gate 5.2, a profile weaker than what the risk tier and task kind require is blocking at package-validation time.
5. The gate profile selected here governs which states are required throughout this run. It cannot be changed mid-run without restarting profile selection.
