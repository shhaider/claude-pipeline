# Gate Profile Selector

Gate 5.4 mechanically enforces profile strength using `risk_tier` plus `task_kind`. A weaker selected profile is blocking with `WRONG_GATE_PROFILE`.

This file defines how to select the correct gate profile for any task. Read this during `18_GATE_PROFILE_SELECTION.md`.

> **Gate 5.3 note:** The Final Packet Auditor (state 37) runs AFTER profile selection and AFTER all required reviewers and audits. Profile selection determines whether the auditor is mandatory (GATE_STANDARD/FULL/FULL_PLUS) or NA-eligible for non-export packages (GATE_LITE only). See `GATE_5_3_USAGE_RULE.md`.

## Mandatory profile-selection metadata (Gate 5.4)

`GATE_PROFILE_SELECTION.md` must record all four of the following for **every** profile,
including `GATE_LITE`:

- `selected_profile` (or `gate_profile`)
- `risk_tier`
- `task_kind`
- `reason` (or `profile_selection_rationale`)

The Gate 5.4 checker fires `MISSING_RISK_TIER`, `MISSING_TASK_KIND`, and
`MISSING_PROFILE_REASON` when any of these are absent — even on Lite packages. Without
risk_tier and task_kind, the selector cannot detect a too-weak profile choice.

---

## Risk tier definitions

### D0 — Documentation only

No code changes. No schema changes. No config changes.

**Examples:**
- Fixing a typo in a README
- Adding a comment to an existing file
- Writing a new docs file with no code
- Updating a CHANGELOG entry

**Default profile:** GATE_LITE

---

### D1 — Tiny isolated change

Code changes that are:
- Bounded to a single leaf module or single test file
- Not touching any hot file
- Not changing any shared interface, export signature, or database schema
- Not affecting any other module's behavior
- Not adding new exports that downstream code will consume

**Examples:**
- Adding a constant to a utility file that is already used by only one caller
- Fixing a single-line bug in a non-hot helper function
- Adding a new test for an existing function
- Renaming a local variable inside a private function

**Default profile:** GATE_LITE

---

### D2 — Standard implementation slice

Normal bounded feature work. The most common tier for sprint tasks.

**Examples:**
- Adding a new feature to an existing module that is not a hot file
- Implementing a new API endpoint in a non-critical route
- Refactoring a bounded subsystem with no cross-system impact
- Adding a new helper module with clear production wiring
- Writing a new test suite for an existing feature

**Default profile:** GATE_STANDARD

---

### D2-hot — Standard work touching hot files

Same scope as D2 but touches one or more hot files. Hot files are listed below.

**Examples:**
- Any D2 task whose diff includes a hot file
- Adding a new model to a routing table
- Updating a feature flag registry entry

**Default profile:** GATE_FULL

**Escalation trigger:** Any diff line touching a hot file upgrades from D2 to D2-hot.

---

### D3 — Migrations, runtime state, gate/handoff logic

Work that:
- Modifies database schema or migration registry
- Changes runtime state persistence, checkpointing, or resume logic
- Modifies gate files, handoff packages, or review logic
- Involves branch/worktree governance
- Produces or verifies merge evidence

**Examples:**
- Adding a new SQL migration
- Changing how CURRENT_STATE.yaml is structured or read
- Modifying 00_START.md or any gate step file
- Writing a merge verification proof
- Implementing a checkpoint/resume mechanism for a long-running agent

**Default profile:** GATE_FULL

---

### D4 — Provider/model routing, cross-system evidence, multi-agent coordination

Work that:
- Modifies LLM provider selection, model routing, or fallback logic
- Produces cross-system evidence packages (evidence generated on one system, reviewed on another)
- Coordinates multiple active agents touching shared state
- Involves repeated correction loops (gate cycle 3 or higher reached in a prior sprint)
- Claims a production system behavior is fixed when it was previously in a broken state

**Examples:**
- Updating `runtime_lane_registry.js` or `scribbli_model_policy.js`
- Producing a VPS-generated package reviewed by a Mac-local agent
- Two agents concurrently modifying the same module with shared exports
- A task that has already failed gate twice and is now on cycle 3
- Claiming that a crash recovery path is now fixed and live

**Default profile:** GATE_FULL

---

## Hot files list

A hot file is any file whose incorrect modification can break a production path, crash a service, misroute LLM calls, or corrupt system state. Touching any hot file in a task's diff upgrades the risk tier to at least D2-hot.

**Current hot files (update this list when new hot files are identified):**

### LLM routing and model selection
- `runtime_lane_registry.js`
- `scribbli_model_policy.js`
- `fallback_state_manager.js`
- `llm_proxy.js`
- `scribbli_llm.js`
- Any file containing hardcoded `claude-*` model strings

### Gate and review logic
- `00_START.md` (this gate file)
- `STATE_MACHINE.md`
- `TRANSITION_RULES.md`
- `STATE_SCHEMA.md`
- `GATE_PROFILES.md`
- `GATE_PROFILE_SELECTOR.md`
- Any file under `gate/` that defines state transitions or verdicts

### Branch governance and CI/CD
- `.github/workflows/*.yml` — any workflow file
- Any pre-merge hook script
- Any branch protection rule config

### Database migration registry
- `migrations/index.js` (or equivalent migration registry)
- Any file that registers or sequences SQL migration files

### Production configuration
- `.env` (or any active environment file)
- Any file that sets API keys, service URLs, or feature flags used in production

### Shared interfaces (files consumed by 3+ other modules)
- Any barrel export file (`index.js`, `index.ts`) that re-exports from multiple modules
- Any shared type definition file consumed by both production and test code
- Any schema file used by both a producer and one or more consumers

---

## Escalation triggers

The following conditions automatically escalate the profile, regardless of the base risk tier:

| Trigger | Escalation |
|---|---|
| Diff touches any hot file | → At least GATE_FULL |
| Task involves a SQL migration | → At least GATE_FULL |
| Task claims "live behavior fixed" | → At least GATE_FULL |
| Task involves multi-agent coordination on shared files | → At least GATE_FULL |
| Gate cycle count reached 3 or higher in a prior attempt | → At least GATE_FULL |
| Task modifies LLM model routing or provider selection | → GATE_FULL + model validation addendum |
| Task involves cross-system evidence (VPS → Mac, etc.) | → At least GATE_FULL |
| Task involves branch merge verification | → At least GATE_FULL |
| Domain addendum applies | → GATE_FULL_PLUS_DOMAIN_ADDENDUM |

---

## Default profile

If no profile is explicitly specified in the task prompt, use this algorithm:

1. Identify all files in the task's diff or file-touch map
2. If any file is in the hot files list → D2-hot → GATE_FULL
3. If any file is a SQL migration or migration registry → D3 → GATE_FULL
4. If the task claims "live behavior fixed" or "production wiring" → D3 → GATE_FULL
5. If the task is docs-only and no code changes → D0 → GATE_LITE
6. If the task is a single bounded leaf-module change with no hot files → D1 → GATE_LITE
7. Otherwise → D2 → GATE_STANDARD

When in doubt between GATE_STANDARD and GATE_FULL, choose GATE_FULL.

---

## When to use domain addenda

Specify domain addenda when:
- The task involves a system with additional compliance requirements (financial, medical, safety-critical)
- The task modifies LLM model routing (use model ID validation addendum)
- The task involves multi-tenant data isolation (use data boundary addendum)
- The task is in a security-sensitive path (use threat model addendum)
- The operator explicitly specifies an addendum in the task prompt

List all applicable addenda in the `domain_addenda` field of the profile selection output.

Gate 5.4 mechanically validates `domain_addenda` for `GATE_FULL_PLUS_DOMAIN_ADDENDUM` packages:
- the list must be present and non-empty;
- each name must match `^[A-Za-z0-9_-]+$`;
- each source definition must exist under `domain_addenda/<name>.md`;
- each package proof must exist at `reports/<task_area>/DOMAIN_ADDENDUM_<name>.md`.

---

## When to stop and ask for human or ChatGPT decision

Stop profile selection and escalate to human if:
- The task prompt is ambiguous about which files will be touched
- The task could be D2 or D4 depending on interpretation, and the wrong choice risks production
- The task involves a new hot file not on the current list (stop, add it, then continue)
- The task crosses system boundaries in a way that is not covered by any existing domain addendum
- Two or more escalation triggers contradict each other (e.g., docs-only flag set but hot file is in diff)
- The operator has specified `human_decision_required: true` in the task prompt
- The task prompt itself fails `PROMPT_CONTRACT_REVIEW` (ambiguous, overclaiming, or contradictory)

When escalating: write `human_decision_required: true` in the profile selection output and route to `GATE_PROFILE_SELECTION_BLOCKED`.

---

## Operator instruction examples

```
Gate: GATE_STANDARD
```

```
Gate: GATE_FULL — touches fallback_state_manager.js
```

```
Gate: GATE_FULL_PLUS_DOMAIN_ADDENDUM — addenda: [model_id_validation]
```

```
Gate: auto — let profile selector decide
```

If the operator specifies a profile that is weaker than what the selector would choose (e.g., GATE_LITE for a hot-file task), record `profile_override_required: true`, but treat the eventual package as blocking under Gate 5.4 with `WRONG_GATE_PROFILE`.
