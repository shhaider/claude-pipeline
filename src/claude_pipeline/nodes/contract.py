"""Contract node: define WHAT must be produced (deliverables list).

Verbatim port of metabuilder's contract_writer role:
  - System prompt = `prompts/metabuilder/27_contract_writer.md`.
  - User message = Python equivalent of `buildContractPacket()` from
    `scripts/metabuilder/plan_self_upgrade.js` — injects a "GOAL ANCHOR"
    structured block (PRIMARY GOAL / SECONDARY / ANTI-GOALS / SUCCESS
    LOOKS LIKE) plus the research output.
  - Tier 3: model=Opus.

Output schema (per port spec):
  {
    "contract_title": str,
    "deliverables": [
      {"id": "D1", "name": str, "description": str,
       "success_criteria": [str, ...], "source_goal": str}, ...
    ],
    "ambiguity_flags": [{"goal": str, "issue": str, "assumed": str}, ...],
    "total_deliverables": int,
    "verification": {...}
  }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.state import Contract, PipelineState

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder"
_CONTRACT_PROMPT_PATH = _PROMPTS_DIR / "27_contract_writer.md"


def _load_role_prompt() -> str:
    try:
        return _CONTRACT_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing contract_writer role prompt at {_CONTRACT_PROMPT_PATH}: {e}"
        ) from e


def _build_user_packet(state: PipelineState) -> str:
    """Port of buildContractPacket.

    Injects the GOAL ANCHOR (PRIMARY / SECONDARY / ANTI-GOALS / SUCCESS
    LOOKS LIKE) above the research evidence, so the contract writer
    cannot drop any stated goal.
    """
    intake = state.get("intake", {})
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "")
    research_brief = state.get("research_brief", "")

    # The PRIMARY GOAL is the issue title + body; SECONDARY is anything
    # the intake decisions surface; ANTI-GOALS are inferred negatives
    # (don't break tests, don't expand scope); SUCCESS LOOKS LIKE is
    # the acceptance criteria.
    initiative_id = f"{state.get('repo', '?')}#{state.get('issue_number', '?')}"

    goal_anchor = [
        "## GOAL ANCHOR",
        "",
        "**PRIMARY GOAL:**",
        f"  {issue_title}",
        "",
        "  Body:",
    ]
    for line in (issue_body or "(empty)").splitlines():
        goal_anchor.append(f"  {line}")
    goal_anchor.extend(
        [
            "",
            "**SECONDARY GOALS (from intake):**",
            f"  - Task type: {intake.get('task_type', '?')}",
            f"  - Scope plan: {intake.get('scope_plan', '?')}",
            f"  - Wiring plan: {intake.get('wiring_plan', '?')}",
            "",
            "**ANTI-GOALS:**",
            "  - Do not expand scope beyond what the issue requests.",
            "  - Do not regress existing passing tests.",
            "  - Do not introduce dependencies the repo doesn't already use.",
            "",
            "**SUCCESS LOOKS LIKE (acceptance criteria from intake):**",
        ]
    )
    for c in intake.get("acceptance_criteria", []) or []:
        goal_anchor.append(f"  - {c}")
    if not intake.get("acceptance_criteria"):
        goal_anchor.append("  (none provided — derive from PRIMARY GOAL)")

    packet_lines = [
        "## Planning Request",
        "",
        f"**Initiative ID:** {initiative_id}",
        f"**Planning request:** {issue_title}",
        "",
        "\n".join(goal_anchor),
        "",
        "## Research evidence",
        "",
        research_brief or "(no research brief)",
        "",
        "## Your task",
        "",
        "You are acting as contract_writer. Produce a deliverable contract that",
        "covers every element in the GOAL ANCHOR above. Every PRIMARY/SECONDARY",
        "goal must map to at least one deliverable. The SUCCESS LOOKS LIKE bullets",
        "should map to deliverable success_criteria.",
        "",
        "Output a single JSON object only, in the schema specified by your role.",
        "No prose preamble, no markdown fence.",
    ]
    return "\n".join(packet_lines)


def _normalize_contract(raw: dict) -> Contract:
    """Coerce variant contract shapes into our TypedDict."""
    deliverables_in = raw.get("deliverables", []) or []
    deliverables = []
    for i, d in enumerate(deliverables_in):
        if not isinstance(d, dict):
            continue
        did = str(d.get("id", f"D{i + 1}"))
        sc_raw = d.get("success_criteria", []) or []
        if isinstance(sc_raw, str):
            sc = [sc_raw]
        else:
            sc = [str(x) for x in sc_raw]
        deliverables.append(
            {
                "id": did,
                "name": str(d.get("name", "")),
                "description": str(d.get("description", "")),
                "success_criteria": sc,
                "source_goal": str(d.get("source_goal", "")),
            }
        )
    return {
        "contract_title": str(raw.get("contract_title", "")),
        "deliverables": deliverables,
        "ambiguity_flags": list(raw.get("ambiguity_flags") or []),
        "total_deliverables": int(raw.get("total_deliverables") or len(deliverables)),
        "verification": dict(raw.get("verification") or {}),
    }


def contract_node(state: PipelineState) -> dict:
    user_msg = _build_user_packet(state)
    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    log.info("contract: invoking claude (opus, role=contract_writer)")
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=300,
            model="opus",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return {"error": f"contract: claude call failed: {e}"}

    log.info(
        "contract: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"contract parse failed: {e}; text head: {result.text[:300]}"}
    if not isinstance(raw, dict):
        return {"error": f"contract: expected JSON object, got {type(raw).__name__}"}

    contract = _normalize_contract(raw)
    if not contract["deliverables"]:
        return {"error": "contract: zero deliverables — refusing to proceed"}

    log.info(
        "contract done: %d deliverables, %d ambiguity flags",
        len(contract["deliverables"]),
        len(contract.get("ambiguity_flags") or []),
    )
    return {"contract": contract, "error": None}
