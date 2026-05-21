# Final Packet Auditor Report

```yaml
final_packet_auditor:
  verdict: HUMAN_DECISION_REQUIRED
  reason: "A human operator decision is needed because the selected gate profile may be too weak for the actual scope."
  blockers:
    - "WRONG_GATE_PROFILE_SUSPECTED"
  required_fix: "Operator must reclassify the task and re-run the gate at the correct profile."
  rerun_from: "HUMAN_DECISION"
  independence:
    achieved: true
    auditor_context: "fresh-subagent"
    auditor_model: "Tier 3 / high-effort"
    auditor_session_id: "auditor-human-decision"
    implementer_session_id: "implementer-human-decision"
    prior_reviewer_session_ids: []
```
