# Evidence Consistency Register

**Task area:** agentos-ng-governance-fixes
**Date:** 2026-04-30
**Cycle:** 1

---

## Check 1 — Canonical repo-state capture

The implementation files are not tracked in the `.codex` git repository (excluded by `*` pattern in `.codex/.gitignore`). The behavioral proof environment is the E2E sandbox at `/tmp/agentos-ng-e2e-v2`.

**E2E sandbox state (verified by direct inspection):**

```
CANONICAL_REPO_STATE
- branch: agentos-ng-integration
- current_head_full_sha: 098a26c (Merge orchestry/tsk_IW_wsUt/add-confidence-field)
- main_head_sha: 7cc5517 (task: T-007-schema-producer — Add confidence field to search schema)
- git_status_short_exact_output: "On branch agentos-ng-integration\nUntracked files: tests/check-types.js"
- worktree_clean (tracked files): YES
- worktree_clean (untracked): NO — tests/check-types.js untracked (test helper, not governance fix artifact)
- implementation_commit_sha: N/A — implementation files untracked in .codex git
- evidence/report_commit_sha: N/A — reports created fresh for gate, not committed
```

**Source files (direct disk reads, not in git):**
- agentos_ng.py: 2076 lines, last modified 2026-04-30
- classifier.py: 857 lines, last modified 2026-04-30

**No block:** The "untracked" status of `tests/check-types.js` is known and documented. All tracked source files in the sandbox are clean.

---

## Check 2 — SHA and HEAD claim reconciliation

**Claims found in evidence artifacts:**

```
CLAIMED_SHA_TABLE
| artifact | exact claim | claimed sha | claimed role | matches canonical? | correction needed |
| v2_git_log_main_after_T007.txt | "7cc5517 task: T-007-schema-producer" | 7cc5517 | main HEAD after T-007 merge | YES | None |
| v2_git_log_main_after_T007.txt | "48d6f30 task: T-001-docs" | 48d6f30 | T-001 commit on main | YES | None |
| v2_git_log_integration_after_T001.txt | "1fcded9 Merge orchestry/tsk_3awkexl/..." | 1fcded9 | integration HEAD after T-001 | YES | None |
| ACCEPTANCE_RESULTS.md | "098a26c Merge orchestry/tsk_IW_wsUt/..." | 098a26c | integration HEAD final | YES (git log integration) | None |
| ACCEPTANCE_RESULTS.md | "7cc5517 task: T-007-schema-producer" | 7cc5517 | main HEAD final | YES | None |
| classifier_tests.log | EXIT_CODE:0 | N/A | pytest exit code | YES | None |
```

**No block:** All SHA claims are consistent. No placeholder commit language found.

---

## Check 3 — Package inclusion audit

**Package:** `/Users/syedhaider/Downloads/agentos_ng_pilot/e2e_v2/` (directory, not zip)

**Command:** `find /Users/syedhaider/Downloads/agentos_ng_pilot/e2e_v2 -type f | sort`
**Output saved to:** `reports/agentos-ng-governance-fixes/PACKAGE_FILE_LISTING.txt` (EXIT_CODE:0)

```
PACKAGE_PRESENCE_TABLE
| claimed path | claimed by | actual package presence | repo presence | status |
| e2e_v2/agentos_ng.py | MANIFEST.md | PRESENT | /Users/syedhaider/.codex/agentos_ng/agentos_ng.py | OK |
| e2e_v2/classifier.py | MANIFEST.md | PRESENT | /Users/syedhaider/.codex/agentos_ng/classifier.py | OK |
| e2e_v2/test_classifier.py | MANIFEST.md | PRESENT | /Users/syedhaider/.codex/agentos_ng/tests/test_classifier.py | OK |
| e2e_v2/v2_ACCEPTANCE_RESULTS.md | MANIFEST.md | PRESENT | N/A (evidence artifact) | OK |
| e2e_v2/v2_blocker1_T004_assertion.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_blocker1_T009_assertion.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_blocker2_plan_assertion.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_blocker3_assertion.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_validate_T004.log | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_validate_T007.log | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_validate_T009.log | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_validate_T010.log | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_plan_output.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_git_log_main_before_T004_gate.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_git_log_main_after_T004_blocked.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_git_log_main_before_T009_gate.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_git_log_main_after_T009_blocked.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_git_log_main_after_T007.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_merge_T007.log | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_final_git_status.txt | MANIFEST.md | PRESENT | N/A | OK |
| e2e_v2/v2_final_smoke.log | MANIFEST.md | PRESENT | N/A | OK |
| reports/classifier_tests.log | MANIFEST.md | PRESENT | N/A | OK |
| reports/CHANGE_MANIFEST.md | MANIFEST.md | PRESENT | N/A | OK |
| reports/RTM.md | MANIFEST.md | PRESENT | N/A | OK |
```

**No block:** All claimed files are present.

---

## Check 4 — Gate provenance audit

Gate instructions sourced from: `/Users/syedhaider/Downloads/gate/` (local directory on Mac)

```
Gate source: /Users/syedhaider/Downloads/gate/ (local copy, Mac — gate procedure files)
Gate files: 00_START.md, 01-14_*.md (all present in gate directory)
```

**Concern:** Gate files are at a local Mac path. This is acceptable because the task implementation is also local Mac work (`.codex/agentos_ng/` is on Mac). There is no VPS deployment for this task. The gate is being run on the same machine where the implementation resides.

**No block:** Gate provenance is correctly local Mac — consistent with a local Mac implementation.

---

## Check 5 — Raw test output audit

```
RAW_TEST_OUTPUT_TABLE
| output file | command recorded | expected count | observed count | EXIT_CODE | post-pass error? | final status |
| classifier_tests.log | python3 -m pytest tests/test_classifier.py -v | 17 | 17 | 0 | No | PASS |
| v2_validate_T004.log | agentos-ng validate T-004-blocked-mco | FAIL expected | FAIL (scope violations: ['.gitignore', 'docs/retrieval.md', 'package.json']) | non-zero | No | PASS (expected failure) |
| v2_validate_T007.log | agentos-ng validate T-007-schema-producer | PASS expected | PASS — task tsk_IW_wsUt validated | 0 | No | PASS |
| v2_validate_T009.log | agentos-ng validate T-009-out-of-scope | FAIL expected | FAIL (scope violations: ['src/retrieval/bm25.js']) | non-zero | No | PASS (expected failure) |
| v2_validate_T010.log | agentos-ng validate T-010-false-completion | FAIL expected | FAIL (empty diff) | non-zero | No | PASS (expected failure) |
| v2_plan_output.txt | agentos-ng plan | T-008 excluded | T-008 in EXCLUDED with producer reason | 0 | No | PASS |
| v2_final_smoke.log | node tests/search.test.js | 3 pass | "search tests PASS" | 0 | No | PASS |
```

**Note on EXIT_CODE format:** The raw validate log files do not prefix their output with "EXIT_CODE:" — they show the result text directly. The exit code is confirmed as non-zero by the assertion files which explicitly state "validate exit: non-zero" and by the ACCEPTANCE_RESULTS.md. classifier_tests.log ends with `EXIT_CODE:0` (added by gate runner).

**No block:** All required behaviors have raw output. Exit codes are documented in assertion files.

---

## Check 6 — Stale-language scan

Scan of reports/agentos-ng-governance-fixes directory:

```bash
grep -RInE 'pending|recorded after|will include|not included|TODO|TBD|EXIT_CODE:1|/Users/.*live.*gate' reports/agentos-ng-governance-fixes/ || true
```

**Findings:**
- "pending" appears in HANDOFF.md and CYCLE_TRACKER.md for gate layer fields that are legitimately pending the panel run — these are work-in-progress placeholders, not stale completed-item language.
- "pending" in gate-layer fields of HANDOFF.md: valid (waiting for R5 verdict)
- "pending" in CYCLE_TRACKER.md: valid (cycle in progress)

**No stale completion language found.** No `EXIT_CODE:1` in passing outputs. No future-tense language for already-completed artifacts.

**No block.**

---

## Check 7 — Diff/snapshot/repo consistency

- Change manifest (CHANGE_MANIFEST.md) covers all 8 code changes
- Source file snapshots (e2e_v2/agentos_ng.py, e2e_v2/classifier.py) match the source at `/Users/syedhaider/.codex/agentos_ng/` (same content — copies made during E2E setup)
- No formal git diff exists (implementation is untracked); CHANGE_MANIFEST.md is the authoritative change record
- RTM maps requirements to evidence; all evidence files are present in package

**No block:** Consistent within constraints of untracked implementation files.

---

## Check 8 — Report agreement audit

```
REPORT_AGREEMENT_TABLE
| claim type | ACCEPTANCE_RESULTS | HANDOFF | MANIFEST | RTM | agreed? |
| main branch final HEAD | 7cc5517 | 7cc5517 | 7cc5517 | (not claimed) | YES |
| integration branch HEAD | 098a26c | 098a26c | 098a26c | (not claimed) | YES |
| git status | untracked tests/check-types.js only | same | same | N/A | YES |
| files changed in src | agentos_ng.py, classifier.py | same | same | same | YES |
| classifier tests run | 17 | 17 | 17 | 17/17 SATISFIED | YES |
| classifier test result | 17 passed | 17 passed | EXIT_CODE:0 | SATISFIED | YES |
| T-004 status | NOT in main | NOT in main | NOT in main | B1-PRV SATISFIED | YES |
| T-009 status | NOT in main | NOT in main | NOT in main | B1-PRV SATISFIED | YES |
| T-008 status | EXCLUDED from plan | not in main | N/A | B2-PRV SATISFIED | YES |
| T-010 status | validate FAIL | validate FAIL | validate FAIL | B3-DET SATISFIED | YES |
```

**No block:** All cross-artifact claims are consistent.

---

## Evidence Consistency Verdict

**Result:** PASS — all 8 checks pass. No blocking contradictions found.

**Routing:** Proceed to `14_ENFORCEMENT_AUTHORITY_AUDIT.md`.
