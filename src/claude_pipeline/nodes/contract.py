"""Contract writer node — locks scope by translating the intake's
acceptance criteria + research evidence + gap_analysis output into a
named-deliverable contract.

Runs AFTER system_gap_analyst (which produced blocking_gaps and
advisory_gaps) and BEFORE pack_planner. Blocking gaps are injected as
MANDATORY ADDITIONAL DELIVERABLES — each one becomes a deliverable the
contract MUST cover. Advisory gaps appear under SUGGESTIONS only.

The packet builder is a pure function (no LLM, no I/O) so tests can
exercise the injection logic without invoking Claude.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


def _format_gap_block(gaps: list[dict], header: str, mandatory: bool) -> str:
    """Format a list of gap dicts as a labeled block. Returns "" when
    gaps is empty so callers can short-circuit the section header."""
    if not gaps:
        return ""
    lines = [f"# {header}"]
    if mandatory:
        lines.append("Each gap below MUST become a deliverable that the contract covers.")
    else:
        lines.append(
            "The following are NOT mandatory; include only if they materially improve the contract.",
        )
    for i, g in enumerate(gaps, start=1):
        lens = g.get("lens", "unknown")
        gap = g.get("gap", "")
        rec = g.get("recommendation", "")
        lines.append(f"  {i}. [{lens}] {gap}")
        if rec:
            lines.append(f"     Recommendation: {rec}")
    return "\n".join(lines)


def build_contract_packet(
    intake: dict,
    research_brief: str | None,
    gap_analysis: dict | None,
    issue_title: str = "",
    issue_number: int | None = None,
) -> str:
    """Build the contract_writer user packet.

    Safe when gap_analysis is None or missing keys — no MANDATORY or
    SUGGESTIONS block is emitted in that case. This is the silent-failure
    guard exercised by test_contract_packet_safe_when_gap_analysis_missing.
    """
    intake_json = json.dumps(intake or {}, indent=2)
    acceptance = intake.get("acceptance_criteria", []) if intake else []
    primary = "\n".join(f"  - {c}" for c in acceptance) or "  (no acceptance criteria in intake)"

    blocking = (gap_analysis or {}).get("blocking_gaps") or []
    advisory = (gap_analysis or {}).get("advisory_gaps") or []

    mandatory_block = _format_gap_block(
        blocking, "MANDATORY ADDITIONAL DELIVERABLES", mandatory=True,
    )
    suggestions_block = _format_gap_block(advisory, "SUGGESTIONS", mandatory=False)

    issue_header = ""
    if issue_number is not None or issue_title:
        issue_header = f"# ISSUE #{issue_number}: {issue_title}\n\n"

    sections = [
        f"{issue_header}You are the CONTRACT WRITER. Lock scope by emitting a structured contract.",
        "# PRIMARY GOAL (from intake acceptance criteria — every item MUST be a deliverable)",
        primary,
        "# INTAKE DECISIONS",
        intake_json,
        "# RESEARCH BRIEF (evidence)",
        research_brief or "(no research brief)",
    ]
    if mandatory_block:
        sections.append(mandatory_block)
    if suggestions_block:
        sections.append(suggestions_block)

    closing = [
        "# REQUIRED OUTPUT",
        "Return ONLY a JSON object (no prose, no markdown fence):",
        "",
        "{",
        '  "contract_title": "...",',
        '  "deliverables": [',
        '    {"id":"D1","name":"...","description":"...","success_criteria":["..."],"source_goal":"..."}',
        "  ],",
        '  "ambiguity_flags": [],',
        '  "total_deliverables": 0,',
        '  "verification": "..."',
        "}",
        "",
        "Every PRIMARY GOAL item must map to at least one deliverable.",
    ]
    if mandatory_block:
        closing.append(
            "Every item under MANDATORY ADDITIONAL DELIVERABLES above must also map to at least one deliverable.",
        )
    if suggestions_block:
        closing.append(
            "Items under the suggestion section above may or may not be included — at your discretion.",
        )
    sections.append("\n".join(closing))
    return "\n\n".join(sections)


def contract_node(state: PipelineState) -> dict:
    """Run the contract writer LLM call. Returns {'contract': {...}}."""
    intake = state.get("intake", {})
    research_brief = state.get("research_brief", "")
    gap_analysis = state.get("gap_analysis")  # may be None

    if not intake:
        return {
            "error": "contract_node: no intake in state — contract writer requires intake decisions",
        }

    packet = build_contract_packet(
        intake=intake,
        research_brief=research_brief,
        gap_analysis=gap_analysis,
        issue_title=state.get("issue_title", ""),
        issue_number=state.get("issue_number"),
    )

    log.info(
        "contract: invoking claude (blocking_gaps=%d, advisory_gaps=%d)",
        len((gap_analysis or {}).get("blocking_gaps", [])),
        len((gap_analysis or {}).get("advisory_gaps", [])),
    )
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
    )
    log.info(
        "contract: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        contract = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"contract parse failed: {e}; text head: {result.text[:300]}"}
    if not isinstance(contract, dict):
        return {"error": f"contract: expected JSON object, got {type(contract).__name__}"}

    log.info("contract done: %d deliverables", len(contract.get("deliverables", [])))
    return {"contract": contract, "error": None}
