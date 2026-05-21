"""Plan node: convert intake decisions + research brief into an
ordered list of Stages.

Each Stage is the unit of work the CODE node will implement in a single
`claude --print` invocation. Stages have: name, description,
file_touch_map. Order matters — stages run sequentially.

For MVP: a single Claude call produces all stages. For v0.2+ we'll add
the 4-Correction iteration loop around this node.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState, Stage

log = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a software-task planner. You have intake decisions and a research brief. Output a sequence of implementation stages.

INTAKE:
{intake_json}

RESEARCH BRIEF:
{research_brief}

ISSUE #{issue_number}: {issue_title}
{gap_block}
Produce a JSON array of stages. Each stage is one focused unit of work that an implementer can complete in a single coding session.

Rules:
- Each stage must be self-contained: it should produce a working state (tests pass after the stage).
- ``file_touch_map`` must list every file the stage will create, modify, or delete. Be specific (paths).
- Order matters: earlier stages prepare for later ones. Schema/structure first, behaviour second, tests third (unless TDD).
- Tier-1 (trivial) tasks: typically 1-2 stages. Tier-2: 2-5 stages. Tier-3: 5-10 stages.
- If a stage would touch more than ~10 files OR more than ~500 LOC of new code, split it.
- DO NOT plan governance / review / commit stages — those are pipeline nodes, not stages.

JSON shape (array of objects). Output the array ONLY — no prose, no markdown fence:

[
  {{
    "name": "short-kebab-case-name",
    "description": "one or two sentences describing what this stage does and why",
    "file_touch_map": ["path/to/file1.py", "path/to/file2.py"]
  }},
  ...
]

Begin:
"""


def _format_gap(g: dict) -> str:
    """Render one gap object as a bullet line.

    Tolerant of partial shapes: missing keys render as empty strings
    rather than raising, so a malformed gap from the analyst can't
    crash the planner.
    """
    lens = str(g.get("lens", "")).strip()
    gap = str(g.get("gap", "")).strip()
    rec = str(g.get("recommendation", "")).strip()
    lens_prefix = f"[{lens}] " if lens else ""
    rec_suffix = f" — recommendation: {rec}" if rec else ""
    return f"- {lens_prefix}{gap}{rec_suffix}"


def _build_gap_block(gap_analysis: dict | None) -> str:
    """Render blocking gaps as MANDATORY ADDITIONAL DELIVERABLES and
    advisory gaps as non-mandatory suggestions. Returns an empty
    string when gap_analysis is absent or contains no gaps, so the
    surrounding prompt template renders cleanly.
    """
    if not gap_analysis:
        return ""
    blocking = list(gap_analysis.get("blocking_gaps") or [])
    advisory = list(gap_analysis.get("advisory_gaps") or [])
    if not blocking and not advisory:
        return ""
    sections: list[str] = [""]
    if blocking:
        sections.append("## MANDATORY ADDITIONAL DELIVERABLES (from adversarial gap analysis)")
        sections.append(
            "Each item below MUST be covered by at least one stage. These "
            "are blocking gaps surfaced by system_gap_analyst — treat them "
            "as non-negotiable additions to the contract."
        )
        sections.extend(_format_gap(g) for g in blocking)
        sections.append("")
    if advisory:
        sections.append("## Advisory gaps (suggestions, not requirements)")
        sections.append(
            "The following were flagged as advisory by system_gap_analyst. "
            "Consider whether any are worth addressing; they are NOT "
            "mandatory."
        )
        sections.extend(_format_gap(g) for g in advisory)
        sections.append("")
    return "\n".join(sections)


def build_plan_prompt(state: PipelineState) -> str:
    """Render the full planner user-prompt for the given state.

    Exposed as a pure function so tests can assert on the rendered
    string without invoking Claude.
    """
    return PROMPT_TEMPLATE.format(
        intake_json=json.dumps(state.get("intake", {}), indent=2),
        research_brief=state.get("research_brief", "(no research brief)"),
        issue_number=state.get("issue_number", "?"),
        issue_title=state.get("issue_title", ""),
        gap_block=_build_gap_block(state.get("gap_analysis")),
    )


def plan_node(state: PipelineState) -> dict:
    prompt = build_plan_prompt(state)
    log.info("plan: invoking claude")
    result = run_claude(
        prompt,
        cwd=state["worktree_path"],
        timeout_s=300,
    )
    log.info("plan: claude returned (%.1fs, cost=$%.4f)", result.duration_s, result.cost_usd)

    try:
        raw_stages = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"plan parse failed: {e}; text head: {result.text[:300]}"}
    if not isinstance(raw_stages, list):
        return {"error": f"plan: expected JSON array, got {type(raw_stages).__name__}"}
    if not raw_stages:
        return {"error": "plan: claude returned an empty stage list"}

    stages: list[Stage] = []
    for i, s in enumerate(raw_stages):
        if not isinstance(s, dict):
            return {"error": f"plan: stage {i} is not an object"}
        required = {"name", "description", "file_touch_map"}
        if not required.issubset(s):
            return {
                "error": f"plan: stage {i} missing fields {sorted(required - set(s))}",
            }
        stages.append(
            {
                "name": str(s["name"]),
                "description": str(s["description"]),
                "file_touch_map": [str(p) for p in s["file_touch_map"]],
            }
        )
    log.info("plan done: %d stages", len(stages))
    return {"plan": stages, "current_stage_idx": 0, "error": None}
