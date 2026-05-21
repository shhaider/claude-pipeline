"""contract node: convert intake + research + gap_analysis into a
structured deliverables contract that the plan node will then break
into stages.

Ports metabuilder's `contract_writer` lane in the shape required by
the system_gap_analyst pre-lane (issue #9): the user packet MUST
inject `gap_analysis.blocking_gaps` as MANDATORY ADDITIONAL
DELIVERABLES and `gap_analysis.advisory_gaps` as suggestions.

Output shape:
    {
      "contract_title": "...",
      "deliverables": [
        {"id": "D1", "name": "...", "description": "...",
         "success_criteria": ["..."], "source_goal": "..."}
      ],
      "ambiguity_flags": [...],
      "verification": "..."
    }
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

MANDATORY_HEADER = "## MANDATORY ADDITIONAL DELIVERABLES (from adversarial gap analysis)"
ADVISORY_HEADER = "## ADVISORY SUGGESTIONS (from adversarial gap analysis — consider but not required)"


def _format_gap_items(items: list[dict], mandatory: bool) -> list[str]:
    if not items:
        return []
    lines: list[str] = [MANDATORY_HEADER if mandatory else ADVISORY_HEADER]
    if mandatory:
        lines.append(
            "Each item below MUST appear as a deliverable in the contract. The contract is "
            "INCOMPLETE without coverage of every blocking gap."
        )
    else:
        lines.append(
            "Each item below is a suggestion surfaced by the gap pass. Include in the "
            "contract only if you judge it relevant; not required."
        )
    for i, item in enumerate(items, start=1):
        lens = item.get("lens", "")
        gap = item.get("gap", "")
        rec = item.get("recommendation", "")
        prefix = "MANDATORY" if mandatory else "SUGGESTION"
        lines.append(
            f"{i}. [{prefix}] ({lens}) — {gap}"
            + (f"\n   Recommendation: {rec}" if rec else "")
        )
    return lines


def build_contract_packet(state: PipelineState) -> str:
    """Build the user message for the contract_writer LLM call.

    When `gap_analysis` is present in state, this injects:
      - `blocking_gaps` under a MANDATORY ADDITIONAL DELIVERABLES header
        (each becomes a deliverable the contract MUST cover);
      - `advisory_gaps` under an ADVISORY SUGGESTIONS header
        (not marked mandatory).

    No LLM calls happen here — pure string assembly so the packet shape
    is unit-testable.
    """
    intake = state.get("intake", {})
    research_brief = state.get("research_brief", "(no research brief)")
    gap = state.get("gap_analysis") or {}
    blocking = gap.get("blocking_gaps") or []
    advisory = gap.get("advisory_gaps") or []

    parts: list[str] = [
        "## Contract Writer Task",
        "",
        "Convert the framing below into a STRUCTURED CONTRACT — a list of deliverables, "
        "each with success criteria, that downstream planning will break into stages.",
        "",
        f"**Issue #{state.get('issue_number', '?')}: {state.get('issue_title', '')}**",
        "",
        "### Intake decisions",
        "```json",
        json.dumps(intake, indent=2, sort_keys=True),
        "```",
        "",
        "### Research brief",
        research_brief.strip() if research_brief else "(no research brief)",
        "",
    ]

    blocking_block = _format_gap_items(blocking, mandatory=True)
    if blocking_block:
        parts.append("")
        parts.extend(blocking_block)

    advisory_block = _format_gap_items(advisory, mandatory=False)
    if advisory_block:
        parts.append("")
        parts.extend(advisory_block)

    if gap.get("summary"):
        parts.append("")
        parts.append(f"**Gap-analysis summary:** {gap['summary']}")

    parts.extend(
        [
            "",
            "### Output",
            "Return VALID JSON ONLY — no prose, no markdown fence:",
            "",
            '{',
            '  "contract_title": "short title for the work",',
            '  "deliverables": [',
            '    {"id": "D1", "name": "...", "description": "...",',
            '     "success_criteria": ["objectively verifiable criterion"],',
            '     "source_goal": "intake | research | gap-blocking | gap-advisory"}',
            '  ],',
            '  "ambiguity_flags": [{"goal": "...", "issue": "...", "assumed": "..."}],',
            '  "verification": "how completion is judged overall"',
            '}',
            "",
            "Rules:",
            "- Every blocking gap above MUST be covered by at least one deliverable. Mark its "
            "`source_goal` as `gap-blocking`.",
            "- Advisory items MAY be covered; if they are, mark `source_goal` as `gap-advisory`.",
            "- Each deliverable id is a short stable token (D1, D2, ...).",
            "- `success_criteria` entries must be objectively verifiable (a check would pass/fail).",
            "",
            "Begin:",
        ]
    )
    return "\n".join(parts)


def contract_node(state: PipelineState) -> dict:
    """Run the contract_writer LLM call. Tier 3 (Opus) per metabuilder
    port spec — though tier routing isn't enforced in v0.1.0 yet."""
    packet = build_contract_packet(state)
    log.info("contract: invoking claude")
    result = run_claude(
        packet,
        cwd=state["worktree_path"],
        timeout_s=600,
        model="claude-opus-4-7",
    )
    log.info(
        "contract: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        parsed = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"contract parse failed: {e}; text head: {result.text[:300]}"}
    if not isinstance(parsed, dict):
        return {"error": f"contract: expected JSON object, got {type(parsed).__name__}"}

    deliverables = parsed.get("deliverables") or []
    if not isinstance(deliverables, list) or not deliverables:
        return {"error": "contract: claude returned no deliverables"}

    log.info("contract done: %d deliverables", len(deliverables))
    return {"contract": parsed, "error": None}
