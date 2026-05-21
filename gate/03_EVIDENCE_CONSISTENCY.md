# Step 3 — Evidence Consistency Preflight

## Gate 5.2 append

For `GATE_FULL` and `GATE_FULL_PLUS_DOMAIN_ADDENDUM`, the final package must include `reports/<task_area>/OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` or an explicit `OUTPUT_CONTRACT_CONSISTENCY_AUDIT_NOT_APPLICABLE.md` with a specific reason. `STALE_CONTRACT_CLAIM`, `STALE_MILESTONE_LABEL`, `STALE_FIELD_NAME`, `STALE_ARTIFACT_NAME`, `CONTRADICTS_SOURCE`, and `CONTRADICTS_TESTS` are blocking.

**State machine:** Write `current_state: EVIDENCE_CONSISTENCY_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

You are here because the Evidence Adequacy Assessment returned `YES` for preflight readiness.

This step catches failures where the code may be correct but the evidence package proves the wrong thing or contradicts itself — mismatched SHAs, stale diffs, missing files claimed as present, old failing runs treated as current, local paths cited as live evidence.

## Output file to create

```
reports/<task_area>/EVIDENCE_CONSISTENCY_REGISTER.md
```

---

## Source-of-truth hierarchy

When artifacts disagree, trust this order:

1. Actual command output from live repo/package inspection
2. Raw test output files with exit codes
3. Actual package file listing
4. Final changed-file snapshots
5. Final diff generated from actual repo state
6. Evidence Adequacy Assessment and Test/Evidence Plan
7. Manifest
8. Handoff
9. Cold-review prose
10. Implementation narrative ← **never evidence**

---

## Required checks — run all 8

### Check 1 — Canonical repo-state capture

Run and record:

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short
git log --oneline -30
```

Record in the register:

```
CANONICAL_REPO_STATE
- branch:
- current_head_full_sha:
- git_status_short_exact_output:
- worktree_clean: YES/NO
- implementation_commit_sha, if known:
- evidence/report_commit_sha, if separate:
- final_package_commit_sha, if known:
```

**Block if:** repo called clean but `git status --short` is not empty.

### Check 2 — SHA and HEAD claim reconciliation

Search all final evidence docs for SHA/HEAD claims (handoff, manifest, repo-state report, closed-loop gate report, cold review reports, RTM, diff headers, package readme).

```
CLAIMED_SHA_TABLE
| artifact | exact claim | claimed sha | claimed role | matches canonical? | correction needed |
```

**Block if:** two different SHAs described as the same HEAD / implementation commit confused with final HEAD / handoff and manifest disagree on HEAD / package contains placeholder `<recorded after commit>`.

### Check 3 — Package inclusion audit

If a zip package exists:
```bash
zipinfo -1 <package>.zip | sort > reports/<task_area>/PACKAGE_FILE_LISTING.txt
```

If a directory:
```bash
find <package_dir> -type f | sort > reports/<task_area>/PACKAGE_FILE_LISTING.txt
```

Compare against manifest included-file list and handoff included-file list.

```
PACKAGE_PRESENCE_TABLE
| claimed path | claimed by | actual package presence | repo presence | status |
```

**Block if:** file claimed included but absent from package / required reports absent / raw outputs absent / snapshots absent.

### Check 4 — Gate provenance audit

The closed-loop gate report must state how the gate instructions were supplied.

Allowed:
```
Gate source: reports/<task_area>/gate/ (local copy included in package)
Gate file included in package: YES
```
or:
```
Gate source: pasted from primary task prompt
No local gate file was available
```

**Block if:** report claims it read a gate file from a local path that does not exist on the target host / report references `/Users/...` as the live gate source / gate provenance missing.

### Check 5 — Raw test output audit

For every required test output, inspect the raw file directly.

```
RAW_TEST_OUTPUT_TABLE
| output file | command recorded | expected count | observed count | EXIT_CODE parsed | EXIT_CODE flag | post-pass error? | POST_PASS flag | final status |
```

**Block if:** raw output file missing / exact command missing / exit code missing or nonzero / output has PASS summary followed by uncaught error / handoff claims different count than raw output / stale failed run preserved without being clearly marked superseded.

---

## EXIT_CODE Validation — Hard Rule (Gate 5.1)

A passing raw test output must contain a line matching exactly:
```
^EXIT_CODE:0\s*$
```

Defined failure flags — all are BLOCKING, none may be classified EXPECTED_NON_BLOCKING:

| Flag | Condition |
|---|---|
| `EXIT_CODE_MISSING` | No `EXIT_CODE` line appears anywhere in raw output |
| `EXIT_CODE_BLANK` | Line `EXIT_CODE:` present but no value follows (e.g., blank PIPESTATUS capture) |
| `EXIT_CODE_NON_NUMERIC` | EXIT_CODE value present but is not a number (e.g., `EXIT_CODE:ok`, `EXIT_CODE:pass`) |
| `EXIT_CODE_NONZERO` | EXIT_CODE value is a number other than 0 (e.g., `EXIT_CODE:1`) |
| `EXIT_CODE_CONFLICTING` | Multiple `EXIT_CODE:` lines in same raw output with different values |
| `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` | `EXIT_CODE:0` appears in a handoff/summary document but is absent from the raw output file itself |

All six flags are BLOCKING. A raw output with any of these flags CANNOT be used to support a PASS claim.

The RAW_TEST_OUTPUT_TABLE must record the exact parsed EXIT_CODE state for every raw output file, using one of: `EXIT_CODE:0 (valid)`, `EXIT_CODE_MISSING`, `EXIT_CODE_BLANK`, `EXIT_CODE_NON_NUMERIC`, `EXIT_CODE_NONZERO`, `EXIT_CODE_CONFLICTING`, or `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW`.

---

## Post-PASS Uncaught Error Detection — Hard Rule (Gate 5.1)

A raw output is BLOCKING if it shows a PASS summary line followed later by an uncaught error or infrastructure failure.

Blocking post-PASS patterns (flag: `POST_PASS_UNCAUGHT_ERROR`):

| Pattern | Example |
|---|---|
| `Error:` after Jest/test PASS line | `Error: ENOENT: ... open '/tmp/jest_rs/perf-cache'` after `Tests: 3 passed, 3 total` |
| `ENOENT` after PASS | Cache write failure after passing test summary |
| `UnhandledPromiseRejection` anywhere | Promise rejection not caught by test runner |
| `uncaughtException` anywhere | Uncaught exception after test runner finishes |
| `Jest did not exit` when clean exit required | Process hang after test summary |
| Cache write/open failure after PASS | Any filesystem failure following a passing summary |
| Any stack trace after PASS | Any `at Object.` or `at Function.` lines appearing after PASS summary |

The `POST_PASS_UNCAUGHT_ERROR` flag is BLOCKING unless the package provides:
- An explicit, evidence-backed reason the error is expected AND non-impacting
- A named reference to the specific error (not a generic "post-PASS errors are known")
- A statement of why the error does not affect result correctness

Mere proximity to a PASS line is not sufficient justification. "Tests passed" does not override a blocking post-PASS error.

### Check 6 — Stale-language scan

```bash
grep -RInE 'pending|recorded after|will include|not included|TODO|TBD|EXIT_CODE:1|matches actual HEAD|/Users/|local Mac|stale|superseded' reports/<task_area> || true
```

Classify every match:

```
STALE_LANGUAGE_TABLE
| artifact | phrase | context | valid historical note? | needs correction? |
```

**Block if:** stale failure language in final status sections / placeholder commit language remains / old failed test output treated as final / local user paths cited as live evidence.

### Check 7 — Diff/snapshot/repo consistency

- Final diff exists
- Snapshots exist for every changed source/test file required by the task
- Diff matches final repo changes
- Snapshots match final repo files
- Snapshots cover the changed regions, not just unrelated parts

**Block if:** diff shows content not in snapshots / snapshots show cleaned content but diff shows old content / changed files missing snapshots / diff path in handoff is wrong.

### Check 8 — Report agreement audit

Compare final claims across: repo-state report, handoff, manifest, closed-loop gate report, cold review adjudication, RTM.

```
REPORT_AGREEMENT_TABLE
| claim type | repo-state | handoff | manifest | gate report | cold adjudication | agreed? |
```

Required claim types: final HEAD / git status / files changed / tests run / test counts / exit codes / package files included / closed-loop verdict / next allowed phase / forbidden phases not started.

**Block if:** final claims disagree across artifacts.

---

## Gate 4.1 — Diff base verification (append to Check 7 when GATE_STANDARD or GATE_FULL)

Before finalizing the consistency check, verify the diff base and scope:

1. Run `git rev-parse HEAD` and record the HEAD SHA
2. Run `git merge-base [task_branch] [target_branch]` and record the correct base SHA
3. Run `git diff [base]..[HEAD] --name-only` and record all changed files
4. Verify all changed files are in the allowed touch map
5. If any out-of-scope files appear in the diff: flag as `DIFF_CONTAINS_OUT_OF_SCOPE_CHANGES`

This check is a prerequisite for `30_DIFF_BASE_SCOPE_AUDIT.md` — record the diff base and HEAD here so Step 30 can cross-reference.

---

## Routing

Write to CURRENT_STATE.yaml before routing:
```yaml
cycles:
  <N>:
    consistency_result: PASS | BLOCKING_CONTRADICTIONS_FOUND
    consistency_contradictions_found: <count>
```

| Outcome | State to write | Next file |
|---|---|---|
| All 8 checks pass — no blocking contradictions | `EVIDENCE_CONSISTENCY_PASS` | `14_ENFORCEMENT_AUTHORITY_AUDIT.md` |
| Blocking contradictions found but fixable (wrong SHA in a doc, stale manifest entry) | (remain in `EVIDENCE_CONSISTENCY_IN_PROGRESS`) | Fix them, then **come back to `03_EVIDENCE_CONSISTENCY.md`** and rerun all 8 checks |
| Blocking contradictions cannot be fixed within scope | `EVIDENCE_CONSISTENCY_BLOCKED` | `13_BLOCKED_HANDOFF.md` |
