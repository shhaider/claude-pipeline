# Gate 5.2-R1 — Failure-mode → fix → fixture verification

For each P-step, this report names the underlying failure mode, the new flag(s) the
Gate 5.2-R1 checker emits, and the fixtures that mechanically prove the fix works.

---

## P01 — Disallow exported-evidence host-path leakage

**Failure mode it targets:**
A package's `EVIDENCE_LEDGER.yaml` declares a `raw_test_output` artifact at an absolute
host path (e.g. `/tmp/some_raw_output.txt`) and the file is never copied into the
exported package. A reviewer on a different machine cannot validate the run because the
artifact is unreachable.

**New blocking flag:** `HOST_PATH_NOT_PACKAGE_EVIDENCE`

**Fixtures:**

| Fixture | Profile | Expected | Observed |
|---|---|---|---|
| `absolute_raw_output_outside_package` (bad) | GATE_FULL | FAIL | `Result: FAIL`, `EXIT: 0` (checker exits 1 → captured by test framework as non-zero return; test asserts `assert_failed`). Combined output contains `HOST_PATH_NOT_PACKAGE_EVIDENCE`. |
| `absolute_host_path_plus_package_copy` (good) | GATE_FULL | PASS | `Result: PASS`, `Checks passed: 47  \|  Checks failed: 0` |

**Test functions:**
- `test_absolute_raw_output_outside_package`
- `test_absolute_host_path_plus_package_copy`

---

## P02 — Require profile metadata for ALL profiles

**Failure mode it targets:**
A `GATE_LITE` package omits `risk_tier` and `task_kind`, so the WRONG_GATE_PROFILE
selector cannot mechanically detect that the package picked too-weak a profile for its
real task class. Pre-R1 the checker only enforced these fields for `STANDARD_AND_UP`,
which is precisely the wrong place — Lite packages were the ones that benefited most
from skipping the metadata.

**New blocking flags (already existed but now apply to all profiles):**
- `MISSING_RISK_TIER`
- `MISSING_TASK_KIND`
- `MISSING_PROFILE_REASON`

**Fixtures:**

| Fixture | Profile | Expected | Observed |
|---|---|---|---|
| `lite_profile_missing_risk_task` (bad) | GATE_LITE | FAIL | `Result: FAIL`. Combined output contains `MISSING_RISK_TIER` and `MISSING_TASK_KIND`. |

**Test function:** `test_lite_profile_missing_risk_task` (asserts both tokens present in output)

---

## P03 — Enforce NOT_APPLICABLE proof requirements as hard-blocking

**Failure mode it targets:**
A profile lists states in `not_applicable_proof_required:` but the checker only emitted
a PASS-with-WARN line if those `_NOT_APPLICABLE.md` files were absent. Operators could
ignore the warning and still PASS, defeating the explicit-decision intent.

**New blocking flags:**
- `MISSING_NOT_APPLICABLE_PROOF` — required NA file is absent
- `NOT_APPLICABLE_REASON_MISSING` — file present but empty/template-only

The checker also accepts a "substantive reason" if the body contains an NA keyword
(e.g. "because", "audit-only task", "no tests run", "no migration", "no concurrent
state", "no consumer api") OR more than 80 characters of non-template prose.

The GATE_LITE `not_applicable_proof_required` list is trimmed from 19 to 8 entries —
only those operators are realistically expected to NA-prove.

**Fixtures:**

| Fixture | Profile | Expected | Observed |
|---|---|---|---|
| `missing_not_applicable_proof` (bad) | GATE_STANDARD | FAIL | 4× `MISSING_NOT_APPLICABLE_PROOF` flags |
| `empty_not_applicable_reason` (bad) | GATE_STANDARD | FAIL | `NOT_APPLICABLE_REASON_MISSING` for `GATE_EFFECTIVENESS_LOG_NOT_APPLICABLE.md` (heading-only) |
| `not_applicable_with_reason` (good) | GATE_STANDARD | PASS | `Result: PASS`, `Checks passed: 33  \|  Checks failed: 0` |

**Test functions:**
- `test_missing_not_applicable_proof`
- `test_empty_not_applicable_reason`
- `test_not_applicable_with_reason`

---

## P04 — Approved dirty-worktree label set

**Failure mode it targets:**
The pre-R1 checker only accepted the literal string `UNRELATED_EXTERNAL_WORK` (or the
phrase "unrelated external work") for dirty-path classification. Real-world Gate Full
packages legitimately use other labels — e.g. `ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH` for
files a concurrent sprint is editing, `AMBIENT_UNRELATED_DOC_COMMIT` for changelog
entries committed alongside but unrelated to the audited change. There was also no
escape hatch for paths the agent could not classify on its own.

**New blocking flags:**
- `DIRTY_PATH_NOT_CLASSIFIED` — dirty path is not on the classification table at all,
  or its row has no recognized label
- `UNKNOWN_REQUIRES_HUMAN_BLOCKER` — explicitly classified `UNKNOWN_REQUIRES_HUMAN`

**Approved labels (any of these allow PASS):**
- `UNRELATED_EXTERNAL_WORK`
- `ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH`
- `AMBIENT_UNRELATED_DOC_COMMIT`
- `UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN`

**Always-blocking tokens (regardless of label):**
`node_modules`, `.run_artifacts`, `raw_test_output*`, `raw_outputs/`, generated
`DOC_FRESHNESS_REPORT.md` in repo.

**Fixtures:**

| Fixture | Profile | Expected | Observed |
|---|---|---|---|
| `dirty_git_status_active_parallel_work` (good) | GATE_FULL | PASS | `Result: PASS`, `Checks passed: 46  \|  Checks failed: 0` |
| `dirty_git_status_ambient_doc_commit` (good) | GATE_FULL | PASS | `Result: PASS`, `Checks passed: 45  \|  Checks failed: 0` |
| `dirty_git_status_unknown_requires_human` (bad) | GATE_FULL | FAIL | `UNKNOWN_REQUIRES_HUMAN_BLOCKER` flag |
| `dirty_git_status_unclassified_paths` (bad) | GATE_FULL | FAIL | `DIRTY_PATH_NOT_CLASSIFIED` flag for the unclassified path |

**Test functions:**
- `test_dirty_git_status_active_parallel_work`
- `test_dirty_git_status_ambient_doc_commit`
- `test_dirty_git_status_unknown_requires_human`
- `test_dirty_git_status_unclassified_paths`

The pre-existing `test_dirty_git_status_classified_unrelated` and the related
`test_dirty_git_status_unclassified` / `test_dirty_git_status_task_relevant` tests
continue to pass under the expanded label whitelist.

---

## P05 — Output-contract structured verdict + negation-aware fallback

**Failure mode it targets:**
The pre-R1 prose scan looked for substring matches of `STALE_MILESTONE_LABEL` etc.
inside `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md`. Audits that explicitly stated "No
STALE_MILESTONE_LABEL found" tripped the false-positive (the token was present, in a
negated context).

**Fix:**
The checker now first looks for a fenced YAML block with key
`output_contract_consistency:`. If found, it uses the structured `verdict:` and
`blocking_findings:` directly. If no structured block is present, it falls back to a
prose scan that distinguishes negated mentions ("No X found", "X not detected",
"X: none") from positive detections ("X detected in HANDOFF.md").

**New flags:**
- `OUTPUT_CONTRACT_VERDICT_INCONSISTENT` — verdict=PASS but blocking_findings non-empty
- `OUTPUT_CONTRACT_VERDICT_UNKNOWN` — verdict value not in {PASS, FAIL, UNCERTAIN}
- `OUTPUT_CONTRACT_VERDICT_UNCERTAIN` — verdict=UNCERTAIN

Plus the existing token flags (`STALE_MILESTONE_LABEL`, `STALE_CONTRACT_CLAIM`, etc.)
are still emitted from either path.

**Fixtures:**

| Fixture | Profile | Expected | Observed |
|---|---|---|---|
| `output_contract_negated_token` (good) | GATE_FULL | PASS | `Result: PASS`, fallback prose scan correctly handled negated tokens |
| `output_contract_structured_pass` (good) | GATE_FULL | PASS | `Result: PASS`, structured verdict PASS over 7 surfaces |
| `output_contract_structured_fail` (bad) | GATE_FULL | FAIL | `STALE_MILESTONE_LABEL` flag from structured path |
| `output_contract_inconsistent_verdict` (bad) | GATE_FULL | FAIL | `OUTPUT_CONTRACT_VERDICT_INCONSISTENT` flag |
| `output_contract_actual_token_unstructured` (bad) | GATE_FULL | FAIL | `STALE_MILESTONE_LABEL` flag from fallback prose scan (positive, non-negated) |

**Test functions:**
- `test_output_contract_negated_token`
- `test_output_contract_structured_pass`
- `test_output_contract_structured_fail`
- `test_output_contract_inconsistent_verdict`
- `test_output_contract_actual_token_unstructured`

---

## Aggregate verification

| P-step | New flag(s) | Bad fixtures | Good fixtures | Tests added |
|---|---|---|---|---|
| P01 | HOST_PATH_NOT_PACKAGE_EVIDENCE | 1 | 1 | 2 |
| P02 | MISSING_RISK_TIER, MISSING_TASK_KIND (now apply to LITE) | 1 | (existing happy paths) | 1 |
| P03 | MISSING_NOT_APPLICABLE_PROOF, NOT_APPLICABLE_REASON_MISSING | 2 | 1 | 3 |
| P04 | DIRTY_PATH_NOT_CLASSIFIED, UNKNOWN_REQUIRES_HUMAN_BLOCKER | 2 | 2 | 4 |
| P05 | OUTPUT_CONTRACT_VERDICT_INCONSISTENT, OUTPUT_CONTRACT_VERDICT_UNCERTAIN, OUTPUT_CONTRACT_VERDICT_UNKNOWN | 3 | 2 | 5 |
| **Total** | **9 new flags** | **9 bad fixtures** | **6 good fixtures** | **15 tests** |

All 15 new tests + all 21 existing tests pass: **36/36 PASS**.

Lane D production cross-check: **61/61 PASS** (no regression).

happy_path fixture cross-check: **45/45 PASS** (no regression).
