"""contract node: stub contract-writer that injects gap-analysis findings
into its packet before the real contract_writer (upgrade #4) lands.

blocking_gaps from gap_analysis become MANDATORY ADDITIONAL DELIVERABLES
that the contract MUST cover. advisory_gaps are surfaced as non-mandatory
suggestions.

This stub does not call run_claude — it exposes build_contract_packet as
a pure helper so tests can exercise the injection logic directly.
"""

from __future__ import annotations

import logging

from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


def build_contract_packet(state: PipelineState) -> str:
    """Build the contract packet with gap-analysis findings injected.

    Pure function — safe to call in tests without mocking run_claude.
    """
    intake = state.get("intake") or {}
    research_brief = state.get("research_brief") or "(no research brief available)"
    gap_analysis = state.get("gap_analysis") or {}

    blocking_gaps: list = gap_analysis.get("blocking_gaps") or []
    advisory_gaps: list = gap_analysis.get("advisory_gaps") or []
    gap_summary: str = gap_analysis.get("summary") or ""

    intake_block = "\n".join([
        f"  task_type:          {intake.get('task_type', '?')}",
        f"  complexity_tier:    {intake.get('complexity_tier', '?')}",
        f"  scope_plan:         {intake.get('scope_plan', '?')}",
        f"  right_thing_answer: {intake.get('right_thing_answer', '?')}",
        f"  risk_flags:         {intake.get('risk_flags', [])}",
        f"  wiring_plan:        {intake.get('wiring_plan', '?')}",
        "  acceptance_criteria:",
        *[f"    - {c}" for c in intake.get("acceptance_criteria", [])],
    ])

    if blocking_gaps:
        mandatory_lines = "\n".join(
            f"  - [{g.get('lens', '?')}] {g.get('gap', '')} — {g.get('recommendation', '')}"
            for g in blocking_gaps
        )
    else:
        mandatory_lines = "  (none identified by gap analyst)"

    if advisory_gaps:
        advisory_lines = "\n".join(
            f"  - [{g.get('lens', '?')}] {g.get('gap', '')} — {g.get('recommendation', '')}"
            for g in advisory_gaps
        )
    else:
        advisory_lines = "  (none identified by gap analyst)"

    gap_summary_section = f"\n## Gap analyst summary\n\n{gap_summary}\n" if gap_summary else ""

    return f"""\
## Intake decisions

{intake_block}

## Research brief

{research_brief}
{gap_summary_section}
## MANDATORY ADDITIONAL DELIVERABLES

The adversarial gap analyst identified the following BLOCKING gaps. \
The contract MUST include a deliverable that closes each one:

{mandatory_lines}

## Advisory suggestions (non-mandatory)

The following gaps are ADVISORY — the contract should note them but they \
do not block implementation. Include them as notes or caveats, not as \
required deliverables:

{advisory_lines}
"""


def contract_node(state: PipelineState) -> dict:
    """Stub contract node. Builds the injected packet; does not call run_claude.

    The real contract_writer (upgrade #4) replaces this stub.
    """
    packet = build_contract_packet(state)
    blocking_count = len((state.get("gap_analysis") or {}).get("blocking_gaps") or [])
    advisory_count = len((state.get("gap_analysis") or {}).get("advisory_gaps") or [])
    log.info(
        "contract (stub): packet built (%d blocking gaps injected, %d advisory noted)",
        blocking_count,
        advisory_count,
    )
    # Store the packet under a key downstream stages can inspect.
    # 'contract' is not yet a declared PipelineState key; total=False tolerates extras.
    return {"contract": {"packet": packet}, "error": None}
