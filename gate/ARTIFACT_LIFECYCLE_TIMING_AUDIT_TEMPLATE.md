# Artifact Lifecycle Timing Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Purpose

Verifies that every evidence artifact was constructed at the correct lifecycle point. An artifact produced too early (before the relevant data existed) cannot prove what it claims to prove.

---

## Artifact timeline table

| Artifact | Purpose | When generated | Data available at that time? | Lifecycle correct? | Flag |
|---|---|---|---|---|---|
| `head_sha` capture | Record pre-task HEAD | [before/after writes] | YES/NO | YES/NO | [flag or OK] |
| Final package / zip | Export all required files | [before/after all writes] | YES/NO | YES/NO | [flag or OK] |
| Package manifest | List all package files | [before/after package created] | YES/NO | YES/NO | [flag or OK] |
| Handoff validation | Validate package completeness | [before/after tests complete] | YES/NO | YES/NO | [flag or OK] |
| Raw test output | Capture test run | [before/after relevant code] | YES/NO | YES/NO | [flag or OK] |
| Migration applied | DB schema change | [before/after dependent code] | YES/NO | YES/NO | [flag or OK] |
| Snapshot | Changed file content | [before/after final write] | YES/NO | YES/NO | [flag or OK] |
| Diff | Code changes | [against correct base] | YES/NO | YES/NO | [flag or OK] |

---

## Timing violation flags

### HEAD_SHA_TIMING_VIOLATION

`head_sha` was collected after writes or commits were made. The captured SHA reflects post-task state, not pre-task state.

Found: YES / NO

If YES — artifact: [path] — collected at: [point] — required: before any task writes

---

### PACKAGE_GENERATED_EARLY

The package/manifest was generated before all export files existed. Some files may be absent or listed with 0 bytes.

Found: YES / NO

If YES — artifact: [path] — generated at: [point] — missing files at that time: [list]

---

### HANDOFF_VALIDATED_EARLY

The handoff was validated before all tests completed or before all artifacts were finalized. Validation is based on incomplete evidence.

Found: YES / NO

If YES — artifact: [path] — validated at: [point] — pending items at that time: [list]

---

### FINAL_PATH_MEMORY_ONLY

A "final" artifact path was only kept in-session memory during the run. If the task required persistence (export, upload, zip), the artifact may be lost if the session ended before persistence occurred.

Found: YES / NO

If YES — artifact: [description] — persistence step: [did it happen? YES/NO]

---

## Verdict

| Violation | Found | Blocking? |
|---|---|---|
| HEAD_SHA_TIMING_VIOLATION | YES/NO | YES/NO |
| PACKAGE_GENERATED_EARLY | YES/NO | YES/NO |
| HANDOFF_VALIDATED_EARLY | YES/NO | YES/NO |
| FINAL_PATH_MEMORY_ONLY | YES/NO | YES/NO |

**Total blocking violations:** [count]

**Verdict:** LIFECYCLE_TIMING_PASS | LIFECYCLE_TIMING_BLOCKING
