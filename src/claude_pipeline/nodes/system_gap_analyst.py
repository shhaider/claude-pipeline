"""system_gap_analyst node: adversarial gap-analysis pass that runs BEFORE
contract writing. Applies 8 named lenses to find unstated dependencies,
silent-failure modes, and architectural smells in the issue framing.

Tier 3 / Opus. Fresh session (no --resume). System prompt loaded via
--append-system-prompt from prompts/metabuilder/35_system_gap_analyst.md.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

# Repo-root-relative path to the role's system-prompt file.
PROMPT_FILE = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder" / "35_system_gap_analyst.md"

MODEL = "claude-opus-4-7"

LENSES = [
    "infrastructure-assumed-but-not-mentioned",
    "silent-failure",
    "cross-cutting-concerns",
    "next-stage-prerequisites",
    "YAGNI-cut",
    "fake-completion",
    "architecture-smell",
    "developer-contract-completeness",
]


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user-facing gap-analysis packet from pipeline state.

    Pure function — safe to call in tests without mocking run_claude.
    """
    intake = state.get("intake") or {}
    research_brief = state.get("research_brief") or "(no research brief available)"

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

    lens_sections = "\n\n".join(
        f"## Lens {i + 1}: {lens}\n"
        f"List every gap you find under this lens. "
        f"For each gap state whether it is BLOCKING or ADVISORY, "
        f"and provide a concrete recommendation to close it."
        for i, lens in enumerate(LENSES)
    )

    return f"""\
## Intake decisions

{intake_block}

## Research brief (codebase anchor)

{research_brief}

## Your task

Apply each of the 8 adversarial lenses below to the intake decisions and research brief above. \
For each lens enumerate every gap you find. A gap is BLOCKING if it will cause the implementation \
to fail or produce a wrong result; it is ADVISORY if it is a risk or smell the contract should note \
but need not block.

{lens_sections}

## Output format

Return VALID JSON only — no prose, no markdown fences:

{{
  "blocking_gaps": [
    {{"lens": "<lens name>", "gap": "<one sentence>", "recommendation": "<one sentence>"}}
  ],
  "advisory_gaps": [
    {{"lens": "<lens name>", "gap": "<one sentence>", "recommendation": "<one sentence>"}}
  ],
  "summary": "<2-3 sentences: overall framing-quality assessment and most critical gap>"
}}
"""


def system_gap_analyst_node(state: PipelineState) -> dict:
    packet = build_gap_analysis_packet(state)
    log.info("system_gap_analyst: invoking claude (adversarial gap-analysis pass, Tier 3 Opus)")

    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        extra_args=["--append-system-prompt", PROMPT_FILE.read_text()],
        model=MODEL,
    )

    if result.is_error:
        msg = result.text or "system_gap_analyst: claude returned is_error=True"
        log.error("system_gap_analyst failed: %s", msg)
        return {"gap_analysis": {}, "error": msg}

    log.info(
        "system_gap_analyst: response received (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        parsed = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.exception("system_gap_analyst: JSON parse failed")
        return {"gap_analysis": {}, "error": f"gap analysis JSON parse failed: {e}"}

    if not isinstance(parsed, dict):
        return {
            "gap_analysis": {},
            "error": f"system_gap_analyst: expected JSON object, got {type(parsed).__name__}",
        }

    # Ensure the expected top-level keys are present; default to empty so
    # downstream consumers can always do .get('blocking_gaps', []).
    gap_analysis: dict = {
        "blocking_gaps": parsed.get("blocking_gaps") or [],
        "advisory_gaps": parsed.get("advisory_gaps") or [],
        "summary": parsed.get("summary") or "",
    }

    log.info(
        "system_gap_analyst done: %d blocking, %d advisory gaps",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
