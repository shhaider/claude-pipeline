# Output Contract Consistency Audit

```yaml
output_contract_consistency:
  verdict: PASS
  blocking_findings: []
  checked_surfaces:
    - HANDOFF
    - PACKAGE_MANIFEST
    - REQUIRED_TEST_SET_EXACTNESS
    - WARNING_OUTPUT_AUDIT
    - FINAL_PACKET_AUDITOR_REPORT
    - CLAIMS_LEDGER
    - EVIDENCE_LEDGER
    - DOMAIN_ADDENDUM_model_id_validation
  notes: "All output surfaces report the same task_area, the same gate profile, and the same EXIT_CODE:0 raw test output reference."
```
