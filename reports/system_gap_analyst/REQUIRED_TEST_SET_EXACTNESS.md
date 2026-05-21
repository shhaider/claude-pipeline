# Required test set exactness

**Task area:** `system_gap_analyst`
**Raw artifact for all assertions below:** `raw/pytest.txt` (EXIT_CODE:0, 9 PASSED).

## Required test set (from issue body §4)

Required minimum: 4 tests. The four required cases (a–d) and their implementing test functions are listed below in prose to avoid markdown-table raw-output collision with the gate checker's `register_raw_ref` parser.

- **(a) packet contains all 8 lenses** — implemented by `test_gap_packet_contains_all_eight_lenses` in `tests/test_system_gap_analyst.py`.
- **(b) packet includes intake + research** — implemented by `test_gap_packet_includes_intake_decisions` and `test_gap_packet_includes_research_brief`.
- **(c) blocking gaps get injected into contract input** — implemented by `test_blocking_gaps_injected_as_mandatory_into_contract_packet`.
- **(d) advisory gaps present but not marked mandatory** — implemented by `test_advisory_gaps_injected_as_suggestions_not_mandatory`.

## Additional tests (over the required 4)

- `test_gap_packet_lenses_are_the_metabuilder_eight` — pins LENSES set equal to the metabuilder 8-name set.
- `test_gap_packet_includes_issue_identifier` — pins issue # + title surfaced in packet.
- `test_blocking_gaps_absent_when_gap_analysis_empty` — pins that empty gap arrays don't emit empty MANDATORY/Advisory headers.
- `test_contract_packet_works_without_gap_analysis_key` — pins backwards-compat for state resumed from before upgrade.

## Run command and exactness

```yaml
required_test_set_exactness:
  command: "python3 -m pytest -v tests/test_system_gap_analyst.py"
  raw_artifact: raw/pytest.txt
  required_test_count: 4
  actual_collected: 9
  actual_passed: 9
  actual_failed: 0
  missing_required: []
  excluded_by_pattern: []
  verdict: PASS
```

All 4 required tests collected and ran. No required test missing from run. No required test excluded by pattern. Five bonus tests also pass.

## Verdict

**PASS — `required_test_set_exactness`.**
