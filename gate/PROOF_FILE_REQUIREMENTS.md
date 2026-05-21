# Proof File Requirements — Gate 5.2

This file defines which proof files are required for each gate profile. Every required state must produce a proof file. Every NOT_APPLICABLE state must produce a `STATE_NAME_NOT_APPLICABLE.md` file.

## Exact-path rule

Each required proof file in `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` must exist at its exact exported relative path after `{task_area}` substitution. A correct basename in the wrong folder does not count.

---

## Rule: every required state produces a proof file

When a state is required for the selected gate profile, the agent must produce a corresponding proof file before the state can be written as complete. Proof files are named after the state or the step number.

When a state is NOT APPLICABLE for the selected gate profile, the agent must produce a `STATE_NAME_NOT_APPLICABLE.md` file with a one-sentence justification. The final package must include all NOT_APPLICABLE proof files.

---

## Core proof files (required for all profiles)

| State | Proof file |
|---|---|
| `GATE_PROFILE_SELECTION_COMPLETE` | `reports/<task_area>/GATE_PROFILE_SELECTION.md` |
| `CYCLE_TRACKER_INITIALIZED` | `reports/<task_area>/CYCLE_TRACKER.md`, `CLAIMS_LEDGER.yaml`, `EVIDENCE_LEDGER.yaml`, `STALE_FILE_REGISTER.yaml` |
| `EVIDENCE_ADEQUACY_*` | `reports/<task_area>/EVIDENCE_ADEQUACY_ASSESSMENT.md` |
| `TEST_PLAN_COMPLETE` | `reports/<task_area>/TEST_AND_EVIDENCE_PLAN.md` |
| `EVIDENCE_CONSISTENCY_PASS` | `reports/<task_area>/EVIDENCE_CONSISTENCY_REGISTER.md` |
| `PANEL_ENTRY_VERIFIED` | Written to CYCLE_TRACKER.md |
| `R1_COMPLETE` | `reports/<task_area>/COLD_REVIEW_REQUIREMENTS_AUDIT.md` |
| `R2_COMPLETE` | `reports/<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` |
| `R3_COMPLETE` | `reports/<task_area>/COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md` |
| `R4_COMPLETE` | `reports/<task_area>/COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md` |
| `R5_COMPLETE` | `reports/<task_area>/COLD_REVIEW_ADJUDICATION.md` |
| `GATE_VERDICT_ISSUED` | Written to CURRENT_STATE.yaml + CYCLE_TRACKER.md |
| `FINAL_PACKAGE_AUDIT_PASS` | PACKAGE_MANIFEST.md updated to VERIFIED |
| `CANONICAL_HANDOFF_AUDIT_PASS` | Written to CURRENT_STATE.yaml |
| `EXECUTION_CONTEXT_AUDIT_PASS` | Written to CURRENT_STATE.yaml |

---

## Gate 4.1 additional proof files

| State | Proof file | Required for profiles |
|---|---|---|
| `PROMPT_CONTRACT_PASS` | `reports/<task_area>/PROMPT_CONTRACT_REVIEW.md` | GATE_FULL, GATE_FULL_PLUS |
| `PRODUCTION_CALLER_AUDIT_PASS` | `reports/<task_area>/PRODUCTION_CALLER_AUDIT.md` | GATE_STANDARD, GATE_FULL |
| `CONSUMER_API_PROOF_AUDIT_PASS` | `reports/<task_area>/CONSUMER_API_PROOF_AUDIT.md` | GATE_STANDARD, GATE_FULL |
| `WARNING_OUTPUT_AUDIT_PASS` | `reports/<task_area>/WARNING_OUTPUT_AUDIT.md` | GATE_STANDARD, GATE_FULL |
| `REQUIRED_TEST_SET_EXACTNESS_PASS` | `reports/<task_area>/REQUIRED_TEST_SET_EXACTNESS.md` | GATE_STANDARD, GATE_FULL |
| `MANIFEST_FINALIZATION_PASS` | `reports/<task_area>/MANIFEST_FINALIZATION_AUDIT.md` + `package_file_sizes.txt` + `package_file_hashes.txt` | GATE_STANDARD, GATE_FULL |
| `MIGRATION_RUNNER_PROVEN` | `reports/<task_area>/MIGRATION_RUNNER_PROOF.md` | All profiles when migration present |
| `IMPLEMENTER_PROMPT_LINT_PASS` | `reports/<task_area>/IMPLEMENTER_PROMPT_LINT.md` | GATE_FULL when prompts present |
| `STRANDED_HELPER_AUDIT_PASS` | `reports/<task_area>/STRANDED_HELPER_AUDIT.md` | GATE_STANDARD, GATE_FULL |
| `DIRTY_WORKTREE_RECURRENCE_AUDIT_PASS` | `reports/<task_area>/DIRTY_WORKTREE_RECURRENCE.md` | GATE_FULL |
| `WORK_ALLOCATION_CLEAR` | `reports/<task_area>/WORK_ALLOCATION_AUDIT.md` | GATE_FULL when multi-agent |
| `EXPORT_CHANNEL_AUDIT_PASS` | `reports/<task_area>/EXPORT_CHANNEL_AUDIT.md` | GATE_STANDARD, GATE_FULL |
| `DIFF_BASE_SCOPE_AUDIT_PASS` | `reports/<task_area>/DIFF_BASE_SCOPE_AUDIT.md` | GATE_STANDARD, GATE_FULL |
| `TEST_STABILITY_OK` | `reports/<task_area>/FLAKE_TIMEOUT_AUDIT.md` | GATE_FULL |
| `CONCURRENCY_ASSUMPTIONS_AUDIT_PASS` | `reports/<task_area>/CONCURRENCY_ASSUMPTIONS_AUDIT.md` | GATE_FULL when state/queue |
| `DOWNSTREAM_READY` | `reports/<task_area>/DOWNSTREAM_CONSUMER_READINESS.md` | GATE_FULL |
| `NEXT_PROMPT_DECISION_COMPLETE` | `reports/<task_area>/NEXT_PROMPT_DECISION.md` | GATE_STANDARD, GATE_FULL |
| `CTO_OPERATOR_INSIGHT_REVIEW_COMPLETE` | `reports/<task_area>/CTO_OPERATOR_INSIGHT_REVIEW.md` | GATE_FULL |
| `GATE_EFFECTIVENESS_LOG_COMPLETE` | `reports/<task_area>/GATE_EFFECTIVENESS_LOG.md` | GATE_FULL |

---

## NOT_APPLICABLE proof files

When a state is not applicable for the selected profile, produce:
- File: `reports/<task_area>/[STATE_NAME]_NOT_APPLICABLE.md`
- Content: "State [STATE_NAME] is not applicable for this gate run. Profile: [GATE_PROFILE]. Reason: [one sentence]."

Example:
```
File: reports/my-task/PROMPT_CONTRACT_REVIEW_NOT_APPLICABLE.md
Content: State PROMPT_CONTRACT_REVIEW is not applicable for this gate run. Profile: GATE_LITE. Reason: Task is a documentation-only change (D0) and does not require prompt contract review.
```

---

## NOT_APPLICABLE Proof Hard Requirement (Gate 5.2-R1)

Under Gate 5.2-R1 the `not_applicable_proof_required` list in
`REQUIRED_PROOF_FILES_BY_PROFILE.yaml` is no longer advisory. Every state listed for the
selected profile must:

1. Have an exact file at `reports/<task_area>/<STATE_NAME>_NOT_APPLICABLE.md`.
2. Be non-empty.
3. Contain a substantive reason — either an NA keyword (e.g. "because", "audit-only task",
   "no tests run", "no migration", "no concurrent state", "no consumer api") OR more than
   80 characters of non-template prose.

Failure modes the checker now blocks:

| Condition | Flag |
|---|---|
| Required `_NOT_APPLICABLE.md` is missing | `MISSING_NOT_APPLICABLE_PROOF` |
| File present but empty | `NOT_APPLICABLE_REASON_MISSING` |
| File present but body is only a heading or template placeholders | `NOT_APPLICABLE_REASON_MISSING` |

If a state is genuinely impossible to NA-prove for a profile (because the state always
applies), it should be **removed** from `not_applicable_proof_required` rather than left as
a listed-but-unenforced entry. The Gate 5.2-R1 GATE_LITE list is trimmed accordingly.

---

## Gate source folder

For every gate run, include the gate source files used. This prevents the reviewer from disagreeing about which version of the gate was active.

Place a copy or a reference under: `reports/<task_area>/gate_used/`

Required to include: `00_START.md`, `STATE_MACHINE.md`, `GATE_PROFILES.md`, `GATE_PROFILE_SELECTOR.md`, `TRANSITION_RULES.md`

If the full gate folder is too large to include, include a hash of the gate folder and the gate version string.

**A local path such as `/Users/.../gate` is NOT proof that gate source was consulted. Include either:**
- `gate_used/` — a copy of the gate folder used, OR
- `gate_hash.txt` — SHA256 of the gate folder contents plus gate version string

---

## FINAL_PACKET_AUDITOR_REPORT.md (Gate 5.3)

**Path:** `reports/{task_area}/FINAL_PACKET_AUDITOR_REPORT.md`

**Required for:** GATE_STANDARD, GATE_FULL, GATE_FULL_PLUS_DOMAIN_ADDENDUM, and GATE_LITE export/signout packages.

**Required schema (all five fields, in this order):**
- `FINAL_PACKET_AUDITOR_VERDICT:` followed by `PASS` / `FAIL` / `HUMAN_DECISION_REQUIRED`
- `REASON:` followed by concise explanation
- `BLOCKERS:` followed by a list (or `[]`)
- `REQUIRED_FIX:` followed by what must be fixed (or `NONE`)
- `RERUN_FROM:` followed by `BEGINNING` / `TARGETED_STATE:<state name>` / `HUMAN_DECISION`

**Final package CANNOT pass if:**
- file is missing
- verdict is FAIL
- verdict is HUMAN_DECISION_REQUIRED but final status claims ready/merged/verified
- RERUN_FROM is missing
- any of the five fields is absent (schema invalid)

**Independence:** The auditor must be a fresh subagent / fresh session / fresh model when possible; for GATE_FULL and stronger, use a Tier 3 / high-effort model. If independence cannot be achieved, the report must explicitly say so.

See state file `37_FINAL_PACKET_AUDITOR.md` and template `FINAL_PACKET_AUDITOR_REPORT_TEMPLATE.md`.

---

## Proof File Export Requirement (Gate 5.1)

**Every required proof file produced by the gate must be physically included in the final exported package.**

A file that exists on the execution host but is absent from the exported zip/directory is NOT acceptable as proof.

The final package MUST include:
- `GATE_PROFILE_SELECTION.md`
- `CURRENT_STATE.yaml`
- `CYCLE_TRACKER.md`
- All ledgers: `CLAIMS_LEDGER.yaml`, `EVIDENCE_LEDGER.yaml`, `STALE_FILE_REGISTER.yaml`
- All required audit proof files for the selected profile (per `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`)
- All NOT_APPLICABLE proof files
- All raw test outputs (all files marked `artifact_type: raw_test_output` in manifest/ledger)
- `WARNING_OUTPUT_AUDIT.md` (if raw outputs present; NOT_APPLICABLE file if none)
- `REQUIRED_TEST_SET_EXACTNESS.md` (if raw outputs present; NOT_APPLICABLE file if none)
- `package_file_sizes.txt`
- `package_file_hashes.txt` (Gate Full)
- `GATE_PACKAGE_VALIDATION_REPORT.md` (Gate Full — produced by checker after first run)
- `HANDOFF.md` (final handoff)
- A file containing `git status --short` output (may be in EVIDENCE_CONSISTENCY_REGISTER.md, CYCLE_TRACKER.md, or a standalone file)
- `gate_used/` directory OR `gate_hash.txt`

If any mandatory item is absent from the package: BLOCKING. Not a warning.

The checker script `tools/check_gate_package.py` enforces this mechanically for Gate Full.
