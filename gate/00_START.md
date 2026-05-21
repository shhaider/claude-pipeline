# Gate — Entry Point (Gate 5.4)

> **Gate 5.4 callout:** Gate 5.4 keeps the FINAL_PACKET_AUDITOR state and hardens the package checker with structured final-auditor provenance, domain-addendum enforcement, fence-aware EXIT_CODE parsing, stronger NOT_APPLICABLE validation, and stronger warning-audit parsing. See `GATE_5_4_USAGE_RULE.md`.

## What this is

This gate is a mandatory addendum to any implementation, evidence, packaging, or review task. It applies even when the primary task did not explicitly ask for tests, raw outputs, snapshots, or manifests.

Read this **after completing the primary task instructions but before returning any final package or handoff.**

**Gate 5.4 — Current hardening set:**
- Strict EXIT_CODE validation: raw outputs must match `^EXIT_CODE:0\s*$` exactly. Blank `EXIT_CODE:` is BLOCKING (flag: `EXIT_CODE_BLANK`).
- Post-PASS uncaught error detection: errors after PASS summary are BLOCKING (flag: `POST_PASS_UNCAUGHT_ERROR`).
- Executable checker: `tools/check_gate_package.py` — Gate Full requires checker to exit 0.
- Manifest-driven raw output discovery: register raw outputs in EVIDENCE_LEDGER.yaml with `artifact_type: raw_test_output`.
- Pre-PASS barrier: PASS cannot be issued while any required audit state is FAIL/missing.
- Final Packet Auditor reports must use structured fenced YAML/JSON, not legacy regex-only prose.
- PASS is blocked if final-auditor independence metadata is missing, conflicting, or not achieved.
- `GATE_FULL_PLUS_DOMAIN_ADDENDUM` requires declared `domain_addenda` plus exact source and proof files.
- Fenced `EXIT_CODE:` examples do not count as raw proof.

See `GATE_5_4_USAGE_RULE.md` for the current hard rules, `GATE_5_3_USAGE_RULE.md` for prior auditor-state policy, and `GATE_5_1_USAGE_GUIDE.md` for the broader guide.

## Gate 5.4 hard rules

- Final PASS requires `tools/check_gate_package.py --final` exit `0`.
- `WRONG_GATE_PROFILE` is blocking.
- `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` is blocking.
- Stale report / output-contract contradictions are blocking.
- Required proof files must exist at the exact exported relative paths.
- Dirty git status must be empty or fully classified as unrelated external work.

## Non-negotiable rule

Do not return a final handoff, export package, READY status, COMPLETE status, or READY_FOR_NEXT_PHASE status until this gate reaches the terminal state:

```
PASS_HANDOFF_COMPLETE
```

If the gate finds fixable blockers, fix them internally. Do not ask the user to fix missing files, stale manifests, contradictory SHAs, incomplete RTMs, missing raw outputs, or similar evidence/package defects.

## How this gate works

The gate is a **strict state machine**. `CURRENT_STATE.yaml` in `reports/<task_area>/` is the single source of truth for where you are in the gate run. Every step reads it at entry and writes it at exit. No step may produce a verdict or handoff without the required prior states already recorded there.

**Navigation map (overview only — follow routing in each file, not this map):**

```
00_START (here)
  → 18_GATE_PROFILE_SELECTION  [Gate 4.1 — FIRST STEP — must complete before evidence]
      → if blocked: return to operator
      → if complete: 01_EVIDENCE_ADEQUACY

  → 01_EVIDENCE_ADEQUACY
      → if adequate: 03_EVIDENCE_CONSISTENCY
      → if upgrade needed: 02_TEST_AND_EVIDENCE_PLAN → 03_EVIDENCE_CONSISTENCY
      → if blocked: 13_BLOCKED_HANDOFF

  → 03_EVIDENCE_CONSISTENCY
      → if clean: 14_ENFORCEMENT_AUTHORITY_AUDIT
      → if fixable contradictions: fix → back to 03_EVIDENCE_CONSISTENCY
      → if blocked: 13_BLOCKED_HANDOFF

  → 14_ENFORCEMENT_AUTHORITY_AUDIT  [mandatory when task involves enforcement/gating/control]
      → if not applicable or PASS: 04_PANEL_ENTRY
      → if FAIL_AUTOFIX_REQUIRED: fix → rerun 14 → 04_PANEL_ENTRY
      → if FAIL_BLOCKED_REQUIRES_HUMAN: 13_BLOCKED_HANDOFF

  → 04_PANEL_ENTRY
      → 05_R1 → 06_R2 → 07_R3 → 08_R4 → 09_R5

  → 10_GATE_VERDICT
      → PASS: 15_FINAL_PACKAGE_AUDIT → 16_CANONICAL_HANDOFF_AUDIT → 17_EXECUTION_CONTEXT_AUDIT → 37_FINAL_PACKET_AUDITOR → 12_PASS_HANDOFF
      → FAIL_AUTOFIX: 11_FIX_CYCLE → back to 01_EVIDENCE_ADEQUACY (new cycle)
      → BLOCKED: 13_BLOCKED_HANDOFF
```

State list (still active in Gate 5.4):
- `FINAL_PACKET_AUDITOR` — independent context-light packet auditor, runs after CANONICAL_HANDOFF_AUDIT_PASS

State machine reference: `STATE_MACHINE.md`
Transition rules: `TRANSITION_RULES.md`
State schema: `STATE_SCHEMA.md`

## Before you begin — initialize the gate state

Create all four files now. Update them throughout the run.

### 1. CURRENT_STATE.yaml

Copy `STATE_FILE_TEMPLATE.yaml` to `reports/<task_area>/CURRENT_STATE.yaml`. Fill in `task_id`, `task_area`, `gate_run_id`, and `gate_started_at`. Set `current_state: CYCLE_TRACKER_INITIALIZED`.

### 2. CYCLE_TRACKER.md

Copy `CYCLE_TRACKER_TEMPLATE.md` to `reports/<task_area>/CYCLE_TRACKER.md`. Fill in task ID and task area.

### 3. CLAIMS_LEDGER.yaml

Copy `CLAIMS_LEDGER_TEMPLATE.yaml` to `reports/<task_area>/CLAIMS_LEDGER.yaml`. Add an entry every time you make a HARD_FACT claim in any report, handoff, or manifest — bind it to the artifact path that supports it.

### 4. EVIDENCE_LEDGER.yaml

Copy `EVIDENCE_LEDGER_TEMPLATE.yaml` to `reports/<task_area>/EVIDENCE_LEDGER.yaml`. Add an entry every time you create an evidence artifact (test log, diff, snapshot, git log, etc.).

### 5. STALE_FILE_REGISTER.yaml

Copy `STALE_FILE_REGISTER_TEMPLATE.yaml` to `reports/<task_area>/STALE_FILE_REGISTER.yaml`. Add an entry every time a previously-produced file is superseded.

### 6. PACKAGE_MANIFEST.md

Copy `PACKAGE_MANIFEST_TEMPLATE.md` to `reports/<task_area>/PACKAGE_MANIFEST.md`. Start filling in required files as you create them. Do not mark VERIFIED until Step 15 runs.

## Next step

**Gate 4.1 addition — Profile selection runs first.**

Before writing `EVIDENCE_ADEQUACY_IN_PROGRESS`, write `current_state: GATE_PROFILE_SELECTION_IN_PROGRESS` to CURRENT_STATE.yaml.

Read `18_GATE_PROFILE_SELECTION.md`.

Only after `GATE_PROFILE_SELECTION_COMPLETE` is recorded may you proceed to `01_EVIDENCE_ADEQUACY.md`.

Profile selection determines which states are required and which terminal state applies for this run. Skipping profile selection is a state machine violation — record it as a blocker.
