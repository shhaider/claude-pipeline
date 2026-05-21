# Step 36 — Gate Effectiveness Log

**State machine:** Write `current_state: GATE_EFFECTIVENESS_LOG_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory for GATE_FULL.** Recommended for GATE_STANDARD. Optional for GATE_LITE.

**This step runs after the terminal state (PASS or BLOCKED) — it is a post-run logging step.**

---

## Why this step exists

The gate is a living system. If it catches something important, that should be recorded. If it missed something that was later caught by a human reviewer or ChatGPT, that should also be recorded. If it was overkill for this type of task, that should be recorded too — so the profile selector can be tuned.

Without this log, the gate has no feedback loop. Patterns of misses accumulate silently. Profile selector calibration never improves.

---

## Output file

Copy `GATE_EFFECTIVENESS_LOG_TEMPLATE.md` to `reports/<task_area>/GATE_EFFECTIVENESS_LOG.md`.

Also append a row to the global effectiveness log at `gate/GATE_EFFECTIVENESS_REGISTER.md` (create it if it does not exist).

---

## Fields to record

### Task metadata
- Task ID
- Risk tier
- Gate profile used
- Domain addenda (if any)
- Gate cycles run
- Final verdict

### Issues the gate caught

For each issue the gate found during this run:
- Which state/reviewer found it
- What type of issue it was
- Whether it was a real issue or a false positive

### Issues the gate missed

For each issue later identified by ChatGPT, a human reviewer, or the next implementer:
- What the issue was
- Which state/reviewer should have caught it
- Why it was missed
- Whether a new gate rule would catch it in future

### False positives

Issues the gate flagged that turned out not to be real:
- What was flagged
- Why it was not actually an issue
- Whether the gate rule should be loosened

### Efficiency assessment

Was this gate profile appropriate for this task?
- APPROPRIATE — the profile matched the risk tier
- OVERKILL — a lighter profile would have been sufficient
- UNDERPOWERED — a heavier profile was needed (but not used)

---

## Final Packet Auditor telemetry (Gate 5.3)

After the Final Packet Auditor (state 37) runs, record its outcome in the effectiveness log using the structured block from `GATE_EFFECTIVENESS_LOG_TEMPLATE.md`:

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

These fields exist to:
- measure whether all-reviewer reruns find new issues after fixes (Gate 5.3 rerun policy);
- measure whether the final auditor reduces the human/ChatGPT escape rate;
- identify upstream reviewers who repeatedly miss the same class of issue.

Operators should fill this in after every gate run, including PASS runs — not just failures.

---

## Routing

Write `current_state: GATE_EFFECTIVENESS_LOG_COMPLETE` to CURRENT_STATE.yaml.

This is the final step. The gate run is now fully closed.
