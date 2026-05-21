# Output Contract Consistency Audit

**Task area:** [task_area]
**Audit completed at:** [ISO timestamp]
**Auditor:** [agent or operator name]

---

## Purpose

The Output Contract Consistency Audit verifies that every status-bearing surface in the
gate package agrees on milestone labels, artifact names, status enums, and
cross-document field values. Disagreement between surfaces (e.g. HANDOFF.md says "M61C in
progress" while RTM and MANIFEST list it as MERGED) is a `STALE_MILESTONE_LABEL`
contradiction and must block PASS.

---

## Structured verdict (Gate 5.2-R1) — REQUIRED

The Gate 5.2-R1 checker prefers a machine-readable verdict block over prose scanning.
Prose scanning is a fallback that may be confused by negated mentions of blocking
tokens; the structured block makes the auditor's verdict explicit.

```yaml
output_contract_consistency:
  verdict: PASS                  # PASS | FAIL | UNCERTAIN
  blocking_findings: []          # list of blocking-token strings, empty iff verdict=PASS
  checked_surfaces:
    - HANDOFF
    - RUNTIME_SCOPE_CHECK
    - RTM
    - MANIFEST
    - source snapshots
    - tests
    - diff
```

Allowed `blocking_findings` tokens:

- `STALE_CONTRACT_CLAIM`
- `STALE_MILESTONE_LABEL`
- `STALE_FIELD_NAME`
- `STALE_ARTIFACT_NAME`
- `CONTRADICTS_SOURCE`
- `CONTRADICTS_TESTS`
- `BLOCKING`
- `FAIL`

Checker behavior:

| Block state | Result |
|---|---|
| `verdict: PASS` and `blocking_findings: []` | PASS |
| `verdict: PASS` but `blocking_findings: [...]` | FAIL with `OUTPUT_CONTRACT_VERDICT_INCONSISTENT` |
| `verdict: FAIL` (any findings) | FAIL with first finding token |
| `verdict: UNCERTAIN` | FAIL with `OUTPUT_CONTRACT_VERDICT_UNCERTAIN` |
| Verdict value not PASS/FAIL/UNCERTAIN | FAIL with `OUTPUT_CONTRACT_VERDICT_UNKNOWN` |
| No structured block found | Fallback to negation-aware prose scan |

---

## Surfaces compared

For each row, record the value found on each surface. Mark a row PASS if every surface
agrees on the value, FAIL otherwise.

| Field | HANDOFF | RUNTIME_SCOPE_CHECK | RTM | MANIFEST | source snapshots | tests | diff | Verdict |
|---|---|---|---|---|---|---|---|---|
| Milestone label | | | | | | | | |
| Artifact name | | | | | | | | |
| Status enum | | | | | | | | |
| Build SHA | | | | | | | | |
| Test count | | | | | | | | |

---

## Findings

For each blocking finding, document the contradiction:

- **Finding:** [token name]
  - **Affected surfaces:** [list]
  - **Conflict:** [exact strings that disagree]
  - **Required correction:** [what must change before PASS]

If the verdict is PASS with no findings: state explicitly that all surfaces agreed.

---

## Verdict notes (prose)

Optional human-readable summary. The structured YAML block above is the source of truth
for the checker.
