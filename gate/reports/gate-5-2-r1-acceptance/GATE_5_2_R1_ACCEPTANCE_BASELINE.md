# Gate 5.2-R1 Acceptance Audit — Baseline

**Date:** 2026-05-01
**Auditor:** Independent acceptance auditor
**Gate folder:** `/Users/syedhaider/Downloads/gate`
**Reference R1 signout:** `/Users/syedhaider/Downloads/GATE_5_2_R1_HARDENING_SIGNOUT.zip`

## Inventory summary

- Total tracked files (depth ≤ 4, excl. `.DS_Store`): **224**
- Python: 3.14.3
- Checker: `tools/check_gate_package.py` exists, **1403 lines**
- Self-tests: `tests/test_check_gate_package.py` exists, **395 lines**

## Reports directories present

```
gate-4-1-upgrade
gate-5-1-upgrade
gate-5-2
gate-5-2-acceptance
gate-5-2-r1                  ← implementer's R1 reports
gate-5-2-r1-acceptance       ← THIS audit
gate-state-machine-upgrade-2026-04-30
gate-state-machine-upgrade-session-2026-05-01
```

Implementer's R1 reports include:
- `GATE_5_2_R1_BASELINE.md`
- `GATE_5_2_R1_CHANGED_FILES.md`
- `GATE_5_2_R1_FAILURE_FIX_VERIFICATION.md`
- `GATE_5_2_R1_HANDOFF.md`
- `GATE_5_2_R1_SELF_TEST_RESULTS.md`

## R1 fixtures present (15/15)

All 15 R1 fixture directories required by the acceptance protocol are present:

1. `absolute_raw_output_outside_package` — EXISTS
2. `absolute_host_path_plus_package_copy` — EXISTS
3. `lite_profile_missing_risk_task` — EXISTS
4. `missing_not_applicable_proof` — EXISTS
5. `empty_not_applicable_reason` — EXISTS
6. `not_applicable_with_reason` — EXISTS
7. `dirty_git_status_active_parallel_work` — EXISTS
8. `dirty_git_status_ambient_doc_commit` — EXISTS
9. `dirty_git_status_unknown_requires_human` — EXISTS
10. `dirty_git_status_unclassified_paths` — EXISTS
11. `output_contract_negated_token` — EXISTS
12. `output_contract_structured_pass` — EXISTS
13. `output_contract_structured_fail` — EXISTS
14. `output_contract_inconsistent_verdict` — EXISTS
15. `output_contract_actual_token_unstructured` — EXISTS

Total fixture directories in `tests/fixtures/`: 37 (15 R1 + 22 pre-existing).

## Version markers

- `00_START.md` line 1: `# Gate — Entry Point (Gate 5.2)`
- `GATE_5_2_USAGE_RULE.md`: declares **Active as of 2026-05-01 (Gate 5.2-R1 hardening pass applied)**

## Known-good Lane D reference

`/Users/syedhaider/Downloads/METAOS_AUDIT_LANE_D_SIGNOUT.zip` available for cross-checking R1 against the canonical Gate 5.2 production package.

## Audit posture

Implementer claims must be verified against actual source. Reports under `reports/gate-5-2-r1/` are inputs to the audit, not evidence on their own.
