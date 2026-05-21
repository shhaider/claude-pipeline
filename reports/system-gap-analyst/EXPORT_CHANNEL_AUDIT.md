# Export Channel Audit

**Cycle:** 1
**Verdict:** PASS

---

## Mandate

Verify that every file the gate package claims to export is reachable via the declared channel (in-repo path under `reports/system-gap-analyst/`), and that no claimed file is reachable only via a host-only or non-portable path.

---

## Channels

| Channel | Reachable from | Files routed through this channel |
|---|---|---|
| In-repo `reports/system-gap-analyst/` | `git ls-files reports/system-gap-analyst/` after gate-package commit | All required GATE_STANDARD proof files plus 4 NOT_APPLICABLE proofs |
| In-repo `src/` and `tests/` | `git ls-files` | Source and test evidence |
| In-repo `prompts/metabuilder/` | `git ls-files` | New system prompt |
| Host-only paths | n/a | NONE — no artifact in the ledger is host-only. |

---

## Per-file routing table

| File | Channel | Reachable | Notes |
|---|---|---|---|
| `reports/system-gap-analyst/CURRENT_STATE.yaml` | In-repo | YES | Tracked in commit. |
| `reports/system-gap-analyst/CYCLE_TRACKER.md` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/CLAIMS_LEDGER.yaml` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/EVIDENCE_LEDGER.yaml` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/STALE_FILE_REGISTER.yaml` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/PACKAGE_MANIFEST.md` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/GATE_PROFILE_SELECTION.md` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/raw/pytest.log` | In-repo | YES | Tracked; pure ASCII log. |
| `reports/system-gap-analyst/git_status_final.txt` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/HANDOFF.md` | In-repo | YES | Tracked. |
| `reports/system-gap-analyst/gate_hash.txt` | In-repo | YES | Gate source proof. |

No host-only paths are referenced. `EVIDENCE_LEDGER.yaml` records `package_relative_path` for every entry, and `cwd` is the implementer's local working dir only for provenance — no claim depends on host-path resolution.

---

## Findings

- **Blocking:** none
- **Non-blocking:** none

## Verdict

PASS.
