# Export Channel Audit

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## Export artifact

**Export type:** zip / directory / upload
**Export path:** [path or URL]
**Export generated at:** [ISO timestamp]
**Export generated after all required files existed:** YES / NO

---

## Required file table

| Required file | Execution host path | Exists on host? | Command | Included in export? | Proof |
|---|---|---|---|---|---|
| [file] | [host_path] | YES/NO | `ls -la [path]` | YES/NO | [zipinfo line or find output] |

---

## Files existing on host but missing from export

| File | Host path | Export checked by | Not found |
|---|---|---|---|
| [file] | [path] | `zipinfo -1 <zip>` | NOT FOUND |

**Total missing from export:** [count]

---

## Upload verification (if applicable)

**Upload method:** [scp / s3 / email / manual]
**Upload confirmation:** [receipt / transfer log / "not applicable"]
**All required files confirmed in upload:** YES / NO / N/A

---

## Verdict

```
EXPORT_CHANNEL_AUDIT_PASS | EXPORT_CHANNEL_AUDIT_FAIL
```

**Rationale:** [one paragraph]

**Fix required (if FAIL):** Regenerate export after ensuring all required files exist on host.
