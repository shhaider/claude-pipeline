"""executive_governance_reviewer node — v0.3 simplification of metabuilder's 8c.

System prompt: `prompts/metabuilder/08_executive_governance_reviewer.md`.

User packet includes:
  - the plan (stages)
  - pack_reviewer verdict
  - reasoning_reviewer verdict
  - test results (verify)
  - git diff
  - issue acceptance criteria

Output JSON:
  {
    governance_verdict: "PASS|FAIL|NEEDS_REVISION",
    overall_assessment: str,
    findings: [{criterion, result, note}, ...],
    blocking_issues: [str, ...]
  }

LLM params: Tier 3 / Opus, max_tokens 8192, T=0.2.
Fresh session.

Re-invocations after governance_repair pass a `repair_round` integer in
the packet so the reviewer can track progress.
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
_GOV_PATH = _PROMPTS_DIR / "08_executive_governance_reviewer.md"


def _load_role_prompt() -> str:
    try:
        return _GOV_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing executive_governance_reviewer role prompt at {_GOV_PATH}: {e}"
        ) from e


def _render_plan(stages: list[dict[str, Any]]) -> str:
    if not stages:
        return "(none)"
    out: list[str] = []
    for i, s in enumerate(stages):
        sid = s.get("stage_id") or f"S{i + 1}"
        out.append(
            f"- **{sid}** — {s.get('name', '?')}: {s.get('purpose') or s.get('description', '')}"
        )
    return "\n".join(out)


def build_governance_packet(state: PipelineState, diff_text: str, repair_round: int) -> str:
    stages = state.get("plan", []) or []
    pack = state.get("pack_review", {}) or {}
    reasoning = state.get("reasoning_review", {}) or {}
    verify = state.get("verify", {}) or {}
    intake = state.get("intake", {}) or {}
    contract = state.get("contract", {}) or {}
    delivs = contract.get("deliverables", []) or []

    intake_crit_lines = [f"- {c}" for c in intake.get("acceptance_criteria", []) or []]
    deliv_lines = [
        f"- {d.get('id', '?')}: {d.get('name', '?')}" for d in delivs
    ]

    repair_block = ""
    if repair_round > 0:
        repair_block = (
            f"\n## Repair round\n\n"
            f"This is governance review **after repair round {repair_round}**. The previous\n"
            f"verdict identified must_fix items; the planner has since patched the affected\n"
            f"stages and the implementer re-ran them. Verify the patches actually addressed\n"
            f"the prior must_fix items before issuing PASS.\n"
        )

    lines = [
        "## executive_governance_reviewer task",
        "",
        "You are acting as executive_governance_reviewer. Make the readiness call:",
        "PASS / FAIL / NEEDS_REVISION. PASS means downstream can ship; FAIL means a",
        "hard blocker; NEEDS_REVISION means must_fix items exist but are repairable",
        "via a targeted stage patch.",
        repair_block,
        "## Issue acceptance criteria (from intake)",
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
        f"- must_fix: {pack.get('must_fix', []) or '(none)'}",
        f"- should_fix: {pack.get('should_fix', []) or '(none)'}",
        f"- hindsight: {pack.get('hindsight', '(none)')}",
        "",
        "## reasoning_reviewer verdict",
        "",
        f"- verdict: {reasoning.get('reasoning_verdict', '?')}",
        f"- overall: {reasoning.get('overall_assessment', '(none)')}",
        f"- blocking_concerns: {reasoning.get('blocking_concerns', []) or '(none)'}",
        "",
        "## Test results",
        "",
        f"- passed: {verify.get('passed', False)}",
        f"- summary: {verify.get('summary', '(none)')}",
        f"- failing_tests: {verify.get('failing_tests', []) or '(none)'}",
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
        '  "governance_verdict": "PASS" | "FAIL" | "NEEDS_REVISION",',
        '  "overall_assessment": "one or two sentences — your readiness call",',
        '  "findings": [',
        "    {",
        '      "criterion": "what was checked — e.g. \\"all must_fix resolved\\", \\"deliverable D2 in diff\\"",',
        '      "result": "PASS | FAIL | PARTIAL",',
        '      "note": "one sentence explaining"',
        "    }",
        "  ],",
        '  "blocking_issues": ["short titles of items that must be fixed before PASS"]',
        "}",
        "```",
        "",
        "Rules:",
        "- governance_verdict=PASS only when blocking_issues is empty AND every finding is PASS.",
        "- governance_verdict=NEEDS_REVISION when targeted stage patches could fix all blockers.",
        "- governance_verdict=FAIL when blockers require redesign (not a patch).",
        "- For each blocking_issue, name the affected stage_id when possible — this is what",
        "  the governance_repair loop will use to scope its patches.",
        "- Output JSON only. No markdown fence. No commentary outside the object.",
    ]
    return "\n".join(lines)


def governance_reviewer_node(state: PipelineState, *, repair_round: int = 0) -> dict:
    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    diff_text = state.get("code_diff", "") or capture_diff(
        state["worktree_path"], state.get("base_branch", "main")
    )
    user_msg = build_governance_packet(state, diff_text, repair_round=repair_round)

    log.info(
        "governance_reviewer: invoking claude (opus, fresh session, repair_round=%d)",
        repair_round,
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
        return {"error": f"governance_reviewer: claude call failed: {e}"}

    log.info(
        "governance_reviewer: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning(
            "governance_reviewer: parse failed: %s; head=%s", e, result.text[:300]
        )
        verdict = {
            "governance_verdict": "NEEDS_REVISION",
            "overall_assessment": f"parse failed: {e}",
            "findings": [],
            "blocking_issues": [],
            "repair_round": repair_round,
        }
        return {"governance_review": verdict, "code_diff": diff_text, "error": None}
    if not isinstance(raw, dict):
        return {
            "error": f"governance_reviewer: expected JSON object, got {type(raw).__name__}"
        }

    findings_in = raw.get("findings", []) or []
    findings: list[dict[str, str]] = []
    for f in findings_in:
        if not isinstance(f, dict):
            continue
        findings.append(
            {
                "criterion": str(f.get("criterion", "")),
                "result": str(f.get("result", "")),
                "note": str(f.get("note", "")),
            }
        )
    verdict = {
        "governance_verdict": str(raw.get("governance_verdict", "NEEDS_REVISION")).upper(),
        "overall_assessment": str(raw.get("overall_assessment", "")),
        "findings": findings,
        "blocking_issues": [str(x) for x in raw.get("blocking_issues", []) or []],
        "repair_round": repair_round,
    }
    log.info(
        "governance_reviewer done: verdict=%s findings=%d blocking=%d",
        verdict["governance_verdict"],
        len(verdict["findings"]),
        len(verdict["blocking_issues"]),
    )
    return {"governance_review": verdict, "code_diff": diff_text, "error": None}
