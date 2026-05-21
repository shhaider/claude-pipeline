# Gate 5.4 Baseline

- Canonical working path: `/Users/syedhaider/Downloads/gate`
- Task: `Gate 5.4 known-issue closure — checker hardening and regression fixtures`
- Required profile context: `GATE_FULL_PLUS_DOMAIN_ADDENDUM`, `D4`, `gate_change`
- Baseline checker surface inspected first:
  - `tools/check_gate_package.py`
  - `tests/test_check_gate_package.py`
  - `tests/fixtures/`
  - `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`
  - `GATE_PROFILES.md`
  - `GATE_PROFILE_SELECTOR.md`
  - `18_GATE_PROFILE_SELECTION.md`
  - `37_FINAL_PACKET_AUDITOR.md`
  - `FINAL_PACKET_AUDITOR_REPORT_TEMPLATE.md`
  - `WARNING_OUTPUT_AUDIT_TEMPLATE.md`
  - `GATE_5_3_USAGE_RULE.md`
- Baseline test command: `python3 -m pytest -q tests/test_check_gate_package.py`
- Baseline result before Gate 5.4 edits: `44 passed in 3.42s`
- Legacy self-test entrypoint before Gate 5.4 edits: `python3 tests/test_check_gate_package.py`
- Legacy result before Gate 5.4 edits: `44 passed, 0 failed`
- Known issues closed in this task:
  1. Final-auditor independence is now mechanically verified against declared structured provenance.
  2. Final-auditor report parsing now requires structured fenced YAML/JSON instead of regex-only prose.
  3. `GATE_FULL_PLUS_DOMAIN_ADDENDUM` now enforces parsed `domain_addenda` source/proof files.
  4. EXIT_CODE parsing is now fence-aware.
  5. Dirty git-status path parsing no longer trims the first path character.
  6. `EXIT_CODE_CONFLICTING` and `EXIT_CODE_NON_NUMERIC` now have regression fixtures.
  7. `NOT_APPLICABLE` reason validation is stricter against placeholders and invisible text.
  8. Warning-audit parsing now supports structured verdicts and stronger prose fallback scanning.
