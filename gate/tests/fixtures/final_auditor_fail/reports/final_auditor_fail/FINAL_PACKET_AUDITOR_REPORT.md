# Final Packet Auditor Report

```yaml
final_packet_auditor:
  verdict: FAIL
  reason: "Manifest self-size is stale and the raw output proof does not support a clean EXIT_CODE:0 finish."
  blockers:
    - "MANIFEST_SELF_SIZE_STALE"
    - "EXIT_CODE_BLANK"
  required_fix: "Regenerate PACKAGE_MANIFEST.md with the correct self-size and rerun the test command to capture a fresh raw output ending with bare EXIT_CODE:0 exact."
  rerun_from: "BEGINNING"
  independence:
    achieved: true
    auditor_context: "fresh-subagent"
    auditor_model: "Tier 3 / high-effort"
    auditor_session_id: "auditor-final-fail"
    implementer_session_id: "implementer-final-fail"
    prior_reviewer_session_ids:
      - "reviewer-r1"
```
