"""release_gatekeeper node — final PASS/FAIL/BLOCKED gate.

System prompt: `prompts/metabuilder/19_release_gatekeeper.md` (verbatim).
User packet: all prior verdicts + plan + diff + verify report.

The release_gatekeeper role prompt enforces several mandatory criteria
(spec completeness on disk, working tree hygiene, mandatory reviewer
panel). For v0.3 we route these through the role prompt's language —
the LLM is asked to verify them. The 4-mandatory-reviewer-panel rule
in the role prompt does not apply to v0.3 (we don't yet ship those
four reviewers — that's v0.4); we tell the gatekeeper this explicitly
in the packet so it doesn't FAIL on a missing-reviewer technicality.

Output JSON:
  {
    decision: "PASS|FAIL|BLOCKED",
    rationale: str,
    unresolved_items: [str, ...],
    verification: str
  }

LLM params: Tier 2 / Sonnet, max_tokens 4096, T=0.3.
Fresh session.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.diff import capture_diff
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder"
_GATEKEEPER_PATH = _PROMPTS_DIR / "19_release_gatekeeper.md"


def _load_role_prompt() -> str:
    try:
        return _GATEKEEPER_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing release_gatekeeper role prompt at {_GATEKEEPER_PATH}: {e}"
        ) from e


def _render_plan(stages: list[dict[str, Any]]) -> str:
    if not stages:
        return "(none)"
    out: list[str] = []
    for i, s in enumerate(stages):
        sid = s.get("stage_id") or f"S{i + 1}"
        ftm = s.get("file_touch_map", {})
        files = []
        if isinstance(ftm, dict):
            files = (ftm.get("create") or []) + (ftm.get("modify") or [])
        elif isinstance(ftm, list):
            files = list(ftm)
        out.append(
            f"- **{sid}** — {s.get('name', '?')} — files: {', '.join(str(f) for f in files) or '(none)'}"
        )
    return "\n".join(out)


def build_gatekeeper_packet(state: PipelineState, diff_text: str) -> str:
    stages = state.get("plan", []) or []
    pack = state.get("pack_review", {}) or {}
    reasoning = state.get("reasoning_review", {}) or {}
    governance = state.get("governance_review", {}) or {}
    verify = state.get("verify", {}) or {}
    contract = state.get("contract", {}) or {}
    delivs = contract.get("deliverables", []) or []
    intake = state.get("intake", {}) or {}
    repair_rounds = int(state.get("governance_repair_rounds", 0) or 0)

    deliv_lines = [
        f"- {d.get('id', '?')}: {d.get('name', '?')} — {d.get('description', '')}"
        for d in delivs
    ]
    intake_crit_lines = [f"- {c}" for c in intake.get("acceptance_criteria", []) or []]

    lines = [
        "## release_gatekeeper task",
        "",
        "You are acting as release_gatekeeper for this pipeline run. Issue the final",
        "GATE decision: PASS, FAIL, or BLOCKED.",
        "",
        "## v0.3 pipeline scope notice (read this first)",
        "",
        "Your role prompt requires the four mandatory reviewers (founder_judge,",
        "reliability_engineer, state_architecture_reviewer, security_blast_radius_judge).",
        "THIS PIPELINE DOES NOT YET SHIP THOSE REVIEWERS — they're scheduled for v0.4.",
        "Do NOT issue FAIL solely on their absence. The reviewers we DO ship and that",
        "have already run on this change are: pack_reviewer, software_reasoning_reviewer,",
        "executive_governance_reviewer. Treat those as the active review ladder.",
        "",
        "## Issue acceptance criteria",
        "",
        "\n".join(intake_crit_lines) or "(none)",
        "",
        "## Contract deliverables",
        "",
        "\n".join(deliv_lines) or "(none)",
        "",
        "## Plan stages",
        "",
        _render_plan(stages),
        "",
        "## pack_reviewer verdict",
        "",
        f"- passed: {pack.get('passed', '?')}",
        f"- must_fix count: {len(pack.get('must_fix', []) or [])}",
        f"- must_fix: {pack.get('must_fix', []) or '(none)'}",
        f"- hindsight: {pack.get('hindsight', '(none)')}",
        "",
        "## reasoning_reviewer verdict",
        "",
        f"- verdict: {reasoning.get('reasoning_verdict', '?')}",
        f"- blocking_concerns: {reasoning.get('blocking_concerns', []) or '(none)'}",
        "",
        "## governance_reviewer verdict (after repair)",
        "",
        f"- verdict: {governance.get('governance_verdict', '?')}",
        f"- blocking_issues: {governance.get('blocking_issues', []) or '(none)'}",
        f"- repair_rounds_executed: {repair_rounds}",
        f"- assessment: {governance.get('overall_assessment', '(none)')}",
        "",
        "## Test results",
        "",
        f"- passed: {verify.get('passed', False)}",
        f"- summary: {verify.get('summary', '(none)')}",
        "",
        "## Diff under review",
        "",
        "```diff",
        diff_text or "(empty diff)",
        "```",
        "",
        "## Required output (JSON only)",
        "",
        "```json",
        "{",
        '  "decision": "PASS" | "FAIL" | "BLOCKED",',
        '  "rationale": "one paragraph — your reasoning",',
        '  "unresolved_items": ["short titles of any unresolved blockers"],',
        '  "verification": "one sentence — how you confirmed completion"',
        "}",
        "```",
        "",
        "Rules:",
        "- decision=PASS requires governance_verdict=PASS AND no must_fix items from",
        "  any reviewer AND verify.passed=true (or pre-existing failures explicitly",
        "  documented as unrelated).",
        "- decision=FAIL means a hard blocker remains and the pipeline should not ship.",
        "- decision=BLOCKED means an external dependency or human action is required.",
        "- Spec completeness: verify deliverables actually appear in the diff under their",
        "  declared paths. If a deliverable file is not in the diff and is not visibly",
        "  satisfied by other changes, that's a FAIL with the missing item listed.",
        "- Output JSON only. No markdown fence. No commentary outside the object.",
    ]
    return "\n".join(lines)


def release_gatekeeper_node(state: PipelineState) -> dict:
    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    diff_text = state.get("code_diff", "") or capture_diff(
        state["worktree_path"], state.get("base_branch", "main")
    )
    user_msg = build_gatekeeper_packet(state, diff_text)

    log.info("release_gatekeeper: invoking claude (sonnet, fresh session)")
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="sonnet",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return {"error": f"release_gatekeeper: claude call failed: {e}"}

    log.info(
        "release_gatekeeper: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning(
            "release_gatekeeper: parse failed: %s; head=%s", e, result.text[:300]
        )
        verdict = {
            "decision": "FAIL",
            "rationale": f"gatekeeper parse failed: {e}",
            "unresolved_items": ["parse_failure"],
            "verification": "parse_failed",
        }
        return {"gatekeeper": verdict, "code_diff": diff_text, "error": None}
    if not isinstance(raw, dict):
        return {
            "error": f"release_gatekeeper: expected JSON object, got {type(raw).__name__}"
        }

    verif_val = raw.get("verification", "")
    if isinstance(verif_val, dict):
        verif_str = str(verif_val.get("method") or verif_val.get("verified_complete", ""))
    else:
        verif_str = str(verif_val)

    verdict = {
        "decision": str(raw.get("decision", "FAIL")).upper(),
        "rationale": str(raw.get("rationale", "")),
        "unresolved_items": [str(x) for x in raw.get("unresolved_items", []) or []],
        "verification": verif_str,
    }
    log.info(
        "release_gatekeeper done: decision=%s unresolved=%d",
        verdict["decision"],
        len(verdict["unresolved_items"]),
    )
    return {"gatekeeper": verdict, "code_diff": diff_text, "error": None}
