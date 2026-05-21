"""system_gap_analyst node: adversarial pre-lane gap analysis.

Runs before contract authoring. Applies 8 adversarial lenses to the
intake decisions and research brief to surface gaps the planner may have
assumed away. Emits {blocking_gaps, advisory_gaps, summary}.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

OPUS_MODEL = "claude-opus-4-7"

PROMPT_PATH = (
    Path(__file__).resolve().parents[3] / "prompts" / "metabuilder" / "35_system_gap_analyst.md"
)

LENSES = (
    "infrastructure-assumed-but-not-mentioned",
    "silent-failure",
    "cross-cutting-concerns",
    "next-stage-prerequisites",
    "YAGNI-cut",
    "fake-completion",
    "architecture-smell",
    "developer-contract-completeness",
)

USER_PACKET_TEMPLATE = """ISSUE #{issue_number}: {issue_title}

INTAKE DECISIONS:
{intake_json}

RESEARCH BRIEF:
{research_brief}

CODEBASE ANCHOR:
{codebase_anchor}

Apply each of the following 8 adversarial lenses in order. For each lens, identify any gaps present in the plan described above:

{lenses_block}

Return a single JSON object matching the schema in your system prompt. No prose, no markdown fences — JSON only.
"""


def system_gap_analyst_node(state: PipelineState) -> dict:
    intake = state.get("intake") or {}
    research_brief = state.get("research_brief") or ""
    codebase_anchor = state.get("codebase_anchor") or ""
    issue_number = state.get("issue_number")
    issue_title = state.get("issue_title") or ""

    try:
        prompt_body = PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"gap_analysis": None, "error": f"prompt file missing: {PROMPT_PATH}"}

    lenses_block = "\n".join(f"{i + 1}. {lens}" for i, lens in enumerate(LENSES))
    user_packet = USER_PACKET_TEMPLATE.format(
        intake_json=json.dumps(intake, indent=2),
        research_brief=research_brief,
        codebase_anchor=codebase_anchor,
        issue_number=issue_number,
        issue_title=issue_title,
        lenses_block=lenses_block,
    )

    log.info("system_gap_analyst: invoking claude opus")
    try:
        result = run_claude(
            user_packet,
            model=OPUS_MODEL,
            extra_args=["--append-system-prompt", prompt_body],
            timeout_s=600,
        )
    except ClaudeError as e:
        return {"gap_analysis": None, "error": f"claude run failed: {e}"}

    if result.is_error:
        return {"gap_analysis": None, "error": result.text or "claude run failed"}

    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        data = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "gap_analysis": None,
            "error": f"gap_analyst parse failed: {e}; head: {result.text[:300]}",
        }

    if not isinstance(data, dict):
        return {
            "gap_analysis": None,
            "error": f"gap_analyst: expected JSON object, got {type(data).__name__}",
        }

    gap_analysis = {
        "blocking_gaps": data["blocking_gaps"] if isinstance(data.get("blocking_gaps"), list) else [],
        "advisory_gaps": data["advisory_gaps"] if isinstance(data.get("advisory_gaps"), list) else [],
        "summary": str(data.get("summary") or ""),
    }
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
