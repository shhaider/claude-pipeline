"""Code node: implement one stage from the plan.

v0.2 change: the code node no longer builds its own prompt. The
prompt-expansion node has already produced a per-stage markdown prompt
(in `runs/{run_id}/prompts/P{NN}_{stage}.md`). This node reads that
prompt and hands it straight to `claude --print` running in the
worktree. The expansion pass has already encoded all the discipline
(truth-boundary / fake-completion / scope-boundaries / stop-condition).

If for some reason the expanded prompt is missing (expansion node
errored on this stage), we fall back to a minimal inline prompt so the
pipeline doesn't deadlock — this preserves the "don't break what
works" constraint.
"""

from __future__ import annotations

import logging
from pathlib import Path

from claude_pipeline.claude import ClaudeError, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


# Fallback prompt — only used when the expansion node failed for this stage.
_FALLBACK_PROMPT_TEMPLATE = """You are implementing one stage of a planned software change. The worktree at your current directory is an isolated checkout. You have Read / Edit / Write / Bash / Glob / Grep tools.

ISSUE: {issue_title}

THE STAGE YOU ARE IMPLEMENTING (stage {stage_idx} of {stage_count}):

Stage name:        {stage_name}
Description:       {stage_description}
File touch map:    {stage_files_bullets}

ACCEPTANCE CRITERIA (issue-level — must be satisfied):
{acceptance_criteria_bullets}

PRIOR STAGES (already implemented, do not redo):
{prior_stages_bullets}

Rules:
- Only modify files in the file touch map. Reading other files is fine.
- Match the existing code's conventions.
- DO NOT commit yet. The pipeline's commit node handles that.

When done, finish with one paragraph summarising what you changed and why.
"""


def _ftm_to_bullets(ftm) -> str:
    if isinstance(ftm, dict):
        parts: list[str] = []
        for label in ("create", "modify"):
            for p in ftm.get(label, []) or []:
                parts.append(f"  - {p} ({label})")
        return "\n".join(parts) or "  (no files declared)"
    if isinstance(ftm, list):
        return "\n".join(f"  - {p}" for p in ftm) or "  (no files declared)"
    return "  (no files declared)"


def code_node(state: PipelineState) -> dict:
    plan = state.get("plan", [])
    idx = state.get("current_stage_idx", 0)
    if idx >= len(plan):
        return {"error": f"code: current_stage_idx {idx} out of range (plan has {len(plan)})"}

    stage = plan[idx]
    intake = state.get("intake", {})

    # Preferred path: read the expanded prompt produced by prompt_expand.
    expanded = stage.get("expanded_prompt") or ""
    prompt_path = stage.get("prompt_path") or ""
    if not expanded and prompt_path:
        try:
            expanded = Path(prompt_path).read_text(encoding="utf-8")
        except OSError as e:
            log.warning("code: failed to read expanded prompt %s: %s", prompt_path, e)

    if expanded:
        prompt = expanded
        log.info(
            "code: invoking claude on stage %d/%d (%s) — using expanded prompt (%d chars)",
            idx + 1,
            len(plan),
            stage.get("name", ""),
            len(expanded),
        )
    else:
        # Fallback — shouldn't happen if expansion succeeded
        prior = plan[:idx]
        prompt = _FALLBACK_PROMPT_TEMPLATE.format(
            issue_title=state.get("issue_title", "?"),
            stage_idx=idx + 1,
            stage_count=len(plan),
            stage_name=stage.get("name", ""),
            stage_description=stage.get("purpose") or stage.get("description", ""),
            stage_files_bullets=_ftm_to_bullets(stage.get("file_touch_map", [])),
            acceptance_criteria_bullets="\n".join(
                f"  - {c}" for c in intake.get("acceptance_criteria", [])
            ),
            prior_stages_bullets="\n".join(
                f"  - {s.get('name', '?')}: {s.get('purpose') or s.get('description', '')}"
                for s in prior
            )
            or "  (none — this is the first stage)",
        )
        log.warning(
            "code: no expanded prompt for stage %d (%s) — using fallback",
            idx + 1,
            stage.get("name", ""),
        )

    try:
        result = run_claude(
            prompt,
            cwd=state["worktree_path"],
            timeout_s=1800,  # 30 min ceiling
            model="sonnet",  # per port spec: code execution uses Tier 2 (Sonnet)
        )
    except ClaudeError as e:
        return {"error": f"code stage {idx + 1}: claude call failed: {e}"}

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
