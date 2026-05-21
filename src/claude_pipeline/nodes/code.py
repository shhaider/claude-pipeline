"""Code node: implement one stage from the plan.

v0.2 change: the code node no longer builds its own prompt. The
prompt-expansion node has already produced a per-stage markdown prompt
(in `runs/{run_id}/prompts/P{NN}_{stage}.md`). This node reads that
prompt and hands it straight to `claude --print` running in the
worktree. The expansion pass has already encoded all the discipline
(truth-boundary / fake-completion / scope-boundaries / stop-condition).

v0.3.1 change (Fix 3 — close the agency gap): when
`IMPLEMENTER_INCLUDE_FULL_STATE` is on (default true), the expanded
per-stage prompt is wrapped inside the FULL pipeline state — original
issue, intake decisions, research brief, contract deliverables, the
whole plan, and prior-stage summaries. The implementer is then
told (in a working-principle footer) that it is accountable for the
whole acceptance-criteria list, not just the stage's narrow file
touch map. This restores the framing context that B (single-call)
had naturally, but in a role-prompted form.

If for some reason the expanded prompt is missing (expansion node
errored on this stage), we fall back to a minimal inline prompt so the
pipeline doesn't deadlock — this preserves the "don't break what
works" constraint.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

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


# v0.3.1 — working-principle footer appended to every wrapped prompt.
_WORKING_PRINCIPLE_FOOTER = """\
# Working principle (read carefully)

You are accountable for the WHOLE acceptance criteria list above, not just this stage's narrow file_touch_map. The expansion tells you WHAT to do; you decide HOW.

- Match adjacent modules' patterns. Before writing, read 1-2 nearby files in the codebase that solve similar problems (e.g., research.py, contract.py for prompt-loading and packet-building patterns) and adopt their conventions.
- Use defensive error handling where the LLM's output may be malformed, where dict-vs-string variants are possible, where parsing could fail.
- Factor out testable helpers. If a function builds a prompt packet, expose it as a separate function so tests don't need to monkeypatch the whole node.
- When you have agency over scope decisions in this stage, lean toward MORE robust code, not less. If you're choosing between "minimum viable" and "match the codebase's existing quality bar", choose the latter.

End your response with a one-paragraph summary of what you changed and why.
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


def _full_state_flag() -> bool:
    """Read the IMPLEMENTER_INCLUDE_FULL_STATE env var.

    Default True. Accepted false values: '0', 'false', 'no', 'off' (case-insensitive).
    """
    raw = os.environ.get("IMPLEMENTER_INCLUDE_FULL_STATE")
    if raw is None:
        return True
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


def _render_intake_block(intake: dict[str, Any]) -> str:
    """Render the intake decisions block. Defensive against missing keys."""
    if not isinstance(intake, dict):
        intake = {}
    risk_flags = intake.get("risk_flags") or []
    if isinstance(risk_flags, list):
        risk_flags_rendered = ", ".join(str(x) for x in risk_flags) or "(none)"
    else:
        risk_flags_rendered = str(risk_flags)

    acceptance = intake.get("acceptance_criteria") or []
    if isinstance(acceptance, list) and acceptance:
        acc_bullets = "\n".join(f"  - {c}" for c in acceptance)
    else:
        acc_bullets = "  (none specified at intake)"

    lines = [
        f"- task_type: {intake.get('task_type', '(unspecified)')}",
        f"- complexity_tier: {intake.get('complexity_tier', '(unspecified)')}",
        f"- risk_flags: {risk_flags_rendered}",
        f"- right_thing_answer: {intake.get('right_thing_answer', '(unspecified)')}",
        f"- scope_plan: {intake.get('scope_plan', '(unspecified)')}",
        "- acceptance_criteria:",
        acc_bullets,
        f"- wiring_plan: {intake.get('wiring_plan', '(unspecified)')}",
    ]
    return "\n".join(lines)


def _render_contract_block(contract: dict[str, Any]) -> str:
    """Render the contract block: title + deliverables."""
    if not isinstance(contract, dict):
        contract = {}
    title = contract.get("contract_title") or "(no contract title)"
    deliverables = contract.get("deliverables") or []
    if not isinstance(deliverables, list) or not deliverables:
        return f"{title}\n\nDeliverables:\n  (no deliverables specified)"

    bullet_lines: list[str] = []
    for d in deliverables:
        if not isinstance(d, dict):
            bullet_lines.append(f"  - {d}")
            continue
        d_id = d.get("id", "?")
        name = d.get("name", "?")
        desc = d.get("description", "")
        bullet_lines.append(f"  - **{d_id}** `{name}` — {desc}")
        sc = d.get("success_criteria") or []
        if isinstance(sc, list):
            for c in sc:
                bullet_lines.append(f"      - success: {c}")
    return f"{title}\n\nDeliverables:\n" + "\n".join(bullet_lines)


def _render_plan_block(plan: list[dict[str, Any]]) -> str:
    """Render the full plan: numbered list of every stage."""
    if not isinstance(plan, list) or not plan:
        return "  (empty plan)"
    lines: list[str] = []
    for i, stage in enumerate(plan, start=1):
        if not isinstance(stage, dict):
            lines.append(f"  {i}. {stage}")
            continue
        name = stage.get("name") or stage.get("stage_id") or "?"
        purpose = stage.get("purpose") or stage.get("description") or "(no purpose)"
        ftm_bullets = _ftm_to_bullets(stage.get("file_touch_map", []))
        lines.append(f"  {i}. **{name}** — {purpose}")
        lines.append(f"     files:\n{ftm_bullets}")
    return "\n".join(lines)


def _render_prior_stages_block(
    plan: list[dict[str, Any]], idx: int, prior_summaries: list[str] | None = None
) -> str:
    """Render the prior-stages block.

    If `prior_summaries` is supplied (list of code_summary strings, one per
    completed stage), use those. Otherwise fall back to the stage purpose.
    """
    if idx <= 0:
        return "  (none — this is the first stage)"
    if not isinstance(plan, list):
        return "  (none)"
    lines: list[str] = []
    prior_summaries = prior_summaries or []
    for i, stage in enumerate(plan[:idx], start=1):
        name = "?"
        purpose = ""
        if isinstance(stage, dict):
            name = stage.get("name") or stage.get("stage_id") or "?"
            purpose = stage.get("purpose") or stage.get("description") or ""
        summary = (
            prior_summaries[i - 1]
            if i - 1 < len(prior_summaries) and prior_summaries[i - 1]
            else f"(no summary captured) — {purpose}"
        )
        # Truncate very long summaries to keep the wrapped prompt bounded.
        if len(summary) > 1500:
            summary = summary[:1500] + " …(truncated)"
        lines.append(f"  - **{name}** — {summary}")
    return "\n".join(lines) or "  (none)"


def build_wrapped_prompt(state: PipelineState, expanded: str) -> str:
    """Wrap the per-stage expansion in the full pipeline state.

    This is the v0.3.1 implementer prompt. Exposed as a top-level
    function so tests can exercise it without spawning Claude or
    constructing the whole node.

    Args:
        state: the live PipelineState (TypedDict at runtime is a dict).
        expanded: the per-stage expanded prompt (the existing ~9-13 KB
            markdown brief from the prompt_expand node).

    Returns:
        A single string suitable to hand straight to `claude --print`.
    """
    plan = state.get("plan") or []
    idx = int(state.get("current_stage_idx", 0) or 0)
    if idx < 0:
        idx = 0
    stage_count = len(plan) if isinstance(plan, list) else 0

    stage: dict[str, Any] = {}
    if isinstance(plan, list) and 0 <= idx < stage_count:
        st = plan[idx]
        if isinstance(st, dict):
            stage = st

    intake = state.get("intake") or {}
    research_brief = state.get("research_brief") or "(no research brief captured)"
    contract = state.get("contract") or {}

    # Acceptance-criteria bullets (intake-level — the canonical list the
    # implementer is accountable for).
    acc_bullets = "  (none specified at intake)"
    if isinstance(intake, dict):
        ac = intake.get("acceptance_criteria") or []
        if isinstance(ac, list) and ac:
            acc_bullets = "\n".join(f"  - {c}" for c in ac)

    # Stage-level pieces.
    stage_name = stage.get("name") or stage.get("stage_id") or f"stage-{idx + 1}"

    # Prior summaries: best-effort — we usually only have the LAST
    # stage's code_summary in state (LangGraph last-write-wins). Treat
    # the single field as belonging to the most-recently-completed
    # stage; everything earlier falls back to the plan's purpose text.
    last_summary = state.get("code_summary") or ""
    prior_summaries: list[str] = []
    if idx > 0:
        prior_summaries = [""] * idx
        if last_summary:
            prior_summaries[-1] = last_summary

    intake_block = _render_intake_block(intake if isinstance(intake, dict) else {})
    contract_block = _render_contract_block(contract if isinstance(contract, dict) else {})
    plan_block = _render_plan_block(plan if isinstance(plan, list) else [])
    prior_block = _render_prior_stages_block(
        plan if isinstance(plan, list) else [], idx, prior_summaries
    )

    issue_number = state.get("issue_number", "?")
    issue_title = state.get("issue_title", "?")
    issue_body = state.get("issue_body") or "(issue body not captured in state)"

    parts = [
        "# Full pipeline context",
        "",
        "## Original GitHub issue (verbatim)",
        "",
        f"**Issue #{issue_number}: {issue_title}**",
        "",
        issue_body,
        "",
        "## Intake decisions (the upstream classifier's read of this task)",
        "",
        intake_block,
        "",
        "## Research brief",
        "",
        research_brief,
        "",
        "## Contract — what must exist",
        "",
        contract_block,
        "",
        "## Plan — all stages (for full context)",
        "",
        plan_block,
        "",
        "## Prior stages (already implemented; do NOT redo)",
        "",
        prior_block,
        "",
        f"## THIS STAGE — your specific work",
        "",
        f"(stage {idx + 1} of {stage_count}: {stage_name})",
        "",
        expanded,
        "",
        _WORKING_PRINCIPLE_FOOTER,
    ]
    return "\n".join(parts)


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

    use_full_state = _full_state_flag()

    if expanded:
        if use_full_state:
            prompt = build_wrapped_prompt(state, expanded)
            log.info(
                "code: invoking claude on stage %d/%d (%s) — wrapped prompt "
                "(expansion=%d chars, wrapped=%d chars, full_state=on)",
                idx + 1,
                len(plan),
                stage.get("name", ""),
                len(expanded),
                len(prompt),
            )
        else:
            prompt = expanded
            log.info(
                "code: invoking claude on stage %d/%d (%s) — using expanded prompt only "
                "(%d chars, full_state=off)",
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

    # v0.3 — shared code session across stages.
    # On stage 0 we start fresh and capture the session id. On every
    # subsequent stage we pass --resume <id> so the same Claude session
    # handles all stages and accumulates context (the missing edge that
    # made the single-call baseline win the v0.2 A/B test).
    prior_session_id = state.get("code_session_id") or None
    resume_id = prior_session_id if idx > 0 else None

    try:
        result = run_claude(
            prompt,
            cwd=state["worktree_path"],
            timeout_s=1800,  # 30 min ceiling
            model="sonnet",  # per port spec: code execution uses Tier 2 (Sonnet)
            resume_session_id=resume_id,
        )
    except ClaudeError as e:
        return {"error": f"code stage {idx + 1}: claude call failed: {e}"}

    log.info(
        "code stage %d done (%.1fs, cost=$%.4f, turns=%d, session=%s, resumed=%s)",
        idx + 1,
        result.duration_s,
        result.cost_usd,
        result.num_turns,
        (result.session_id or "")[:8],
        "yes" if resume_id else "no",
    )

    summary = result.text.strip()[-2000:] or "(no summary returned)"
    out: dict = {
        "code_summary": summary,
        "current_stage_idx": idx + 1,
        "error": None,
    }
    # Always carry the session id forward. On stage 0 this is the first
    # capture; on later stages it should be the same id (resume keeps it
    # stable), but we write it again defensively in case the CLI ever
    # rotates.
    if result.session_id:
        out["code_session_id"] = result.session_id
    return out
