"""Code node: implement one stage from the plan.

This is the heavy node. Claude Code reads its own prompt + research +
intake, then uses its native tools (Read/Edit/Write/Bash) to modify code
in the worktree.

The node runs ONE stage per invocation. After the stage completes,
graph.py advances ``current_stage_idx`` and re-enters this node until
all stages are done.
"""

from __future__ import annotations

import logging

from claude_pipeline.claude import run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are implementing one stage of a planned software change. The worktree at your current directory is an isolated checkout. You have Read / Edit / Write / Bash / Glob / Grep tools.

CONTEXT (from earlier pipeline phases):

INTAKE:
- Task type:    {task_type}
- Tier:         {complexity_tier}
- Acceptance:   {acceptance_criteria_bullets}

RESEARCH BRIEF (you read the code in this brief; rely on it):
{research_brief}

THE STAGE YOU ARE IMPLEMENTING (stage {stage_idx} of {stage_count}):

Stage name:        {stage_name}
Description:       {stage_description}
File touch map:    {stage_files_bullets}

PRIOR STAGES (already implemented, do not redo):
{prior_stages_bullets}

Rules:
- Only modify files in the file_touch_map. Reading other files is fine.
- Match the existing code's conventions (naming, formatting, error handling).
- If you must touch a file NOT in the touch map, do it but note it clearly at the end.
- DO NOT commit yet. The pipeline's commit node handles that.
- DO NOT run pytest / npm test unless the description asks you to.

When done, finish with one paragraph summarising what you changed and why. No special markers needed — your final message body is what the pipeline records as the stage summary.
"""


def code_node(state: PipelineState) -> dict:
    plan = state.get("plan", [])
    idx = state.get("current_stage_idx", 0)
    if idx >= len(plan):
        return {"error": f"code: current_stage_idx {idx} out of range (plan has {len(plan)})"}

    stage = plan[idx]
    intake = state.get("intake", {})
    prior = plan[:idx]

    prompt = PROMPT_TEMPLATE.format(
        task_type=intake.get("task_type", "?"),
        complexity_tier=intake.get("complexity_tier", "?"),
        acceptance_criteria_bullets="\n".join(
            f"  - {c}" for c in intake.get("acceptance_criteria", [])
        ),
        research_brief=state.get("research_brief", "(none)"),
        stage_idx=idx + 1,
        stage_count=len(plan),
        stage_name=stage.get("name", ""),
        stage_description=stage.get("description", ""),
        stage_files_bullets="\n".join(
            f"  - {f}" for f in stage.get("file_touch_map", [])
        )
        or "  (no files declared)",
        prior_stages_bullets="\n".join(
            f"  - {s['name']}: {s['description']}" for s in prior
        )
        or "  (none — this is the first stage)",
    )
    log.info(
        "code: invoking claude on stage %d/%d (%s)",
        idx + 1,
        len(plan),
        stage.get("name", ""),
    )
    result = run_claude(
        prompt,
        cwd=state["worktree_path"],
        timeout_s=1800,  # 30 min ceiling for the heavy node
    )
    log.info(
        "code stage %d done (%.1fs, cost=$%.4f, turns=%d)",
        idx + 1,
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    summary = result.text.strip()[-2000:] or "(no summary returned)"
    return {
        "code_summary": summary,
        "current_stage_idx": idx + 1,
        "error": None,
    }
