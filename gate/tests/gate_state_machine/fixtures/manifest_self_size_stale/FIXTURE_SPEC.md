# Fixture: manifest_self_size_stale

## Setup

- `PACKAGE_MANIFEST.md` includes an entry for itself:
  ```
  | PACKAGE_MANIFEST.md | `task-001/PACKAGE_MANIFEST.md` | YES | [ ] |
  ```
- At the time the manifest was generated, it was 2,847 bytes
- After all entries were filled in (including its own entry), the manifest grew to 4,102 bytes
- `package_file_sizes.txt` (generated after the manifest was finalized) shows:
  ```
  4102 reports/task-001/PACKAGE_MANIFEST.md
  ```
- But the manifest's "Manifest generated at" timestamp is earlier than its own "size" entry
  was written — the manifest listed itself at a time when it was smaller
- Additionally: `MANIFEST_FINALIZATION_AUDIT.md` shows `manifest_self_size: 2847`
  but `stat` shows `4102` — a mismatch

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Manifest self-size is stale:
       MANIFEST_FINALIZATION_AUDIT.md claims PACKAGE_MANIFEST.md is 2847 bytes
       stat output shows: 4102 bytes
       Flag: MANIFEST_SELF_SIZE_STALE
       Invariant violated: manifest_self_size_matches_stat
[WARN] Package manifest was likely generated before being fully written:
       manifest_generated_at is earlier than final entry timestamp
       Final package_file_sizes.txt should be regenerated after manifest is finalized
```

## Expected invariant

`manifest_self_size_matches_stat`

## Why this matters

A manifest that lists itself at a stale size cannot verify its own integrity. If a reviewer
checks "does the manifest file have the size listed in the manifest?" the answer will be NO.
This also indicates the manifest was generated before all entries were complete — a lifecycle
timing violation that may affect other entries too.
