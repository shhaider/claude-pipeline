# Gate 4.1 Baseline — Pre-Upgrade Snapshot

**Created:** 2026-05-01
**Purpose:** Record the state of the gate before the 4.1 risk-tiered upgrade is applied.

---

## Existing gate files

### State sequence files (00–17)

| File | Role |
|---|---|
| `00_START.md` | Gate entry point — initialize state and route to Step 01 |
| `01_EVIDENCE_ADEQUACY.md` | Assess whether evidence is adequate, needs upgrade, or is blocked |
| `02_TEST_AND_EVIDENCE_PLAN.md` | Build evidence when EVIDENCE_UPGRADE_REQUIRED |
| `03_EVIDENCE_CONSISTENCY.md` | 8-check preflight for evidence consistency |
| `04_PANEL_ENTRY.md` | Pre-panel gate check before R1–R5 |
| `05_R1_REQUIREMENTS.md` | Reviewer 1: Requirements coverage |
| `06_R2_ACTIVE_PROOF.md` | Reviewer 2: Active proof auditor |
| `07_R3_AI_PATTERNS.md` | Reviewer 3: AI failure pattern auditor |
| `08_R4_HANDOFF.md` | Reviewer 4: Handoff completeness |
| `09_R5_ADJUDICATION.md` | Reviewer 5: Final adjudication verdict |
| `10_GATE_VERDICT.md` | Map R5 + enforcement audit to gate verdict |
| `11_FIX_CYCLE.md` | Apply fixes when FAIL_AUTOFIX_REQUIRED |
| `12_PASS_HANDOFF.md` | Issue final PASS handoff |
| `13_BLOCKED_HANDOFF.md` | Issue BLOCKED handoff |
| `14_ENFORCEMENT_AUTHORITY_AUDIT.md` | Mandatory for enforcement/gating/control tasks |
| `15_FINAL_PACKAGE_AUDIT.md` | Physical manifest + claims ledger + evidence ledger audit |
| `16_CANONICAL_HANDOFF_AUDIT.md` | Exactly-one-handoff, stale-file, consistency audit |
| `17_EXECUTION_CONTEXT_AUDIT.md` | Branch/HEAD/cwd proof for context-sensitive claims |

### Templates and ledgers

| File | Purpose |
|---|---|
| `STATE_FILE_TEMPLATE.yaml` | Template for CURRENT_STATE.yaml |
| `CYCLE_TRACKER_TEMPLATE.md` | Template for per-gate cycle tracker |
| `CLAIMS_LEDGER_TEMPLATE.yaml` | Template for HARD_FACT claim tracking |
| `EVIDENCE_LEDGER_TEMPLATE.yaml` | Template for evidence artifact tracking |
| `PACKAGE_MANIFEST_TEMPLATE.md` | Template for package manifest |
| `STALE_FILE_REGISTER_TEMPLATE.yaml` | Template for stale file tracking |

### State machine documentation

| File | Purpose |
|---|---|
| `STATE_MACHINE.md` | Master state list (initialization → terminal) |
| `STATE_SCHEMA.md` | CURRENT_STATE.yaml schema reference + validation rules |
| `TRANSITION_RULES.md` | All allowed state transitions |
| `STALE_FILE_POLICY.md` | Rules for HISTORICAL banners and stale file handling |
| `STATE_MACHINE_EXAMPLES.md` | Worked examples of gate runs |
| `ENFORCEMENT_EXAMPLES.md` | Examples for enforcement-authority audit |

### Scripts and self-tests

| File | Purpose |
|---|---|
| `SCRIPT_SPEC_check_gate_package.md` | Spec for automated gate package checker |
| `SELF_TEST_GATE_STATE_MACHINE.md` | 14 Q&A self-test confirming gate catches known failures |

### Existing known failure fixtures

| Fixture | Failure mode |
|---|---|
| `tests/gate_state_machine/fixtures/bad_local_path_package_listing/` | Package listing from local disk, not from exported zip |
| `tests/gate_state_machine/fixtures/bad_right_command_wrong_branch/` | Tests ran on wrong branch; context claim false |

### Existing reports

| Path | Contents |
|---|---|
| `reports/gate-state-machine-upgrade-2026-04-30/` | Prior upgrade sprint artifacts |
| `examples/known_failures/agentos-ng-governance-fixes/` | Real-world known failure package |

---

## Current state sequence (from STATE_MACHINE.md)

```
GATE_NOT_STARTED
  → CYCLE_TRACKER_INITIALIZED
  → EVIDENCE_ADEQUACY_IN_PROGRESS
      → EVIDENCE_ALREADY_ADEQUATE | EVIDENCE_UPGRADE_REQUIRED | EVIDENCE_BLOCKED_REQUIRES_HUMAN
  → TEST_PLAN_IN_PROGRESS → TEST_PLAN_COMPLETE  (if upgrade required)
  → EVIDENCE_CONSISTENCY_IN_PROGRESS
      → EVIDENCE_CONSISTENCY_PASS | EVIDENCE_CONSISTENCY_BLOCKED
  → ENFORCEMENT_AUDIT_NOT_APPLICABLE | ENFORCEMENT_AUDIT_IN_PROGRESS
      → ENFORCEMENT_AUDIT_PASS | ENFORCEMENT_AUDIT_FAIL_AUTOFIX | ENFORCEMENT_AUDIT_FAIL_BLOCKED
  → PANEL_ENTRY_VERIFIED
  → R1_IN_PROGRESS → R1_COMPLETE
  → R2_IN_PROGRESS → R2_COMPLETE
  → R3_IN_PROGRESS → R3_COMPLETE
  → R4_IN_PROGRESS → R4_COMPLETE
  → R5_IN_PROGRESS → R5_COMPLETE
  → GATE_VERDICT_ISSUED
      → GATE_PASS_FOR_HANDOFF | GATE_FAIL_AUTOFIX_REQUIRED | GATE_FAIL_BLOCKED_REQUIRES_HUMAN
  → FIX_CYCLE_IN_PROGRESS → FIX_CYCLE_COMPLETE  (if autofix)
  → FINAL_PACKAGE_AUDIT_IN_PROGRESS
      → FINAL_PACKAGE_AUDIT_PASS | FINAL_PACKAGE_AUDIT_FAIL
  → CANONICAL_HANDOFF_AUDIT_IN_PROGRESS
      → CANONICAL_HANDOFF_AUDIT_PASS | CANONICAL_HANDOFF_AUDIT_FAIL
  → EXECUTION_CONTEXT_AUDIT_IN_PROGRESS | EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE
      → EXECUTION_CONTEXT_AUDIT_PASS | EXECUTION_CONTEXT_AUDIT_FAIL
  → PASS_HANDOFF_COMPLETE | BLOCKED_HANDOFF_COMPLETE
```

---

## Current required reports/proof files (per gate run)

Every gate run must produce:
- `CURRENT_STATE.yaml`
- `CYCLE_TRACKER.md`
- `CLAIMS_LEDGER.yaml`
- `EVIDENCE_LEDGER.yaml`
- `STALE_FILE_REGISTER.yaml`
- `PACKAGE_MANIFEST.md`
- `EVIDENCE_ADEQUACY_ASSESSMENT.md`
- `EVIDENCE_CONSISTENCY_REGISTER.md`
- `COLD_REVIEW_REQUIREMENTS_AUDIT.md` (R1)
- `COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` (R2)
- `COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md` (R3)
- `COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md` (R4)
- `COLD_REVIEW_ADJUDICATION.md` (R5)
- `HANDOFF.md` (pass) or `BLOCKED_HANDOFF.md` (blocked)

Conditional:
- `ENFORCEMENT_AUTHORITY_AUDIT.md` — when enforcement/gating scope
- `TEST_AND_EVIDENCE_PLAN.md` — when EVIDENCE_UPGRADE_REQUIRED

---

## Gaps relative to Gate 4.1 upgrade

### Missing: Profile selection
No concept of GATE_LITE / GATE_STANDARD / GATE_FULL / GATE_FULL_PLUS_DOMAIN_ADDENDUM. Every task runs the same gate regardless of risk tier. Low-risk tasks pay the full overhead; high-risk tasks have no additional domain checks.

### Missing: Risk tier classification
No D0/D1/D2/D2-hot/D3/D4 taxonomy. No hot files list. No escalation triggers. The gate cannot route to the appropriate lane without this.

### Missing: Prompt contract review
No check for ambiguous terms, hidden assumptions, lifecycle timing ambiguity, forbidden interpretations, or overclaims in the task prompt itself before implementation begins.

### Missing: Artifact lifecycle timing audit
No check that artifacts were constructed at the correct lifecycle point (e.g., head_sha collected before writes, final package generated before final files existed).

### Missing: Production caller audit
No systematic check that claimed "live behavior" has an actual production caller. Infrastructure-ready code can be overclaimed as live-wired.

### Missing: Consumer API proof audit
No check that tests assert through the same API downstream code will use, rather than bypassing via raw DB/file inspection.

### Missing: Warning output contradiction audit
No requirement to scan raw outputs for warnings that contradict success claims.

### Missing: Required test set exactness
No check that the exact required test set was run, not just a broad pattern.

### Missing: Manifest finalization / stat / hash check
Manifest tracks file presence but not file sizes (stat) or hashes. A manifest could list 0-byte files or files that changed after listing.

### Missing: Migration runner proof
No check that SQL migrations were applied via the actual migration runner, not just manually.

### Missing: Implementer prompt lint
No check for invalid code snippets, impossible tests, or overclaiming in implementation prompts.

### Missing: Stranded helper / unused export scan
No check that new helpers, exports, or agents have production callers, not just test callers.

### Missing: Dirty worktree recurrence register
No mechanism to track when the same path dirties the repo repeatedly across tasks.

### Missing: Work allocation / hot file conflict audit
No check for multi-agent conflicts when multiple agents touch hot files simultaneously.

### Missing: Export channel audit
No systematic check that files existing on the execution host are actually included in exported packages.

### Missing: Diff base / scope audit
No check that diffs use the correct base/head and include only task scope.

### Missing: Flake / timeout / load sensitivity audit
No mechanism to flag tests that are known to be load-sensitive or flaky.

### Missing: Concurrency assumptions audit
No check for race conditions, missing locks, or non-idempotent operations in state/persistence/queue systems.

### Missing: Downstream consumer readiness audit
No gate before declaring a next phase ready.

### Missing: Next prompt decision artifact
No required artifact describing whether to continue/correct/split/defer the next step.

### Missing: CTO/operator insight review
No outer-frame operator lens for D2-hot/D3/D4 work.

### Missing: Overclaim taxonomy
Final handoff status is too coarse ("READY_FOR_HANDOFF"). No distinction between LIVE_BEHAVIOR_FIXED, INFRASTRUCTURE_READY_NOT_WIRED, TEST_HELPER_ONLY, DOCS_ONLY, etc.

### Missing: Gate effectiveness log
No mechanism to record what the gate caught, missed, or overcalled.

### Missing: Machine-readable proof file requirements by profile
No YAML that specifies exactly which proof files are required for each profile.

### Missing: Profile-aware terminal states
All passes end at PASS_HANDOFF_COMPLETE regardless of profile. No profile-specific terminal states.
