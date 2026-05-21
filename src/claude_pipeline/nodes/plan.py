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
import re

from claude_pipeline.claude import run_claude
from claude_pipeline.state import PipelineState, Stage

log = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a software-task planner. You have intake decisions and a research brief. Output a sequence of implementation stages.

INTAKE:
{intake_json}

RESEARCH BRIEF:
{research_brief}

ISSUE #{issue_number}: {issue_title}

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


def _extract_json_array(text: str) -> list:
    """Pull the first balanced JSON array out of Claude's stdout."""
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", text)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == "[":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and start >= 0:
                return json.loads(cleaned[start : i + 1])
    raise ValueError(f"no balanced JSON array found in: {text[:200]!r}")


def plan_node(state: PipelineState) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        intake_json=json.dumps(state.get("intake", {}), indent=2),
        research_brief=state.get("research_brief", "(no research brief)"),
        issue_number=state["issue_number"],
        issue_title=state.get("issue_title", ""),
    )
    log.info("plan: invoking claude")
    result = run_claude(
        prompt,
        cwd=state["worktree_path"],
        timeout_s=300,
    )
    try:
        raw_stages = _extract_json_array(result.stdout)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "error": f"plan parse failed: {e}; stdout head: {result.stdout[:300]}",
        }

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
