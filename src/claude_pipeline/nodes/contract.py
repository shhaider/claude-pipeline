"""contract_writer node — converts the intake decisions + research brief
into a structured contract (deliverables + verification + ambiguity
flags) that the planner will route into stages.

Adversarial pre-lane integration: when ``gap_analysis`` is present in
state, every entry in ``gap_analysis.blocking_gaps`` is injected into
the user packet as a MANDATORY ADDITIONAL DELIVERABLE that the contract
MUST cover. Entries in ``advisory_gaps`` are included as SUGGESTIONS
only — the contract writer may incorporate them or note them as
deferred.

This is a partial port of metabuilder's ``contract_writer`` role; the
full port (verbatim 27_contract_writer.md system prompt + full
buildContractPacket) is a separate upgrade issue. What lives here is
the integration seam for system_gap_analyst output.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import Contract, ContractDeliverable, PipelineState

log = logging.getLogger(__name__)


def _format_blocking_gaps(gaps: list[dict]) -> str:
    if not gaps:
        return ""
    lines = [
        "## MANDATORY ADDITIONAL DELIVERABLES (from system_gap_analyst)",
        "",
        (
            "The adversarial gap analyst surfaced the following BLOCKING gaps. "
            "Each one MUST become a deliverable in the contract. Do NOT drop "
            "them, do NOT downgrade them to suggestions, do NOT merge them "
            "into existing deliverables in a way that loses the specific "
            "concern."
        ),
        "",
    ]
    for i, g in enumerate(gaps, start=1):
        lines.append(
            f"{i}. **[lens: {g.get('lens', '?')}]** {g.get('gap', '')}\n"
            f"   - Required action: {g.get('recommendation', '')}"
        )
    return "\n".join(lines)


def _format_advisory_gaps(gaps: list[dict]) -> str:
    if not gaps:
        return ""
    lines = [
        "## Advisory suggestions (from system_gap_analyst)",
        "",
        (
            "The following ADVISORY gaps are NOT mandatory. Consider each: "
            "either incorporate it, explicitly defer it with reasoning, or "
            "decline it. These are suggestions, not requirements."
        ),
        "",
    ]
    for i, g in enumerate(gaps, start=1):
        lines.append(
            f"{i}. _[lens: {g.get('lens', '?')}]_ {g.get('gap', '')}\n"
            f"   - Suggestion: {g.get('recommendation', '')}"
        )
    return "\n".join(lines)


def build_contract_packet(state: PipelineState) -> str:
    """Build the user message for the contract_writer LLM call.

    When ``gap_analysis`` is present in state, blocking gaps are
    injected as MANDATORY ADDITIONAL DELIVERABLES and advisory gaps as
    SUGGESTIONS.
    """
    intake = state.get("intake", {}) or {}
    research_brief = state.get("research_brief", "") or ""
    gap_analysis = state.get("gap_analysis", {}) or {}
    blocking = list(gap_analysis.get("blocking_gaps", []) or [])
    advisory = list(gap_analysis.get("advisory_gaps", []) or [])

    parts = [
        "## Contract-writing task",
        "",
        (
            "You are acting as **contract_writer**. Convert the intake "
            "decisions + research brief into a structured contract of "
            "deliverables that the pack_planner will route into stages."
        ),
        "",
        f"**Issue #{state.get('issue_number', '?')}: "
        f"{state.get('issue_title', '(no title)')}**",
        "",
        "## Intake decisions",
        "```json",
        json.dumps(intake, indent=2),
        "```",
        "",
        "## Research brief",
        research_brief or "(no research brief)",
    ]

    blocking_block = _format_blocking_gaps(blocking)
    if blocking_block:
        parts += ["", blocking_block]

    advisory_block = _format_advisory_gaps(advisory)
    if advisory_block:
        parts += ["", advisory_block]

    parts += [
        "",
        "## Output",
        (
            "Return VALID JSON ONLY — no preamble, no fence. Shape:"
        ),
        "",
        "```",
        "{",
        "  \"contract_title\": \"...\",",
        "  \"deliverables\": [",
        "    {\"id\": \"D1\", \"name\": \"...\", \"description\": \"...\",",
        "     \"success_criteria\": [\"...\"], \"source_goal\": "
        "\"intake|research|gap_analysis_blocking\"}",
        "  ],",
        "  \"ambiguity_flags\": [{\"goal\": \"...\", \"issue\": \"...\", "
        "\"assumed\": \"...\"}],",
        "  \"total_deliverables\": 0,",
        "  \"verification\": \"how a reviewer will check this contract is "
        "satisfied\"",
        "}",
        "```",
        "",
        (
            "Each blocking gap above MUST appear as at least one deliverable "
            "with `source_goal: \"gap_analysis_blocking\"`."
        ),
    ]
    return "\n".join(parts)


def _coerce_deliverable(raw: object) -> ContractDeliverable | None:
    if not isinstance(raw, dict):
        return None
    return {
        "id": str(raw.get("id", "")),
        "name": str(raw.get("name", "")),
        "description": str(raw.get("description", "")),
        "success_criteria": [
            str(c) for c in raw.get("success_criteria", []) or []
        ],
        "source_goal": str(raw.get("source_goal", "")),
    }


def contract_node(state: PipelineState) -> dict:
    """Run the contract_writer pass. Tier 3 (Opus).

    Note: spec calls for T=0.2 / max_tokens=8192. The `claude --print`
    CLI does not expose those as flags (verified via `claude --help`);
    they are implicit until we route through the SDK directly.
    """
    packet = build_contract_packet(state)
    log.info("contract: invoking claude (Opus)")
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        model="claude-opus-4-7",
    )
    log.info(
        "contract: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "error": (
                f"contract parse failed: {e}; text head: {result.text[:300]}"
            )
        }
    if not isinstance(raw, dict):
        return {"error": f"contract: expected JSON object, got {type(raw).__name__}"}

    deliverables = [
        d
        for d in (_coerce_deliverable(x) for x in raw.get("deliverables", []) or [])
        if d is not None
    ]
    contract: Contract = {
        "contract_title": str(raw.get("contract_title", "")),
        "deliverables": deliverables,
        "ambiguity_flags": list(raw.get("ambiguity_flags", []) or []),
        "total_deliverables": int(raw.get("total_deliverables", len(deliverables))),
        "verification": str(raw.get("verification", "")),
    }
    log.info("contract done: %d deliverables", len(deliverables))
    return {"contract": contract, "error": None}
