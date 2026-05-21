"""Plan node: pack_planner — stage the contract into a task graph.

Verbatim port of metabuilder's pack_planner role:
  - System prompt = `prompts/metabuilder/10_pack_planner.md`.
  - User message = Python equivalent of `buildPlannerPacket()` — injects
    the contract deliverables verbatim as "MANDATORY CONTRACT" so the
    planner cannot drop a deliverable.
  - Tier 3 + max_tokens=8192 (Opus).

Includes the deterministic 4-Correction cycle:
  1. First pack_planner call -> get plan.
  2. checkPlanCompleteness(contract, plan) -> any missing deliverables?
  3. If yes: ONE retry with CORRECTION REQUIRED block appended. Max 1.
  4. If second call still has missing, log warning and accept.

Output schema:
  {
    "plan_title": str,
    "stages": [Stage, ...],
    "recommended_first_stage": str,
    "estimated_risk": "low|medium|high",
    "risk_rationale": str,
    "assumption_audit": {...},
    "verification": {...}
  }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.plan_completeness import (
    build_correction_block,
    check_plan_completeness,
)
from claude_pipeline.state import PipelineState, Plan, Stage

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder"
_PLANNER_PROMPT_PATH = _PROMPTS_DIR / "10_pack_planner.md"


def _load_role_prompt() -> str:
    try:
        return _PLANNER_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing pack_planner role prompt at {_PLANNER_PROMPT_PATH}: {e}"
        ) from e


def _render_deliverables(deliverables: list[dict[str, Any]]) -> str:
    """Render contract deliverables for verbatim inclusion in the planner packet."""
    if not deliverables:
        return "(no deliverables)"
    lines: list[str] = []
    for d in deliverables:
        did = d.get("id", "D?")
        name = d.get("name", "?")
        desc = d.get("description", "")
        sc = d.get("success_criteria", []) or []
        lines.append(f"- **{did}** — `{name}` — {desc}")
        if sc:
            for c in sc:
                lines.append(f"    - success: {c}")
    return "\n".join(lines)


def _build_user_packet(state: PipelineState, correction_block: str = "") -> str:
    """Port of buildPlannerPacket — inject the contract deliverables
    verbatim as "MANDATORY CONTRACT" so the planner cannot drop them.
    """
    contract = state.get("contract", {}) or {}
    deliverables = contract.get("deliverables", []) or []
    issue_title = state.get("issue_title", "")
    research_brief = state.get("research_brief", "")
    intake = state.get("intake", {})

    initiative_id = f"{state.get('repo', '?')}#{state.get('issue_number', '?')}"

    lines = [
        "## Planning Request",
        "",
        f"**Initiative ID:** {initiative_id}",
        f"**Planning request:** {issue_title}",
        "",
        "## MANDATORY CONTRACT - every deliverable below MUST appear in at least one stage",
        "",
        _render_deliverables(deliverables),
        "",
        "## Research evidence",
        "",
        research_brief or "(no research brief)",
        "",
        "## Intake decisions",
        "",
        json.dumps(dict(intake), indent=2),
        "",
        "## Your task",
        "",
        "You are acting as pack_planner. Produce a JSON `planning_output` per your role.",
        "Constraints (project-specific overrides for this run):",
        "- Skip the mandatory-reviewer-panel stages (founder_judge, reliability_engineer,",
        "  state_architecture_reviewer, security_blast_radius_judge) and the pack_reviewer /",
        "  release_gatekeeper stages — this pipeline runs those out-of-band, not as stages.",
        "  Your plan should contain ONLY implementation_builder stages.",
        "- Aim for 2-5 stages. Each stage = one focused coding session.",
        "- Use `file_touch_map` as an object with `create`, `modify`, `do_not_touch` arrays.",
        "- Every contract deliverable above MUST appear in some stage's `file_touch_map` or `purpose`.",
        "- Output a single JSON object only, no prose preamble, no markdown fence.",
    ]
    if correction_block:
        lines.extend(["", correction_block])
    return "\n".join(lines)


def _normalize_plan_output(raw: dict) -> tuple[Plan, list[Stage]]:
    """Coerce pack_planner output into (Plan, flat stage list)."""
    stages_in = raw.get("stages", []) or []
    stages: list[Stage] = []
    flat_for_graph: list[Stage] = []
    for i, s in enumerate(stages_in):
        if not isinstance(s, dict):
            continue
        sid = str(s.get("stage_id") or f"S{i + 1}")
        name = str(s.get("name", sid))
        purpose = str(s.get("purpose") or s.get("description") or "")
        role = str(s.get("role", "implementation_builder"))
        ftm = s.get("file_touch_map", {})
        # Build a flat list for graph display, but keep the structured
        # form too (the prompt-expansion node uses the structured form).
        flat_files: list[str] = []
        if isinstance(ftm, dict):
            for k in ("create", "modify"):
                v = ftm.get(k, []) or []
                if isinstance(v, list):
                    flat_files.extend(str(x) for x in v)
        elif isinstance(ftm, list):
            flat_files = [str(x) for x in ftm]
            ftm = {"create": [], "modify": flat_files, "do_not_touch": []}
        crit_in = s.get("acceptance_criteria", []) or []
        crit_out: list[dict[str, str]] = []
        for c in crit_in:
            if isinstance(c, dict):
                crit_out.append(
                    {
                        "check": str(c.get("check", "")),
                        "pass_condition": str(c.get("pass_condition", "")),
                    }
                )
            elif isinstance(c, str):
                crit_out.append({"check": c, "pass_condition": "(prose-only)"})
        stage: Stage = {
            "stage_id": sid,
            "name": name,
            "purpose": purpose,
            "description": purpose,  # v0.1 compat
            "role": role,
            "file_touch_map": ftm,
            "acceptance_criteria": crit_out,
            "depends_on": [str(x) for x in (s.get("depends_on") or [])],
            "backward_compat_notes": str(s.get("backward_compat_notes", "")),
        }
        stages.append(stage)
        flat_for_graph.append(stage)

    plan_meta: Plan = {
        "plan_title": str(raw.get("plan_title", "")),
        "stages": stages,
        "recommended_first_stage": str(raw.get("recommended_first_stage", "")),
        "estimated_risk": str(raw.get("estimated_risk", "")),
        "risk_rationale": str(raw.get("risk_rationale", "")),
        "assumption_audit": dict(raw.get("assumption_audit") or {}),
        "verification": dict(raw.get("verification") or {}),
    }
    return plan_meta, flat_for_graph


def _one_pack_planner_call(
    state: PipelineState, correction_block: str = ""
) -> tuple[Plan | None, list[Stage], str | None]:
    """Single pack_planner invocation. Returns (plan_meta, stages, error)."""
    user_msg = _build_user_packet(state, correction_block=correction_block)
    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return None, [], str(e)

    log.info(
        "plan: invoking claude (opus, role=pack_planner%s)",
        " — CORRECTION" if correction_block else "",
    )
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="opus",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return None, [], f"plan: claude call failed: {e}"

    log.info(
        "plan: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return None, [], f"plan parse failed: {e}; text head: {result.text[:300]}"
    if not isinstance(raw, dict):
        return None, [], f"plan: expected JSON object, got {type(raw).__name__}"

    plan_meta, stages = _normalize_plan_output(raw)
    if not stages:
        return None, [], "plan: zero stages — refusing to proceed"

    return plan_meta, stages, None


def plan_node(state: PipelineState) -> dict:
    """Generate the plan, then run the deterministic completeness check.

    If the check fails AND we haven't already done a correction pass,
    run ONE more pack_planner call with a CORRECTION REQUIRED block.
    """
    contract = state.get("contract", {}) or {}
    deliverables = contract.get("deliverables", []) or []

    # First pass
    plan_meta, stages, err = _one_pack_planner_call(state)
    if err:
        return {"error": err}
    assert plan_meta is not None

    # Completeness gate
    check = check_plan_completeness(deliverables, stages)
    if not check["ok"] and not state.get("plan_correction_attempted", False):
        log.warning(
            "plan: completeness check failed — %d missing deliverables; running correction",
            len(check["missing"]),
        )
        correction = build_correction_block(check["missing"])
        plan_meta2, stages2, err2 = _one_pack_planner_call(
            state, correction_block=correction
        )
        if err2:
            log.warning("plan: correction call errored: %s — keeping original plan", err2)
        else:
            assert plan_meta2 is not None
            check2 = check_plan_completeness(deliverables, stages2)
            if check2["ok"]:
                log.info("plan: correction succeeded — using corrected plan")
                plan_meta, stages = plan_meta2, stages2
            else:
                log.warning(
                    "plan: correction still incomplete (%d missing) — using corrected plan anyway",
                    len(check2["missing"]),
                )
                plan_meta, stages = plan_meta2, stages2

    log.info(
        "plan done: %d stages (risk=%s)",
        len(stages),
        plan_meta.get("estimated_risk", "?"),
    )

    # Final completeness state (informational)
    final_check = check_plan_completeness(deliverables, stages)

    return {
        "plan": stages,
        "plan_meta": plan_meta,
        "plan_correction_attempted": True,
        "current_stage_idx": 0,
        "error": None
        if final_check["ok"]
        else None,  # don't hard-fail; downstream nodes still see the plan
    }
