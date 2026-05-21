# State 37 — Final Packet Auditor

## Name
FINAL_PACKET_AUDITOR

## Purpose

A simple, independent, context-light final review after the structured gate has already passed.

This state runs AFTER:
- Evidence Adequacy
- Evidence Consistency
- Required Test Set Exactness
- Warning Output Audit
- The five-reviewer cold panel (R1–R5)
- R5 Adjudication
- Final Package Audit
- Canonical Handoff Audit
- Executable checker validation (`tools/check_gate_package.py`)

It runs BEFORE:
- PASS_HANDOFF_COMPLETE
- Any final return to the operator/user

## Why this state exists

Even when every prior reviewer has issued a PASS, packages have escaped to the operator with:
- contradictions between reports
- stale labels or milestone names
- missing raw proof
- blank or non-zero EXIT_CODE
- post-PASS uncaught errors
- dirty repo state
- wrong gate profile selection
- overclaiming live behavior when only infrastructure was built
- a final status stronger than evidence supports

The final packet auditor is the last sanity check, intentionally context-light so it cannot be socialized into the prior conclusions.

## Independence requirements

Run the auditor as a fresh subagent / fresh session / fresh model when possible. The auditor must NOT have prior context from the gate run.

Gate 5.4 mechanically checks only the declared structured provenance inside the report:
- `independence.achieved`
- `auditor_context`
- `auditor_model`
- `auditor_session_id`
- `implementer_session_id`
- `prior_reviewer_session_ids`

This is not cryptographic/runtime proof unless the execution environment supplies trusted session IDs. Missing or conflicting provenance blocks PASS.

For GATE_FULL and GATE_FULL_PLUS_DOMAIN_ADDENDUM, use a Tier 3 / high-effort model for the final auditor when available.

## Reviewer prompt (paste this verbatim into the fresh subagent)

You are the final independent packet auditor.

You did not implement the work.
You did not run the prior reviewers.
Your job is to decide whether this package is safe to return to the operator.

Review the final package, handoff, manifest, raw test outputs, checker report, diff, snapshots, final git status, and gate verdict.

Pass only if the package proves what it claims.

Look especially for:
- contradictions between reports;
- stale labels, fields, milestone names, or status enums;
- missing raw proof;
- blank or nonzero exit codes;
- post-pass uncaught errors;
- dirty repo state;
- wrong gate profile;
- overclaiming live behavior when only infrastructure exists;
- source/test/diff/snapshot mismatch;
- a final status that is stronger than the evidence supports.

Output a fenced YAML or JSON block with this schema:

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

Do not praise.
Do not summarize everything.
Decide pass or fail.

## Output file

The auditor must write `reports/{task_area}/FINAL_PACKET_AUDITOR_REPORT.md` containing the structured fenced block above. Legacy prose-only five-field reports are rejected by Gate 5.4.

## State transitions

- FINAL_PACKET_AUDITOR PASS → PASS_HANDOFF
- FINAL_PACKET_AUDITOR FAIL → FIX_CYCLE
- FINAL_PACKET_AUDITOR HUMAN_DECISION_REQUIRED → BLOCKED_HANDOFF

## Hard rule

PASS_HANDOFF_COMPLETE cannot be reached unless `final_packet_auditor.verdict` is PASS and the declared independence metadata passes mechanical validation.
