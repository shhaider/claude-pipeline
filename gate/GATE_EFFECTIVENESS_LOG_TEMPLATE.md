# Gate Effectiveness Log

**Task ID:** [task_id]
**Date:** [ISO timestamp]

---

## Task metadata

| Field | Value |
|---|---|
| Risk tier | D0 / D1 / D2 / D2-hot / D3 / D4 |
| Gate profile used | GATE_LITE / GATE_STANDARD / GATE_FULL / GATE_FULL_PLUS |
| Domain addenda | [list or "none"] |
| Gate cycles run | [N] |
| Final verdict | PASS / BLOCKED |
| Final outcome label | [label from overclaim taxonomy] |

---

## Issues the gate caught

| Issue | State/reviewer that found it | Issue type | Real issue or false positive? |
|---|---|---|---|
| [description] | [R2 / Step 15 / Step 17 / etc.] | [overclaim / missing evidence / stale artifact / etc.] | REAL / FALSE_POSITIVE |

Total issues caught: [count]

---

## Issues the gate missed

These were caught later by a human reviewer, ChatGPT, or the next implementer:

| Issue | When caught | Who caught it | Should have been caught by | Why missed | New rule added? |
|---|---|---|---|---|---|
| [description] | [sprint / review date] | [human / ChatGPT / next implementer] | [step/reviewer] | [reason] | YES / NO |

Total missed: [count]

---

## False positives

Issues the gate flagged that were not real:

| Flagged issue | State/reviewer | Why it was not real | Rule adjustment needed? |
|---|---|---|---|
| [description] | [step/reviewer] | [explanation] | YES / NO |

Total false positives: [count]

---

## New rules added as a result of this run

| Rule | Added to | Effect |
|---|---|---|
| [rule description] | [gate file] | [what it catches going forward] |

---

## Efficiency assessment

```
APPROPRIATE | OVERKILL | UNDERPOWERED
```

**Rationale:** [one paragraph — was this the right level of gate for this task?]

**Profile recommendation for similar tasks in future:** [GATE_LITE / GATE_STANDARD / GATE_FULL]

---

## Append to GATE_EFFECTIVENESS_REGISTER.md

```
| [task_id] | [risk_tier] | [profile] | [cycles] | [verdict] | [caught] | [missed] | [FP] | [assessment] |
```

---

## Final Packet Auditor (Gate 5.3)

This section measures whether the independent final auditor (state 37) caught issues that earlier reviewers missed, and whether full-restart reruns surfaced new issues after fixes. Operators must fill this in after every gate run, not just failures.

```yaml
final_packet_auditor:
  verdict: PASS | FAIL | HUMAN_DECISION_REQUIRED | NOT_RUN
  blockers: []
  were_blockers_missed_by_prior_reviewers: true|false|n/a
  reviewer_states_that_should_have_caught_it: []
  fix_required_full_restart: true|false
  after_fix_did_previous_reviewer_fail_on_rerun: true|false|unknown
  human_or_chatgpt_later_found_issue: true|false|unknown
  issue_class_added_to_gate: true|false
  notes: ""
```

**Why this matters**

- Measures whether all-reviewer reruns find new issues after fixes — without this, the rerun policy cannot be calibrated.
- Measures whether the final auditor reduces human/ChatGPT escape rate — without this, the auditor's marginal value cannot be assessed.
- If `were_blockers_missed_by_prior_reviewers: true` and `reviewer_states_that_should_have_caught_it` is non-empty for several runs, the affected upstream reviewers need rule changes.
- If `human_or_chatgpt_later_found_issue: true` and `verdict: PASS`, the auditor missed something — log it as a new issue class.
