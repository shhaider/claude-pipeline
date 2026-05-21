"""Research node: given the intake decisions, produce a concise
research brief that grounds the plan in the actual codebase.

Claude Code does the reading itself (it has Read/Grep/Bash tools inside
the worktree). Output is a markdown brief: what the code currently looks
like, where the touch points are, what conventions exist.
"""

from __future__ import annotations

import logging

from claude_pipeline.claude import run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are doing read-only research for a software task. The worktree at your current directory is an isolated checkout of {repo}. You have Read/Grep/Glob/Bash tools.

THE TASK (from intake):
- Type:          {task_type}
- Tier:          {complexity_tier}
- Scope:         {scope_plan}
- Right thing:   {right_thing_answer}
- Acceptance:    {acceptance_criteria_bullets}
- Wiring:        {wiring_plan}

ISSUE #{issue_number}: {issue_title}

ISSUE BODY:
{issue_body}

Your job: produce a 1-2 page research brief in markdown that the PLAN node will use. It should answer:

1. **Current code shape** — what exists today in the files this task touches. List the relevant files with one-line descriptions.
2. **Touch points** — the specific functions / classes / modules the implementation will need to modify.
3. **Existing conventions** — code patterns, naming, test style, that the new code must match.
4. **Hidden constraints** — anything in the code that complicates the obvious approach (existing API contracts, foreign callers, governance gates).
5. **Recommended approach** — one paragraph: based on the actual code (not abstract reasoning), what's the cleanest way to satisfy the acceptance criteria?

Constraints:
- Read code; do NOT speculate. If you can't find the relevant code, say so.
- DO NOT write any code yet. This node is read-only.
- Keep it concise — the next node (PLAN) needs to read this in one pass.

Output the markdown brief directly. No preamble.
"""


def research_node(state: PipelineState) -> dict:
    intake = state.get("intake", {})
    prompt = PROMPT_TEMPLATE.format(
        repo=state["repo"],
        issue_number=state["issue_number"],
        issue_title=state.get("issue_title", ""),
        issue_body=state.get("issue_body", ""),
        task_type=intake.get("task_type", "?"),
        complexity_tier=intake.get("complexity_tier", "?"),
        scope_plan=intake.get("scope_plan", "?"),
        right_thing_answer=intake.get("right_thing_answer", "?"),
        acceptance_criteria_bullets="\n".join(
            f"  - {c}" for c in intake.get("acceptance_criteria", [])
        ),
        wiring_plan=intake.get("wiring_plan", "?"),
    )
    log.info("research: invoking claude (read-only research pass)")
    result = run_claude(
        prompt,
        cwd=state["worktree_path"],
        timeout_s=600,  # Reading can take a while on large repos
    )
    brief = result.stdout.strip()
    if not brief:
        return {"error": "research: claude returned empty brief"}
    log.info("research done: brief length %d chars", len(brief))
    return {"research_brief": brief, "error": None}
