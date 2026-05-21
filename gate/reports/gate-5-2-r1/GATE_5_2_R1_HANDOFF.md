# Gate 5.2-R1 Hardening — Handoff

**Final status:** `GATE_5_2_R1_READY_FOR_ACCEPTANCE_AUDIT`

## What changed

Gate 5.2-R1 adds five blocking enforcements that were missing or advisory under Gate 5.2.0:

1. **P01 — Host-path leakage detection.** Raw test outputs declared via absolute host
   paths (e.g. `/tmp/...`) without an in-package copy now fire
   `HOST_PATH_NOT_PACKAGE_EVIDENCE`. A new `provenance_host_path:` +
   `package_relative_path:` pattern is supported for documenting host provenance while
   keeping the artifact exported.
2. **P02 — Profile metadata for ALL profiles.** `risk_tier`, `task_kind`, and
   `profile_selection_rationale`/`reason` are now mandatory in every
   `GATE_PROFILE_SELECTION.md`, including `GATE_LITE`. Pre-R1 the checker only enforced
   these for Standard and above — exactly the wrong place, since under-selection is
   precisely a Lite-side concern.
3. **P03 — NOT_APPLICABLE proof is hard-blocking.** Missing NA proof fires
   `MISSING_NOT_APPLICABLE_PROOF`; empty/template-only NA proof fires
   `NOT_APPLICABLE_REASON_MISSING`. The GATE_LITE list is trimmed from 19 to 8 entries
   so the enforcement isn't punishingly heavy.
4. **P04 — Approved dirty-worktree label set.**
   `ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH`, `AMBIENT_UNRELATED_DOC_COMMIT`,
   `UNRELATED_EXTERNAL_WORK`, and `UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN` are accepted.
   `UNKNOWN_REQUIRES_HUMAN` blocks via `UNKNOWN_REQUIRES_HUMAN_BLOCKER`. Unclassified
   dirty paths block via `DIRTY_PATH_NOT_CLASSIFIED`.
5. **P05 — Output-contract structured verdict.**
   `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` should now contain a fenced YAML block under
   key `output_contract_consistency:` with `verdict:` (PASS/FAIL/UNCERTAIN) and
   `blocking_findings:`. The checker prefers the structured form. Without one, it
   falls back to a negation-aware prose scan that no longer false-positives on phrases
   like "No STALE_MILESTONE_LABEL found".

## Self-test result

**36 / 36 PASS** (21 baseline + 15 new for R1).

## Cross-checks

| Check | Result |
|---|---|
| `tests/fixtures/happy_path_gate_full` (final mode) | **PASS** — 45/45 checks |
| `METAOS_AUDIT_LANE_D_SIGNOUT.zip` (production package) | **PASS** — 61/61 checks |

**Zero regressions introduced by R1.** The Lane D package, which was validated under
unmodified Gate 5.2 and signed out by the operator, still passes under Gate 5.2-R1
without any modification to the package itself.

## Files modified / created

See `GATE_5_2_R1_CHANGED_FILES.md` for the full inventory:
- 11 existing files modified
- 16 new files created (1 template, 15 fixtures)
- 5 report files in `reports/gate-5-2-r1/`

## Per-P-step verification

See `GATE_5_2_R1_FAILURE_FIX_VERIFICATION.md` for the failure-mode → fix → fixture
mapping with concrete checker output.

## Should Gate 5.2 be considered ready for canonical install after R1?

**The R1 hardening pass is complete and ready for acceptance audit.** All five
hardening goals are implemented, fully tested, and verified non-regressive against the
Lane D production package. The decision to install as canonical is left to the
acceptance audit (per the prompt's explicit instruction).

If the acceptance auditor agrees, Gate 5.2-R1 should be the canonical Gate from this
point forward — superseding 5.2.0 and 5.1 — because:

- It catches everything 5.2.0 caught (verified — Lane D and happy_path still PASS).
- It additionally catches five real failure modes that 5.2.0 silently allowed (host
  paths, missing Lite metadata, unenforced NA proofs, narrow dirty-label whitelist,
  prose-scan false positives).
- All new enforcement is mechanical (not prose-only) and has fixture coverage.

## Open questions / Gate 5.3 backlog

- **Domain-addendum file existence is still not enforced.** The
  `GATE_FULL_PLUS_DOMAIN_ADDENDUM` profile lists `DOMAIN_ADDENDUM_{name}.md` in
  `required_always_additional` but the checker silently skips templates with `{name}`.
  R2 should accept a `domain_addenda:` list in `GATE_PROFILE_SELECTION.md` and require
  `reports/<task_area>/DOMAIN_ADDENDUM_<name>.md` for each.
- **`SUMMARY_DOC_PATTERNS` is still broad** — a doc that legitimately quotes
  `EXIT_CODE:0` in a code example could trip `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW`. R2
  should add a fence-aware skip similar to the new structured-verdict scanner.
- **Display-only path-trim cosmetic bug** in `dirty_paths_from_git_status` — chops one
  extra char from dirty paths in failure messages. Classification still correct;
  cosmetic only. Defer to R2 for cleanup.
- **No fixtures for `EXIT_CODE_CONFLICTING` or `EXIT_CODE_NON_NUMERIC`.** Code paths
  exist but are unexercised. Add as part of R2 self-test expansion.
- **Substantive-reason heuristic in `_na_reason_is_substantive` is keyword-based.** Real
  package authors might write a substantive reason that fails the keyword test (e.g.
  by paraphrasing). R2 might augment with a length-only floor or a small LLM check.
  Current heuristic is conservative: 80+ chars OR a known keyword.
- **R1 fixtures use `dirty_git_status_unclassified_paths` rather than upgrading the
  pre-existing `dirty_git_status_unclassified` fixture.** The pre-existing fixture
  tests the case where there is no classification file at all (different path in the
  checker), so both fixtures are now correct and complementary.

## Lingering concerns I want to flag

- The negation-aware prose scan in `_scan_blocking_token_with_negation` covers the
  common cases (preceding `no`/`not`, trailing `not found`/`none`/`absent`) but is not
  exhaustive. Edge cases like "I confirmed STALE_MILESTONE_LABEL did not appear" might
  still trip a false positive. The structured verdict block is the recommended path
  precisely so audits don't have to rely on the prose scanner. R2 may iterate on the
  scanner if real packages report false positives.
- The `_NA_REASON_KEYWORDS` list is opinionated. If an operator writes "Not relevant —
  no production caller exists yet" it would NOT match any keyword on a literal pass,
  but the 80-char floor would let it through. Make sure the operator-facing docs
  emphasize the 80-char floor as the simple way to comply.

## Verdict

**`GATE_5_2_R1_READY_FOR_ACCEPTANCE_AUDIT`**
