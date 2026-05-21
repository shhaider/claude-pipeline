"""contract_writer node: define what must exist for this issue.

Ports the first of metabuilder's three plan-lane LLM calls (the
`27_contract_writer.md` system prompt + `buildContractPacket` user
packet). For now this pipeline keeps a single downstream `plan` node
that handles the planner-stage work; this node owns only the contract
half — the structured list of deliverables that the plan must satisfy.

The reason this lives as its own node (rather than being folded into
plan_node) is that it has a sharp, narrow output schema and a clear
upstream dependency on the system_gap_analyst pass: blocking gaps from
gap_analysis are injected here as MANDATORY ADDITIONAL DELIVERABLES,
and advisory gaps ride along as suggestions only.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


def _format_gap_block(
    gaps: list[dict],
    *,
    heading: str,
    framing: str,
) -> str:
    """Render a list of gap dicts under a heading with a framing line."""
    lines: list[str] = [heading, "", framing, ""]
    for i, g in enumerate(gaps, start=1):
        lens = g.get("lens", "?")
        gap = g.get("gap", "")
        rec = g.get("recommendation", "")
        lines.append(f"{i}. **[{lens}]** {gap}")
        if rec:
            lines.append(f"   _Recommendation:_ {rec}")
    return "\n".join(lines)


def build_contract_packet(state: PipelineState) -> str:
    """Build the user packet for the contract_writer LLM call.

    Pure-python; deterministic; safe to unit-test without an LLM.

    When `gap_analysis` is present in state, this packet includes:
      - **blocking_gaps** rendered as MANDATORY ADDITIONAL DELIVERABLES
        — each one becomes a deliverable the contract MUST cover.
      - **advisory_gaps** rendered as SUGGESTED ADDITIONAL DELIVERABLES
        — advice only, not requirements.

    When `gap_analysis` is absent, the packet omits both blocks (the
    contract_writer falls back to plain intake + research framing).
    """
    intake = state.get("intake", {})
    issue_number = state.get("issue_number", "?")
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "")
    research_brief = state.get("research_brief", "(no research brief)")
    gap_analysis = state.get("gap_analysis") or {}
    blocking_gaps = gap_analysis.get("blocking_gaps") or []
    advisory_gaps = gap_analysis.get("advisory_gaps") or []
    gap_summary = gap_analysis.get("summary") or ""

    sections: list[str] = [
        "## Contract Writing Task",
        "",
        "You are acting as **contract_writer**. Produce the structured contract — "
        "the list of deliverables this issue MUST produce — that the downstream "
        "planner will stage and the implementer will build against.",
        "",
        f"**Issue #{issue_number}:** {issue_title}",
        "",
        "**Issue body:**",
        issue_body or "(no body)",
        "",
        "## Intake decisions",
        "",
        "```json",
        json.dumps(intake, indent=2, sort_keys=True),
        "```",
        "",
        "## Research brief",
        "",
        research_brief,
    ]

    if blocking_gaps:
        sections.append("")
        sections.append(
            _format_gap_block(
                blocking_gaps,
                heading="## MANDATORY ADDITIONAL DELIVERABLES (from adversarial gap analysis)",
                framing=(
                    "The system_gap_analyst pass flagged the following as BLOCKING. "
                    "Each one MUST be covered by at least one deliverable in your "
                    "contract output. These are not optional; the contract is "
                    "incomplete without them."
                ),
            )
        )

    if advisory_gaps:
        sections.append("")
        sections.append(
            _format_gap_block(
                advisory_gaps,
                heading="## SUGGESTED ADDITIONAL DELIVERABLES (advisory only)",
                framing=(
                    "The system_gap_analyst pass flagged the following as advisory. "
                    "Consider whether to include them as deliverables; they are "
                    "suggestions, not requirements."
                ),
            )
        )

    if gap_summary:
        sections.append("")
        sections.append("## Gap-analyst summary")
        sections.append("")
        sections.append(gap_summary)

    sections += [
        "",
        "## Output",
        "",
        "Return VALID JSON ONLY — no prose, no markdown fence. Shape:",
        "",
        "{",
        '  "contract_title": "...",',
        '  "deliverables": [',
        '    {"id": "D1", "name": "...", "description": "...", "success_criteria": ["..."], "source_goal": "..."}',
        "  ],",
        '  "ambiguity_flags": [{"goal": "...", "issue": "...", "assumed": "..."}],',
        '  "total_deliverables": <int>,',
        '  "verification": "..."',
        "}",
        "",
        "Begin:",
    ]
    return "\n".join(sections)


def contract_node(state: PipelineState) -> dict:
    """LangGraph node entry point — produces a `contract` dict on state.

    The full contract_writer system prompt (metabuilder's
    `27_contract_writer.md`) is out of scope for this port. This node
    runs the user packet alone for now and stores the structured
    contract for downstream consumption by plan_node.
    """
    packet = build_contract_packet(state)
    log.info("contract: invoking claude")
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
        raw: Any = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "error": (
                f"contract parse failed: {e}; text head: {result.text[:300]}"
            ),
        }
    if not isinstance(raw, dict):
        return {"error": f"contract: expected JSON object, got {type(raw).__name__}"}
    return {"contract": raw, "error": None}
