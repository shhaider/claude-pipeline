# Manifest Finalization / Stat / Hash Check

**Task ID:** [task_id]
**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]

---

## File size check

**Command:**
```bash
find <export-root> -type f -print0 | sort -z | xargs -0 stat -c '%s %n'
```

**Output file:** `reports/<task_area>/package_file_sizes.txt`

**Files with size 0 bytes (non-placeholder):**
- [file path] — 0 bytes — BLOCKER unless intentionally empty

**Self-size check for manifest:**

| Manifest file | Size at time of listing | Final size (from stat) | Match? | Flag |
|---|---|---|---|---|
| [manifest_path] | [bytes] | [bytes] | YES/NO | OK / MANIFEST_SELF_SIZE_STALE |

---

## Hash generation

**Command:**
```bash
find <export-root> -type f -print0 | sort -z | xargs -0 sha256sum
```

**Output file:** `reports/<task_area>/package_file_hashes.txt`

**Hash file included in package:** YES / NO

---

## Manifest vs stat reconciliation

| File (from manifest) | Manifest size claim | Stat size | Match? | Verdict |
|---|---|---|---|---|
| [file] | [size] | [size] | YES/NO | OK / SIZE_MISMATCH |

---

## Findings

| Check | Result | Blocking? |
|---|---|---|
| Files with 0 bytes | [count] | YES/NO |
| Manifest self-size stale | YES/NO | YES/NO |
| Stat/manifest size mismatches | [count] | YES/NO |
| Hash file generated | YES/NO | YES (for GATE_FULL) |

**Total blocking findings:** [count]

---

## Verdict

```
MANIFEST_FINALIZATION_PASS | MANIFEST_FINALIZATION_FAIL
```

**Rationale:** [one paragraph]
