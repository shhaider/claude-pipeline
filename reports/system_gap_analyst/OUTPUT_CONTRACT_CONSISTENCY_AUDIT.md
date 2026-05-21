# Output contract consistency audit

**Task area:** `system_gap_analyst`
**Scope:** Verify that the JSON output contracts in the prompt files match the parsers that consume them.

```yaml
output_contract_consistency:
  verdict: PASS
  checked_surfaces:
    - prompts/metabuilder/35_system_gap_analyst.md (system prompt output schema)
    - src/claude_pipeline/nodes/system_gap_analyst.py::_coerce_finding
    - src/claude_pipeline/nodes/system_gap_analyst.py::system_gap_analyst_node
    - src/claude_pipeline/nodes/contract.py::build_contract_packet (inline schema)
    - src/claude_pipeline/nodes/contract.py::_coerce_deliverable
    - src/claude_pipeline/nodes/contract.py::contract_node
  blocking_findings: []
  audits:
    - prompt: prompts/metabuilder/35_system_gap_analyst.md
      declared_schema:
        blocking_gaps: list of {lens, gap, recommendation}
        advisory_gaps: list of {lens, gap, recommendation}
        summary: str
      consumer: src/claude_pipeline/nodes/system_gap_analyst.py::_coerce_finding + system_gap_analyst_node
      consumer_reads:
        - raw.get("blocking_gaps", []) — read as list
        - raw.get("advisory_gaps", []) — read as list
        - raw.get("summary", "") — read as str
        - each finding's lens, gap, recommendation — read as str
      verdict: ALIGNED — every field the parser reads is declared in the prompt; every field the prompt promises is consumed.
    - prompt: build_contract_packet output schema (inline in contract.py)
      declared_schema:
        contract_title: str
        deliverables: list of {id, name, description, success_criteria, source_goal}
        ambiguity_flags: list of {goal, issue, assumed}
        total_deliverables: int
        verification: str
      consumer: src/claude_pipeline/nodes/contract.py::_coerce_deliverable + contract_node
      consumer_reads: same set
      verdict: ALIGNED
  contradictions: []
```

## Narrative

The system_gap_analyst's prompt-side schema (`prompts/metabuilder/35_system_gap_analyst.md` — output section) names exactly the three fields the Python parser destructures: `blocking_gaps`, `advisory_gaps`, `summary`. Each finding is a `{lens, gap, recommendation}` triple, matching `_coerce_finding`. The lens enum is constrained to the same 8 names asserted in `LENSES`.

The contract_writer's prompt-side schema is inline in `build_contract_packet` (declared in the user packet, not in a separate file). It names `contract_title`, `deliverables[{id, name, description, success_criteria, source_goal}]`, `ambiguity_flags`, `total_deliverables`, `verification`. The `_coerce_deliverable` parser destructures the same fields with the same names. **No drift.**

## Verdict

**PASS — `output_contract_consistency`.**
