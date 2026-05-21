# Fixture: file_exists_on_host_missing_from_export

## Setup

- Task ran on VPS at `/home/claw/clawcodex/`
- Required file: `reports/task-001/raw_outputs/test_run.log`
- The file exists on the VPS: `ls -la /home/claw/clawcodex/reports/task-001/raw_outputs/test_run.log` shows 14,392 bytes
- Export zip was generated BEFORE the test run completed:
  `zip -r TASK_001_PACKAGE.zip reports/task-001/`
  was run at 14:32:05; the test completed and wrote `test_run.log` at 14:32:47
- `PACKAGE_MANIFEST.md` lists `test_run.log` as present (it was added to manifest after the test ran)
- `EXPORT_CHANNEL_AUDIT.md`:
  - `test_run.log` — Execution host path exists: YES — Included in export: YES (incorrect)
  - Proof: "exists at /home/claw/clawcodex/reports/task-001/raw_outputs/test_run.log"
    (this is a host path, not a zipinfo line — incorrect proof method)
- Actual `zipinfo -1 TASK_001_PACKAGE.zip` does NOT contain `test_run.log`

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Export channel audit: file exists on host but not in export
       File: reports/task-001/raw_outputs/test_run.log
       Host path: /home/claw/clawcodex/reports/task-001/raw_outputs/test_run.log — EXISTS
       In export zip: zipinfo -1 TASK_001_PACKAGE.zip | grep test_run.log — NOT FOUND
       EXPORT_CHANNEL_AUDIT.md used host path as proof instead of zipinfo output
       Invariant violated: required_file_in_export_not_just_on_host
[FAIL] EXPORT_CHANNEL_AUDIT.md proof method invalid:
       Proof given: "/home/claw/clawcodex/reports/..." (local host path)
       Required: zipinfo output from actual exported zip
```

## Expected invariant

`required_file_in_export_not_just_on_host`

## Why this matters

The file is real. It has 14,392 bytes on the VPS. But the reviewer receives a zip.
The zip does not contain the file. The reviewer cannot verify the test output.
The fix: regenerate the zip after all files exist, and prove inclusion with zipinfo.
