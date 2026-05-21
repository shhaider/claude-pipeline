# Gate 5.2-R1 Install Decision

**Date:** 2026-05-01
**Auditor:** Independent acceptance auditor
**Decision:** `GATE_5_2_R1_ACCEPTED_INSTALL_CANONICAL`

## Acceptance criteria — all satisfied

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Source verification: 7/7 PASS | YES | `GATE_5_2_R1_SOURCE_VERIFICATION.md` |
| Self-tests: ≥36/36 PASS, exit 0 | YES (36/36, exit 0) | `GATE_5_2_R1_SELF_TEST_RERUN.md` |
| Targeted fixture verification: 10/10 match expected | YES (10/10) | `GATE_5_2_R1_TARGETED_FIXTURE_VERIFICATION.md` |
| Full gate snapshot zip exists | YES | `/Users/syedhaider/Downloads/gate_5_2_r1_canonical_candidate_2026-05-01.zip` (1.3 MB, 1476 entries) |
| SHA256 recorded in a file | YES | `GATE_5_2_R1_CANONICAL_ZIP_SHA256.txt` |
| Real diff produced (not placeholder) | YES (1642 lines, valid unified-diff format) | `GATE_5_2_TO_5_2_R1_DIFF.patch` |
| Lane D recheck PASS or fails for documented R1-correct reason | YES (61/61 PASS, exit 0 — no regression) | `GATE_5_2_R1_LANE_D_RECHECK.md` |

## Final verdict: GATE_5_2_R1_ACCEPTED_INSTALL_CANONICAL

`/Users/syedhaider/Downloads/gate` is hereby accepted as **canonical Gate 5.2-R1**.

### Canonical pointers

| Item | Path |
|------|------|
| Live canonical install | `/Users/syedhaider/Downloads/gate` |
| Frozen canonical ZIP | `/Users/syedhaider/Downloads/gate_5_2_r1_canonical_candidate_2026-05-01.zip` |
| ZIP SHA256 | `063550cfd5ef99df50f553673db4dba94fb89bcb6486c43875ef139d1c99db91` |
| Standing usage rule | `/Users/syedhaider/Downloads/gate/GATE_5_2_USAGE_RULE.md` |
| Acceptance signout (this audit) | `/Users/syedhaider/Downloads/gate/reports/gate-5-2-r1-acceptance/` |

## Gate 5.2-R1 hardening summary (verified by this acceptance)

R1 added the following blocking checks to Gate 5.2:

1. **HOST_PATH_NOT_PACKAGE_EVIDENCE** — declared raw outputs that are absolute and resolve outside the package, with no in-package copy, are blocked.
2. **MISSING_RISK_TIER / MISSING_TASK_KIND / MISSING_PROFILE_REASON** — ALL profiles (including GATE_LITE) require these metadata fields.
3. **MISSING_NOT_APPLICABLE_PROOF / NOT_APPLICABLE_REASON_MISSING** — NA proofs are now hard requirements with substantive-reason content checks.
4. **DIRTY_PATH_NOT_CLASSIFIED / UNKNOWN_REQUIRES_HUMAN_BLOCKER** — every dirty path must be classified with one of four approved labels; `UNKNOWN_REQUIRES_HUMAN` blocks.
5. **OUTPUT_CONTRACT_VERDICT_INCONSISTENT / UNCERTAIN / UNKNOWN** — structured YAML verdict block parsing for output-contract audits, with negation-aware prose-scan fallback.
6. **MISSING_CHECKER_REPORT_FINAL_MODE** — `--final` requires the validation report be present in-package.
7. **gate_source_included** — package must export `gate_used/` directory or `gate_hash.txt`.

## Remaining Gate 5.3 backlog (carried forward)

These items are NOT regressions and NOT R1 in scope; they are documented in the implementer R1 handoff (`reports/gate-5-2-r1/GATE_5_2_R1_HANDOFF.md`) as Gate 5.3 candidates:

- Domain-addendum enforcement (`GATE_FULL_PLUS_DOMAIN_ADDENDUM` profile checks)
- Fence-aware `EXIT_CODE` skip in summary docs (avoid false positives where docs quote raw output inside fenced blocks)
- Dirty path-trim cosmetic bug (whitespace normalization in classification matching)
- Missing fixtures for `EXIT_CODE_CONFLICTING` and `EXIT_CODE_NON_NUMERIC`
- NA-reason heuristic robustness (currently 80-char threshold + keyword list)
- Prose-scan exhaustiveness (additional negation patterns)

These items are tracked, not blocking.

## Notes for downstream consumers

- Existing packages built under unmodified Gate 5.2 (e.g. Lane D) continue to PASS under R1 — no migration required for already-completed packages.
- New packages from 2026-05-01 onward MUST include `risk_tier`, `task_kind`, and `reason` in `GATE_PROFILE_SELECTION.md` even for GATE_LITE.
- New packages SHOULD adopt the structured YAML verdict block in `OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md` to avoid prose-scan ambiguity (the fallback prose scan still works but is brittle).
