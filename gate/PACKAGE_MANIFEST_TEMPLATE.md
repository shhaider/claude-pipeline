# Package Manifest

**Task ID:** [task_id]
**Task area:** [task_area]
**Gate run ID:** [gate_run_id]
**Cycle:** [N]
**Manifest generated at:** [ISO timestamp]
**Manifest status:** DRAFT | VERIFIED

> A DRAFT manifest lists what SHOULD be in the package.
> A VERIFIED manifest has been checked by 15_FINAL_PACKAGE_AUDIT.md — every file physically confirmed present.
> Do not mark VERIFIED without running 15_FINAL_PACKAGE_AUDIT.md.

---

## Package contents

### Required gate artifacts

| File | Path in package | Physical path on disk | Present in package | Verified |
|---|---|---|---|---|
| CURRENT_STATE.yaml | `<task_area>/CURRENT_STATE.yaml` | `reports/<task_area>/CURRENT_STATE.yaml` | [ ] | [ ] |
| CYCLE_TRACKER.md | `<task_area>/CYCLE_TRACKER.md` | `reports/<task_area>/CYCLE_TRACKER.md` | [ ] | [ ] |
| CLAIMS_LEDGER.yaml | `<task_area>/CLAIMS_LEDGER.yaml` | `reports/<task_area>/CLAIMS_LEDGER.yaml` | [ ] | [ ] |
| EVIDENCE_LEDGER.yaml | `<task_area>/EVIDENCE_LEDGER.yaml` | `reports/<task_area>/EVIDENCE_LEDGER.yaml` | [ ] | [ ] |
| STALE_FILE_REGISTER.yaml | `<task_area>/STALE_FILE_REGISTER.yaml` | `reports/<task_area>/STALE_FILE_REGISTER.yaml` | [ ] | [ ] |
| EVIDENCE_ADEQUACY_ASSESSMENT.md | `<task_area>/EVIDENCE_ADEQUACY_ASSESSMENT.md` | `reports/<task_area>/EVIDENCE_ADEQUACY_ASSESSMENT.md` | [ ] | [ ] |
| EVIDENCE_CONSISTENCY_REGISTER.md | `<task_area>/EVIDENCE_CONSISTENCY_REGISTER.md` | `reports/<task_area>/EVIDENCE_CONSISTENCY_REGISTER.md` | [ ] | [ ] |
| COLD_REVIEW_REQUIREMENTS_AUDIT.md (final cycle) | `<task_area>/COLD_REVIEW_REQUIREMENTS_AUDIT.md` | `reports/<task_area>/COLD_REVIEW_REQUIREMENTS_AUDIT.md` | [ ] | [ ] |
| COLD_REVIEW_ACTIVE_PROOF_AUDIT.md (final cycle) | `<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` | `reports/<task_area>/COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` | [ ] | [ ] |
| COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md (final cycle) | `<task_area>/COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md` | `reports/<task_area>/COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md` | [ ] | [ ] |
| COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md (final cycle) | `<task_area>/COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md` | `reports/<task_area>/COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md` | [ ] | [ ] |
| COLD_REVIEW_ADJUDICATION.md (final cycle) | `<task_area>/COLD_REVIEW_ADJUDICATION.md` | `reports/<task_area>/COLD_REVIEW_ADJUDICATION.md` | [ ] | [ ] |

### Conditional gate artifacts

| File | Condition for inclusion | Present in package | Verified |
|---|---|---|---|
| ENFORCEMENT_AUTHORITY_AUDIT.md | If enforcement audit was applicable | [ ] | [ ] |
| TEST_AND_EVIDENCE_PLAN.md | If EVIDENCE_UPGRADE_REQUIRED in any cycle | [ ] | [ ] |

### Raw Test Outputs (Gate 5.1 — required section)

List every raw test output file. These files will be scanned for EXIT_CODE validation and post-PASS error detection.

| Artifact ID | File | artifact_type in ledger | EXIT_CODE:0 present? | POST_PASS errors? | Present in package |
|---|---|---|---|---|---|
| [E00N] | [filename] | raw_test_output | YES / NO | YES / NO | [ ] |

> If no raw test outputs exist: record "No raw test outputs — NOT_APPLICABLE" and produce `REQUIRED_TEST_SET_EXACTNESS_NOT_APPLICABLE.md`.

---

### Evidence artifacts

List every artifact registered in EVIDENCE_LEDGER.yaml that is meant to be in the package:

| Artifact ID | File | Path in package | Present | Verified |
|---|---|---|---|---|
| E001 | [filename] | [package path] | [ ] | [ ] |
| E002 | [filename] | [package path] | [ ] | [ ] |

### Implementation artifacts

| File | Path in package | Present | Verified |
|---|---|---|---|
| implementation.patch | `<task_area>/implementation.patch` | [ ] | [ ] |
| [changed files snapshots] | `<task_area>/snapshots/` | [ ] | [ ] |

### Handoff documents

| File | Status field | Expected status | Verified |
|---|---|---|---|
| HANDOFF.md | Readiness: [value] | READY | [ ] |
| BLOCKED_HANDOFF.md | (if present) Status banner | HISTORICAL | [ ] |

---

## Package verification commands

Run these to verify physical presence before marking VERIFIED:

```bash
# If zip:
zipinfo -1 <package_name>.zip | sort

# If directory:
find reports/<task_area>/ -type f | sort

# Cross-check against this manifest — every file in the manifest must appear in the output
```

---

### Gate 4.1 — Proof files by profile

**Gate profile for this run:** [GATE_LITE / GATE_STANDARD / GATE_FULL / GATE_FULL_PLUS_DOMAIN_ADDENDUM]

List all required proof files for the selected profile:

| Proof file | Required | Present | Verified |
|---|---|---|---|
| `GATE_PROFILE_SELECTION.md` | YES | [ ] | [ ] |
| `PROMPT_CONTRACT_REVIEW.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `PRODUCTION_CALLER_AUDIT.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `CONSUMER_API_PROOF_AUDIT.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `WARNING_OUTPUT_AUDIT.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `REQUIRED_TEST_SET_EXACTNESS.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `MANIFEST_FINALIZATION_AUDIT.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `package_file_sizes.txt` | [YES/NO] | [ ] | [ ] |
| `package_file_hashes.txt` | [YES/NO for FULL] | [ ] | [ ] |
| `STRANDED_HELPER_AUDIT.md` | [YES/NO/CONDITIONAL] | [ ] | [ ] |
| `EXPORT_CHANNEL_AUDIT.md` | [YES/NO] | [ ] | [ ] |
| `DIFF_BASE_SCOPE_AUDIT.md` | [YES/NO] | [ ] | [ ] |
| `NEXT_PROMPT_DECISION.md` | [YES/NO] | [ ] | [ ] |
| `CTO_OPERATOR_INSIGHT_REVIEW.md` | [YES/NO for FULL] | [ ] | [ ] |
| `GATE_EFFECTIVENESS_LOG.md` | [YES/NO for FULL] | [ ] | [ ] |
| `gate_used/` (gate source folder) | YES for FULL | [ ] | [ ] |

**NOT_APPLICABLE proof files (for states skipped in this profile):**

| State | NOT_APPLICABLE file | Present |
|---|---|---|
| [STATE_NAME] | `[STATE_NAME]_NOT_APPLICABLE.md` | [ ] |

---

### Gate 4.1 — Package integrity

| Item | Value | Verified |
|---|---|---|
| File sizes generated via `stat` | `package_file_sizes.txt` | [ ] |
| File hashes generated via `sha256sum` | `package_file_hashes.txt` | [ ] |
| Manifest self-size: stale or 0 bytes? | YES/NO | [ ] |
| All files > 0 bytes (non-placeholder) | YES/NO | [ ] |

---

## Manifest audit result

- **Total required files:** [N]
- **Present and verified:** [N]
- **Missing from package:** [N] — list: [...]
- **Local-path-only entries (non-portable):** [N] — list: [...]
- **NOT_APPLICABLE files present:** [N of N required]
- **Gate profile proof files complete:** YES / NO
- **Manifest status:** DRAFT | VERIFIED | FAILED

> A manifest is VERIFIED only when every file in it has been physically confirmed present in the package using `zipinfo` or `find` — not by reading its own contents.
