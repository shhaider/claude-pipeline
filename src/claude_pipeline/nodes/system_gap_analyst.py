"""System Gap Analyst node — adversarial pre-lane between research and contract.

Ports the metabuilder `system_gap_analyst` role to v0.4. Applies 8 named
lenses to the planning request + research brief and surfaces blocking /
advisory gaps. The downstream contract node injects blocking gaps as
MANDATORY ADDITIONAL DELIVERABLES.

System prompt = the canonical role file shipped at
`src/claude_pipeline/prompts/35_system_gap_analyst.md`, loaded via
`--append-system-prompt`.

NOTE on CLI flag limitations: the issue specifies temperature 0.2 and
max_tokens 8192. Claude Code's `claude --print` wrapper does not currently
expose `--temperature` or `--max-tokens`. We declare the intent in the
packet header (so the model sees the constraint) and pass `model='opus'`
for tier-3 selection; numeric knobs require a future SDK switch.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "What does this request assume already exists in the codebase that may not?",
    ),
    (
        "silent-failure",
        "What would pass tests and look done but fail in production because a supporting piece was left out?",
    ),
    (
        "cross-cutting-concerns",
        "Error paths, observability, CLI entrypoints, test layers, logging — what does the request ignore?",
    ),
    (
        "next-stage-prerequisites",
        "What decision in this stage is load-bearing for the next stage that the request skips?",
    ),
    (
        "YAGNI-cut",
        "What could be added but should not — gold-plating to cut.",
    ),
    (
        "fake-completion",
        "What could be superficially completed — stub returning hardcoded values, presence-only test — but the actual contract is not satisfied?",
    ),
    (
        "architecture-smell",
        "What's the biggest architectural mistake or premature abstraction in this direction?",
    ),
    (
        "developer-contract-completeness",
        "Does the request name required fields, allowed/forbidden state transitions, system-level invariants, and failure conditions? Flag if absent.",
    ),
]

ROLE_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "35_system_gap_analyst.md"


def _format_codebase_anchor(research_packet: dict | None, research_brief: str | None) -> str:
    """Build the codebaseAnchor block from research output.

    Prefers structured fields (sources_consulted, implementation_details);
    falls back to the legacy research_brief string when those are absent.
    """
    if research_packet:
        srcs = research_packet.get("sources_consulted") or []
        impls = research_packet.get("implementation_details") or []
        lines: list[str] = []
        if srcs:
            lines.append("Sources consulted:")
            lines.extend(f"  - {s}" for s in srcs)
        if impls:
            lines.append("Implementation details:")
            lines.extend(f"  - {d}" for d in impls)
        if lines:
            return "\n".join(lines)
    if research_brief:
        return f"(no structured research packet — embedded brief follows)\n\n{research_brief}"
    return "(no codebase anchor available)"


def build_gap_analysis_packet(
    intake: dict,
    research_brief: str | None,
    research_packet: dict | None = None,
) -> str:
    """Build the user packet for the system_gap_analyst LLM call.

    Mirrors metabuilder's buildGapAnalysisPacket: intake decisions +
    research findings + codebaseAnchor block + the 8 named lenses spelled
    out for the model.
    """
    intake_json = json.dumps(intake or {}, indent=2)
    anchor = _format_codebase_anchor(research_packet, research_brief)
    lens_block = "\n".join(
        f"  {i+1}. **{name}** — {desc}"
        for i, (name, desc) in enumerate(LENSES)
    )
    return f"""SYSTEM GAP ANALYST — ADVERSARIAL PRE-LANE

You are reviewing a planning request BEFORE the contract is written.
Run the 8 adversarial lenses below and produce a structured JSON gap list.

(Model knobs the wrapper cannot enforce: temperature=0.2, max_tokens=8192. Reason slowly.)

# INTAKE DECISIONS
{intake_json}

# RESEARCH BRIEF
{research_brief or "(no research brief)"}

# CODEBASE ANCHOR
{anchor}

# THE 8 ADVERSARIAL LENSES
Apply each lens to the request. For every concrete gap, label it with the lens it came from.

{lens_block}

# REQUIRED OUTPUT
Return ONLY a single JSON object — no prose, no markdown fence — matching:

{{
  "gaps": [
    {{
      "id": "gap_001",
      "lens": "<one of the 8 lens names above, verbatim>",
      "gap": "<what is missing>",
      "recommendation": "<add to scope | defer | no action>",
      "priority": "blocking | important | optional"
    }}
  ],
  "analyst_summary": "<2-3 sentences naming the single biggest blind spot>"
}}

If no gaps are found, return gaps: [] with an analyst_summary stating so.
"""


def _normalize_gap_list(raw: dict) -> dict:
    """Translate the role-prompt's {gaps[], analyst_summary} shape into
    the node's {blocking_gaps, advisory_gaps, summary} shape that
    downstream consumers (contract_node) expect.

    priority == "blocking" → blocking_gaps[]; everything else (including
    "important", "optional", or missing) → advisory_gaps[].
    """
    gaps = raw.get("gaps") or []
    blocking: list[dict] = []
    advisory: list[dict] = []
    for g in gaps:
        if not isinstance(g, dict):
            continue
        entry = {
            "lens": g.get("lens", "unknown"),
            "gap": g.get("gap") or g.get("description") or "",
            "recommendation": g.get("recommendation") or g.get("recommended_action") or "",
        }
        prio = (g.get("priority") or "").strip().lower()
        if prio == "blocking":
            blocking.append(entry)
        else:
            advisory.append(entry)
    return {
        "blocking_gaps": blocking,
        "advisory_gaps": advisory,
        "summary": raw.get("analyst_summary") or raw.get("summary") or "",
    }


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial pre-lane. Returns {'gap_analysis': {...}}."""
    intake = state.get("intake", {})
    research_brief = state.get("research_brief", "")
    research_packet = state.get("research_packet")  # optional, forward-compat

    if not research_brief and not research_packet:
        return {
            "error": "system_gap_analyst: no research_brief or research_packet in state — gap analysis requires research input",
        }

    packet = build_gap_analysis_packet(intake, research_brief, research_packet)

    if not ROLE_PROMPT_PATH.exists():
        return {"error": f"system_gap_analyst: role prompt not found at {ROLE_PROMPT_PATH}"}

    log.info("system_gap_analyst: invoking claude (model=opus, fresh session)")
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        model="opus",
        extra_args=["--append-system-prompt", str(ROLE_PROMPT_PATH)],
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "error": f"system_gap_analyst parse failed: {e}; text head: {result.text[:300]}",
        }
    if not isinstance(raw, dict):
        return {
            "error": f"system_gap_analyst: expected JSON object, got {type(raw).__name__}",
        }

    gap_analysis = _normalize_gap_list(raw)
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
