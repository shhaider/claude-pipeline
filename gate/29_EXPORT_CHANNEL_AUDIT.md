# Step 29 — Export Channel Audit

**State machine:** Write `current_state: EXPORT_CHANNEL_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_STANDARD and GATE_FULL** when the package is expected to be exported (zipped, uploaded, transferred to another system, or reviewed by a human off the execution host).

**Skip for GATE_LITE.** Produce `EXPORT_CHANNEL_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

"The file exists on the VPS" is not the same as "the file is included in the exported package." This audit explicitly verifies that every file required by the reviewer or the next phase is physically present in the export artifact — not just on the execution host.

A concrete failure: a raw test output file exists at `/home/claw/clawcodex/reports/task-001/raw_output.txt` on the VPS. The manifest lists it. But the zip sent to the reviewer was generated before this file existed. The reviewer receives a zip without the file. The file "exists" — but the reviewer cannot see it.

---

## Output file

Copy `EXPORT_CHANNEL_AUDIT_TEMPLATE.md` to `reports/<task_area>/EXPORT_CHANNEL_AUDIT.md`.

Also update `reports/<task_area>/15_FINAL_PACKAGE_AUDIT.md` (append the export channel verification table).

---

## Required table

| Required file | Execution host path exists? | Included in export? | Included in uploaded package? | Proof |
|---|---|---|---|---|
| [file] | YES / NO | YES / NO | YES / NO | [zipinfo line / upload confirmation] |

---

## Checks

### Check 1 — Identify all required files

List every file that the reviewer, next-phase implementer, or human decision-maker needs:
- All files listed in PACKAGE_MANIFEST.md
- All raw output files
- The gate source folder (`gate_used/`) if required
- All diff and snapshot files
- The manifest itself

### Check 2 — Verify presence on execution host

For each required file:
```bash
ls -la [file_path]
```

If the file does not exist on the execution host: `MISSING_ON_HOST` — this is a blocker.

### Check 3 — Verify inclusion in export artifact

For each required file:
- If package is a zip: `zipinfo -1 <package>.zip | grep [filename]`
- If package is a directory: `find <export_dir> -name [filename]`

If the file is on the host but absent from the export: `EXISTS_ON_HOST_MISSING_FROM_EXPORT` — this is a blocker.

### Check 4 — Verify uploaded package (if applicable)

If the package was uploaded or transferred:
1. Verify the upload confirmation includes the expected file
2. If the reviewer is on a different host, verify they received the file

---

## Hard rule

"Exists on VPS" is **not sufficient** if the reviewer receives a zip. The zip must contain the file. The proof must be a `zipinfo -1` line from the actual zip, not a local disk listing.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| All required files present in export | `EXPORT_CHANNEL_AUDIT_PASS` | Continue |
| Any file exists on host but missing from export | `EXPORT_CHANNEL_AUDIT_FAIL` | `FIX_CYCLE_IN_PROGRESS` (regenerate export) |
