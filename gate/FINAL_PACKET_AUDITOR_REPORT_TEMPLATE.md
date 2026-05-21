# Final Packet Auditor Report

```yaml
final_packet_auditor:
  verdict: PASS
  reason: "Concise explanation."
  blockers: []
  required_fix: "NONE"
  rerun_from: "TARGETED_STATE:NA"
  independence:
    achieved: true
    auditor_context: "fresh-subagent"
    auditor_model: "Tier 3 / high-effort"
    auditor_session_id: "auditor-session-id"
    implementer_session_id: "implementer-session-id"
    prior_reviewer_session_ids: []
```

Notes:
- Allowed `verdict`: `PASS`, `FAIL`, `HUMAN_DECISION_REQUIRED`
- Allowed `rerun_from`: `BEGINNING`, `HUMAN_DECISION`, `TARGETED_STATE:<state_name>`
- Allowed `auditor_context`: `fresh-subagent`, `fresh-session`, `fresh-model`, `isolated-session`
- Gate 5.4 mechanically checks only the declared provenance. It is not trusted runtime proof unless the environment supplies trusted session IDs.
