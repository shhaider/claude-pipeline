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

{gap_block}ISSUE #{issue_number}: {issue_title}

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
    lens = g.get("lens", "?")
    desc = g.get("gap") or g.get("description") or ""
    rec = g.get("recommendation", "")
    return f"- [{lens}] {desc}" + (f" — {rec}" if rec else "")


def plan_node(state: PipelineState) -> dict:
    gap = state.get("gap_analysis") or {}
    blocking = gap.get("blocking_gaps") or [] if isinstance(gap, dict) else []
    advisory = gap.get("advisory_gaps") or [] if isinstance(gap, dict) else []

    parts = []
    if blocking:
        parts.append(
            "MANDATORY ADDITIONAL DELIVERABLES (from system_gap_analyst — blocking_gaps "
            "MUST each be covered by at least one stage):\n"
            + "\n".join(_format_gap(g) for g in blocking)
        )
    if advisory:
        parts.append(
            "ADVISORY SUGGESTIONS (from system_gap_analyst — non-mandatory; "
            "incorporate at planner discretion):\n"
            + "\n".join(_format_gap(g) for g in advisory)
        )
    gap_block = ("\n\n".join(parts) + "\n\n") if parts else ""

    prompt = PROMPT_TEMPLATE.format(
        intake_json=json.dumps(state.get("intake", {}), indent=2),
        research_brief=state.get("research_brief", "(no research brief)"),
        issue_number=state["issue_number"],
        issue_title=state.get("issue_title", ""),
        gap_block=gap_block,
    )
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
