# Step 15 — Final Package Audit

> **Gate 5.3 ordering note:** This step runs BEFORE the Final Packet Auditor (state 37, file `37_FINAL_PACKET_AUDITOR.md`). Final Packet Auditor sits AFTER state 16 (Canonical Handoff Audit) and is independent of this step's mechanical pass.

## Gate 5.4 final checker barrier

Before final PASS, the package must pass:

```bash
python3 tools/check_gate_package.py --package <package> --task-area <task_area> --profile <profile> --risk-tier <risk> --task-kind <kind> --final
```

If `--final` exits nonzero, PASS is blocked.

You are here because Reviewer 5 returned `READY_FOR_REVIEW`, the gate returned `GATE_PASS_FOR_HANDOFF`, and `CURRENT_STATE.yaml` is now in state `FINAL_PACKAGE_AUDIT_IN_PROGRESS`.

This step runs **before** `12_PASS_HANDOFF.md`. A gate pass is not allowed until this audit completes with verdict PASS.

**This step exists because of a concrete failure:** A governance-fixes packet claimed PASS, but the zip did not contain the e2e_v2 files it claimed to contain, MANIFEST.md referenced local-machine-only paths, and HANDOFF.md said PENDING while CYCLE3_GATE_VERDICT.md said PASS. This audit would have caught all three failures before the handoff was issued.

---

## What this step does

1. Reads PACKAGE_MANIFEST.md
2. Physically verifies every file listed in the manifest is present in the package
3. Reads CLAIMS_LEDGER.yaml and verifies every HARD_FACT claim has an artifact that is present in the package and whose content supports the claim
4. Reads EVIDENCE_LEDGER.yaml and verifies every artifact marked `included_in_package: YES` is actually present
5. Checks all file paths in manifests and handoffs are portable (not local-machine-only)
6. Checks for SHA/HEAD claim consistency across all documents

---

## Step 1 — Write CURRENT_STATE.yaml

Write to `reports/<task_area>/CURRENT_STATE.yaml`:
```yaml
current_state: FINAL_PACKAGE_AUDIT_IN_PROGRESS
```

---

## Step 2 — Determine the package location

What form is the package in?

- If a zip file: run `zipinfo -1 <package>.zip | sort > /tmp/package_contents.txt`
- If a directory: run `find reports/<task_area>/ -type f | sort > /tmp/package_contents.txt`

Save the output. This is the ground truth for what is physically present.

---

## Step 3 — Manifest audit

Open `reports/<task_area>/PACKAGE_MANIFEST.md`.

For every file listed in the manifest:

1. Check if it appears in `/tmp/package_contents.txt`
2. If YES: mark `Present: YES, Verified: YES`
3. If NO: mark `Present: NO, Verified: NO` — this is a **blocker**
4. Check if the path is a portable path (not starting with `/Users/`, `/home/`, `/tmp/`, `C:\` or similar local-machine prefixes)
   - If local-machine-only path: mark as `LOCAL_PATH_ONLY` — this is a **blocker**
5. For any artifact claimed to be generated from an uploaded/exported package (PACKAGE_FILE_LISTING.txt, zipinfo output, etc.): verify the artifact was generated via `zipinfo -1 <package>` or `tar -tzf <package>`, not by listing local disk files. Any listing containing absolute local paths (`/Users/...`, `/home/...`) fails this check — **blocker**.

Update PACKAGE_MANIFEST.md with verification results. Change manifest status from DRAFT to VERIFIED (if all pass) or FAILED (if any fail).

---

## Step 4 — Claims ledger audit

Open `reports/<task_area>/CLAIMS_LEDGER.yaml`.

For every claim with `claim_type: HARD_FACT`:

1. Find the `evidence_artifact_path`
2. Check if the artifact is present on disk (`exists_on_disk`)
3. Check if the artifact is present in the package (look in `/tmp/package_contents.txt`)
4. If artifact missing from disk: `verification_result: SOURCE_MISSING` — **blocker**
5. If artifact missing from package: `verification_result: NOT_IN_PACKAGE` — **blocker**
6. If artifact path is local-machine-only: `verification_result: LOCAL_PATH_ONLY` — **blocker**
7. Read the artifact content (or a relevant excerpt). Does the content support the claim?
   - YES: `verification_result: VERIFIED`, `hard_fact_verified: true`
   - NO: `verification_result: SOURCE_CONTRADICTS`, `hard_fact_verified: false` — **blocker**
   - Artifact exists but doesn't address the claim: `verification_result: SOURCE_SILENT` — **warning** (not a blocker unless it's the only evidence for a critical claim)

Update each claim entry in CLAIMS_LEDGER.yaml with verification results.
Update the summary block.

---

## Step 5 — Evidence ledger audit

Open `reports/<task_area>/EVIDENCE_LEDGER.yaml`.

For every artifact with `included_in_package: YES`:

1. Check if it appears in `/tmp/package_contents.txt`
2. If NOT present: `verified_in_package: false` — **blocker**
3. If present: `verified_in_package: true`

Update EVIDENCE_LEDGER.yaml summary block.

---

## Step 6 — SHA and HEAD consistency check

For every document in the package that makes a SHA or HEAD claim (HANDOFF.md, CYCLE_TRACKER.md, EVIDENCE_ADEQUACY_ASSESSMENT.md, COLD_REVIEW_ADJUDICATION.md, etc.):

1. Extract the claimed SHA/HEAD
2. Check all documents claim the same SHA/HEAD for the same concept
3. If any document claims a different SHA: record as **blocker** with the contradicting documents named

---

## Step 7 — Handoff status pre-check

Before running the canonical handoff audit:

1. Open HANDOFF.md. Find the "Final readiness status" field. It must say `READY_FOR_HANDOFF` or equivalent — NOT `PENDING`, `IN_PROGRESS`, or `BLOCKED`.
   - If PENDING or similar: **blocker** — do not proceed to 12_PASS_HANDOFF.md
2. Check if BLOCKED_HANDOFF.md exists in the package
   - If yes: it must have the HISTORICAL banner (see STALE_FILE_POLICY.md)
   - If no banner: **blocker**

---

## Step 8 — Compile audit results

### Blockers

List every blocker found:

```
BLOCKER: [description]
Source: [which check above]
Evidence: [exact file/path/output]
Fix required: [what must change]
```

### Warnings

List every warning:

```
WARNING: [description]
Source: [which check above]
```

---

## Step 9 — Verdict and routing

### If zero blockers

Update CURRENT_STATE.yaml:
```yaml
current_state: FINAL_PACKAGE_AUDIT_PASS
final_package_audit_result: PASS
```

Update PACKAGE_MANIFEST.md status to `VERIFIED`.
Update CLAIMS_LEDGER.yaml `audit_verdict: PASS`.
Update EVIDENCE_LEDGER.yaml `audit_verdict: PASS`.

Route to: `16_CANONICAL_HANDOFF_AUDIT.md`

### If one or more blockers

**Do not route to 12_PASS_HANDOFF.md.**

Update CURRENT_STATE.yaml:
```yaml
current_state: FINAL_PACKAGE_AUDIT_FAIL
final_package_audit_result: FAIL
```

Fix each blocker (within scope):
- Missing file in package → add it to the package
- Local path in manifest → replace with portable relative path
- SOURCE_CONTRADICTS claim → fix the claim or regenerate the artifact
- HANDOFF.md PENDING → update to READY
- BLOCKED_HANDOFF.md missing banner → add the HISTORICAL banner

After fixing all blockers:
- Regenerate PACKAGE_MANIFEST.md
- Re-run this step (Step 15) from Step 2

**If a blocker cannot be fixed within scope:**
Update CURRENT_STATE.yaml to `GATE_FAIL_BLOCKED_REQUIRES_HUMAN` and route to `13_BLOCKED_HANDOFF.md`.

---

## Routing summary

| Outcome | Next file |
|---|---|
| Zero blockers | `16_CANONICAL_HANDOFF_AUDIT.md` |
| Blockers fixed within scope | Re-run `15_FINAL_PACKAGE_AUDIT.md` from Step 2 |
| Blocker cannot be fixed | `13_BLOCKED_HANDOFF.md` |

---

## Gate 4.1 — Manifest Finalization / Stat / Hash Check (append)

This section is required for GATE_STANDARD and GATE_FULL profiles.

### Step A — Generate file sizes using stat

Run:
```bash
find <export-root> -type f -print0 | sort -z | xargs -0 stat -c '%s %n'
```

Save output to `reports/<task_area>/package_file_sizes.txt`.

Verify:
- No file listed in the manifest has size 0 bytes (except explicitly empty placeholder files)
- The manifest file itself does not list its own size as 0 bytes (self-referential size problem)
- File sizes match between `stat` output and any size claims in the manifest

If the manifest was generated before some files were written, their sizes will be 0 or stale. This is a **blocker**.

Gate 5.2 also requires:
- exact required-proof-file paths, not basename matches elsewhere
- exported proof files to be present inside the package
- dirty git status proof to be clean or fully classified as unrelated external work

### Step B — Generate hashes

Run:
```bash
find <export-root> -type f -print0 | sort -z | xargs -0 sha256sum
```

Save output to `reports/<task_area>/package_file_hashes.txt`.

Include this hash file in the package manifest under "Package integrity verification."

### Step C — Self-size check

Open the manifest file. Find the entry for the manifest file itself (if listed).

If the manifest lists itself:
- Its size at listing time was almost certainly smaller than its final size (because it was written before the self-referential entry was added)
- Flag: `MANIFEST_SELF_SIZE_STALE` — list manifest with `stat` size and reconcile

### Manifest finalization blockers

| Check | Blocker? |
|---|---|
| Any file listed as 0 bytes | YES (unless explicitly empty placeholder) |
| Manifest self-size is stale or 0 | YES |
| File sizes do not match between stat output and manifest claims | YES |
| Hash file not generated | YES (for GATE_FULL) |

---

## Gate 4.1 — Warning Output Findings (append)

If `22_WARNING_OUTPUT_AUDIT.md` was run, append its blocking findings here:

| Warning | File | Line | Contradicts | Blocking? |
|---|---|---|---|---|
| [warning text] | [file] | [line] | [claimed behavior] | YES / NO |

If no blocking warnings: "No blocking warnings found in raw output scan."

---

## Gate 5.1 — Raw Output Discovery (Manifest-Driven)

The package audit must NOT limit raw output discovery to directories named `raw/` or `raw_outputs/`.

Required steps:
1. Scan EVIDENCE_LEDGER.yaml for all entries with `artifact_type: raw_test_output`
2. Scan PACKAGE_MANIFEST.md "Raw Test Outputs" section (if present)
3. The union of these two sources is the complete list of raw test outputs to audit
4. For each listed raw output: verify it is physically present in the package
5. If any listed raw output is absent from package: BLOCKING
6. If any file in the package appears to be a raw test output (contains `EXIT_CODE:` or `Tests:` lines) but is NOT listed in manifest/ledger: BLOCKING for GATE_FULL, WARNING for GATE_STANDARD

---

## Gate 5.1 — Required Proof Files Export Check

Every required proof file for the selected profile MUST be physically included in the exported package. A file that exists on the execution host but is absent from the package zip/directory is NOT acceptable.

Mandatory package contents:
- `GATE_PROFILE_SELECTION.md`
- `CURRENT_STATE.yaml`
- `CYCLE_TRACKER.md`
- All ledgers (`CLAIMS_LEDGER.yaml`, `EVIDENCE_LEDGER.yaml`, `STALE_FILE_REGISTER.yaml`)
- All required audit proof files for the selected profile
- All NOT_APPLICABLE proof files
- All raw test outputs (registered in manifest/ledger)
- `WARNING_OUTPUT_AUDIT.md` (if raw outputs present)
- `REQUIRED_TEST_SET_EXACTNESS.md` (if raw outputs present)
- `package_file_sizes.txt`
- `package_file_hashes.txt` (Gate Full)
- `GATE_PACKAGE_VALIDATION_REPORT.md` (Gate Full — produced by checker, included after first run)
- Final handoff (`HANDOFF.md`)
- Final git status proof file (any file containing `git status --short` output)
- `gate_used/` directory OR `gate_hash.txt`

**A local path such as `/Users/.../gate` is NOT proof that gate source was consulted.** Include either:
- `gate_used/` — a copy of the gate folder at time of use, OR
- `gate_hash.txt` — SHA256 of the gate folder contents plus gate version string

If any mandatory item is absent: BLOCKING (not a warning).

---

## Gate 5.1 — Pre-PASS Barrier Check

Before routing to FINAL_PACKAGE_AUDIT_PASS, verify all the following. If any is unchecked, route to FINAL_PACKAGE_AUDIT_FAIL:

```
[ ] All required states for selected profile are present in CURRENT_STATE.yaml
[ ] No required state is recorded as FAIL/BLOCKING/UNCERTAIN
[ ] No required state is missing from CURRENT_STATE.yaml
[ ] No required state is NOT_APPLICABLE without a documented reason
[ ] EXIT_CODE validation: no EXIT_CODE_MISSING/BLANK/NONZERO/CONFLICTING flags in any raw output
[ ] Post-PASS error check: no POST_PASS_UNCAUGHT_ERROR flags in any raw output
[ ] check_gate_package.py exits 0 (required for Gate Full; recommended for Gate Standard)
[ ] GATE_PACKAGE_VALIDATION_REPORT.md included in package (Gate Full — skip on first run to avoid circular dependency)
```

---

## Gate 5.2-R1 — Output-Contract structured verdict (append)

`OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` SHOULD include a fenced YAML block declaring the
audit verdict in machine-readable form. The Gate 5.2-R1 checker prefers the structured
block to avoid prose-scan false positives like "no STALE_MILESTONE_LABEL".

Required structured block format:

````markdown
```yaml
output_contract_consistency:
  verdict: PASS  # or FAIL or UNCERTAIN
  blocking_findings: []  # list of blocking-token strings, empty if verdict=PASS
  checked_surfaces:
    - HANDOFF
    - RUNTIME_SCOPE_CHECK
    - RTM
    - MANIFEST
    - source snapshots
    - tests
    - diff
```
````

Checker behavior:
- `verdict: PASS` with empty `blocking_findings` → PASS.
- `verdict: PASS` with non-empty `blocking_findings` → FAIL with
  `OUTPUT_CONTRACT_VERDICT_INCONSISTENT`.
- `verdict: FAIL` or `verdict: UNCERTAIN` → FAIL with the first listed blocking-finding
  token (or `STALE_MILESTONE_LABEL` if none specified).
- No structured block found → fall back to negation-aware prose scan.

See `OUTPUT_CONTRACT_CONSISTENCY_AUDIT_TEMPLATE.md` for a copyable example.

---

## Gate 5.2-R1 — Host-path leakage check (append)

For every artifact in `EVIDENCE_LEDGER.yaml` with `artifact_type: raw_test_output`:
- The declared path MUST resolve under the package root.
- An absolute host path (e.g. `/tmp/...`) is permitted ONLY as a `provenance_host_path:`
  field paired with a sibling `package_relative_path:` whose target file exists in the
  package. Both fields must be present.

If the absolute path resolves outside the package and there is no sibling package-relative
copy, the checker fires `HOST_PATH_NOT_PACKAGE_EVIDENCE` and blocks PASS.

---

## Gate 5.2-R1 — Mandatory profile metadata (append)

`GATE_PROFILE_SELECTION.md` must contain `selected_profile`/`gate_profile`, `risk_tier`,
`task_kind`, and a non-empty `reason`/`profile_selection_rationale` regardless of profile.
Missing fields fire `MISSING_RISK_TIER`, `MISSING_TASK_KIND`, and
`MISSING_PROFILE_REASON`.

---

## Gate 5.2-R1 — NOT_APPLICABLE proof hard requirement (append)

Every state listed in the selected profile's `not_applicable_proof_required:` array must
have an exact file at `reports/<task_area>/<STATE>_NOT_APPLICABLE.md` with a substantive
reason. Empty or template-only files fire `NOT_APPLICABLE_REASON_MISSING`. Missing files
fire `MISSING_NOT_APPLICABLE_PROOF`. See `PROOF_FILE_REQUIREMENTS.md` for the full rule.
