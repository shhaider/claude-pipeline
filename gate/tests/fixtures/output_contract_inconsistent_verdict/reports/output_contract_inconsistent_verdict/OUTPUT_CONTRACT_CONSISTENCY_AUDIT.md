# Output Contract Consistency Audit

**Task area:** output_contract_inconsistent_verdict

## Structured verdict (Gate 5.2-R1)

```yaml
output_contract_consistency:
  verdict: PASS
  blocking_findings:
    - STALE_MILESTONE_LABEL
  checked_surfaces:
    - HANDOFF
    - RUNTIME_SCOPE_CHECK
    - RTM
    - MANIFEST
    - source snapshots
    - tests
    - diff
```

## Bug

The auditor wrote PASS but listed a blocking finding. Gate 5.2-R1 must catch this contradiction and block.
