"""system_gap_analyst node: adversarial pre-lane gap analysis.

Runs AFTER research and BEFORE plan. Applies 8 named adversarial lenses
to find unstated dependencies, silent-failure modes, and architectural
smells in the intake+research framing.

Output: gap_analysis = {blocking_gaps, advisory_gaps, summary}. Persisted
to PipelineState and consumed by plan_node which injects blocking_gaps
as MANDATORY ADDITIONAL DELIVERABLES.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

OPUS_MODEL = "claude-opus-4-7"

# Resolve repo-root/prompts/metabuilder/35_system_gap_analyst.md
# __file__ → .../src/claude_pipeline/nodes/system_gap_analyst.py
# parents[3] → repo root
PROMPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "prompts" / "metabuilder" / "35_system_gap_analyst.md"
)

# Wire-protocol order — DO NOT change these strings or their order.
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


def _build_codebase_anchor(state: PipelineState) -> str:
    """Best-effort codebase anchor: drawn from research output.

    The current `research_node` returns a free-form markdown brief, not
    a structured object with `sources_consulted`/`implementation_details`
    fields (those land when research is split per metabuilder roadmap
    item #3). For now, surface what we have: repo + worktree + research
    brief excerpt.
    """
    repo = state.get("repo", "?")
    worktree = state.get("worktree_path", "?")
    brief = state.get("research_brief", "")
    return f"REPO: {repo}\nWORKTREE: {worktree}\n\nRESEARCH BRIEF EXCERPT:\n{brief}"


USER_PACKET_TEMPLATE = """ISSUE #{issue_number}: {issue_title}

INTAKE DECISIONS:
{intake_json}

RESEARCH BRIEF:
{research_brief}

CODEBASE ANCHOR:
{codebase_anchor}

Apply each of the following 8 adversarial lenses in order. For every lens,
identify any gaps that are present in the framing above. Return them in the
JSON schema described in your system prompt.

LENSES:
{lenses_block}

Return a single JSON object matching the schema in your system prompt. No
prose, no markdown fences — JSON only.
"""


def system_gap_analyst_node(state: PipelineState) -> dict:
    intake = state.get("intake") or {}
    research_brief = state.get("research_brief") or "(no research brief)"
    issue_number = state.get("issue_number", "?")
    issue_title = state.get("issue_title", "")

    try:
        prompt_body = PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"error": f"system_gap_analyst: prompt file missing at {PROMPT_PATH}"}

    lenses_block = "\n".join(f"{i+1}. {lens}" for i, lens in enumerate(LENSES))
    user_packet = USER_PACKET_TEMPLATE.format(
        issue_number=issue_number,
        issue_title=issue_title,
        intake_json=json.dumps(intake, indent=2),
        research_brief=research_brief,
        codebase_anchor=_build_codebase_anchor(state),
        lenses_block=lenses_block,
    )

    log.info("system_gap_analyst: invoking claude (Tier-3 Opus, fresh session)")
    try:
        result = run_claude(
            user_packet,
            cwd=state.get("worktree_path"),
            model=OPUS_MODEL,
            extra_args=["--append-system-prompt", prompt_body],
            timeout_s=600,
        )
    except ClaudeError as e:
        return {"error": f"system_gap_analyst: claude failed: {e}"}

    if result.is_error:
        return {"error": f"system_gap_analyst: claude returned soft error: {result.text[:300]}"}

    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        data = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"system_gap_analyst parse failed: {e}; head: {result.text[:300]}"}
    if not isinstance(data, dict):
        return {"error": f"system_gap_analyst: expected JSON object, got {type(data).__name__}"}

    gap_analysis = {
        "blocking_gaps": data.get("blocking_gaps") if isinstance(data.get("blocking_gaps"), list) else [],
        "advisory_gaps": data.get("advisory_gaps") if isinstance(data.get("advisory_gaps"), list) else [],
        "summary": str(data.get("summary") or ""),
    }
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
