"""pack_reviewer node — v0.3 simplification of metabuilder's 8a.

Metabuilder runs pack_reviewer against the implementation_record AFTER
the implementer claims the stage is done. In v0.3 we run it once at the
end of all coding, reviewing the actual diff against base. This is the
simpler "all reviewers after the code node" topology described in the
v0.3 plan; if it proves insufficient, v0.4 can split per-stage.

System prompt: `prompts/metabuilder/12_pack_reviewer.md` (verbatim).
User packet: Python port of buildReviewerPacket — plan + research +
code summary + git diff + mandatory Fresh Eyes Hindsight directive.

Output schema (from role prompt):
  {
    must_fix: [str],
    should_fix: [str],
    notes: [str],
    passed: bool,
    hindsight: str,        # one sentence + classification
    verification: str,     # one sentence
  }

LLM params: Tier 2 / Sonnet, max_tokens 4096, T=0.3.
Fresh session — does NOT resume the code session (different role,
needs fresh eyes per the role prompt's literal wording).
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
_PACK_REVIEWER_PATH = _PROMPTS_DIR / "12_pack_reviewer.md"


def _load_role_prompt() -> str:
    try:
        return _PACK_REVIEWER_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing pack_reviewer role prompt at {_PACK_REVIEWER_PATH}: {e}"
        ) from e


def _render_plan(stages: list[dict[str, Any]]) -> str:
    if not stages:
        return "(no plan stages)"
    out: list[str] = []
    for i, s in enumerate(stages):
        sid = s.get("stage_id") or f"S{i + 1}"
        out.append(
            f"- **{sid}** — {s.get('name', '?')}: {s.get('purpose') or s.get('description', '')}"
        )
        ftm = s.get("file_touch_map", {})
        if isinstance(ftm, dict):
            for label in ("create", "modify", "do_not_touch"):
                paths = ftm.get(label, []) or []
                if paths:
                    out.append(f"    - {label}: {', '.join(paths)}")
    return "\n".join(out)


def _render_contract(contract: dict[str, Any]) -> str:
    delivs = contract.get("deliverables", []) or []
    if not delivs:
        return "(no contract deliverables)"
    out: list[str] = []
    for d in delivs:
        out.append(
            f"- **{d.get('id', '?')}** — `{d.get('name', '?')}` — {d.get('description', '')}"
        )
        for c in d.get("success_criteria", []) or []:
            out.append(f"    - success: {c}")
    return "\n".join(out)


def build_reviewer_packet(state: PipelineState, diff_text: str) -> str:
    """Port of buildReviewerPacket — assembles the user message body
    for pack_reviewer.

    Includes plan + research summary + code summary + git diff. The
    role prompt itself carries the Fresh Eyes Hindsight instructions
    and the output schema; we just feed it the evidence.
    """
    contract = state.get("contract", {}) or {}
    plan_meta = state.get("plan_meta", {}) or {}
    stages = state.get("plan", []) or []
    research_brief = (state.get("research_brief", "") or "")[:6000]
    code_summary = state.get("code_summary", "") or "(no summary)"
    verify = state.get("verify", {}) or {}
    issue_title = state.get("issue_title", "?")
    issue_body = (state.get("issue_body", "") or "")[:3000]

    lines = [
        "## pack_reviewer task",
        "",
        "You are acting as pack_reviewer. Review the completed implementation against",
        "the contract and plan. Apply the Mandatory Fresh Eyes Hindsight check from",
        "your role prompt BEFORE forming a verdict. Return a single JSON object only.",
        "",
        "## Issue",
        "",
        f"**Title:** {issue_title}",
        "",
        "**Body:**",
        issue_body or "(empty body)",
        "",
        "## Contract deliverables",
        "",
        _render_contract(contract),
        "",
        "## Plan (stages executed)",
        "",
        _render_plan(stages),
        "",
        f"**Plan title:** {plan_meta.get('plan_title', '?')}",
        f"**Estimated risk:** {plan_meta.get('estimated_risk', '?')} — {plan_meta.get('risk_rationale', '')}",
        "",
        "## Research evidence (excerpt)",
        "",
        research_brief or "(no research brief)",
        "",
        "## Implementation summary (last stage's narration)",
        "",
        code_summary,
        "",
        "## Test results (verify node)",
        "",
        f"- **Passed:** {verify.get('passed', False)}",
        f"- **Summary:** {verify.get('summary', '(none)')}",
    ]
    if verify.get("failing_tests"):
        lines.append(f"- **Failing tests:** {', '.join(verify['failing_tests'])}")
    lines.extend(
        [
            "",
            "## Diff under review (git diff base)",
            "",
            "```diff",
            diff_text or "(empty diff)",
            "```",
            "",
            "## Required output (JSON only, no preamble)",
            "",
            "```json",
            "{",
            '  "must_fix": ["string", ...],',
            '  "should_fix": ["string", ...],',
            '  "notes": ["string", ...],',
            '  "passed": true | false,',
            '  "hindsight": "one sentence describing the alternative approach + MINOR|MATERIAL|BLOCKING classification",',
            '  "verification": "one sentence — how you confirmed your verdict"',
            "}",
            "```",
            "",
            "Rules:",
            "- passed=true ONLY if every must_fix is empty AND hindsight is not BLOCKING.",
            "- Tag findings with [must-fix], [should-fix], or [note] in the strings themselves.",
            "- Be specific: name files and line numbers from the diff.",
            "- Output JSON only. No markdown fence. No commentary outside the object.",
        ]
    )
    return "\n".join(lines)


def pack_reviewer_node(state: PipelineState) -> dict:
    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    diff_text = state.get("code_diff", "") or capture_diff(
        state["worktree_path"], state.get("base_branch", "main")
    )
    user_msg = build_reviewer_packet(state, diff_text)

    log.info("pack_reviewer: invoking claude (sonnet, fresh session)")
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="sonnet",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return {"error": f"pack_reviewer: claude call failed: {e}"}

    log.info(
        "pack_reviewer: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("pack_reviewer: parse failed: %s; head=%s", e, result.text[:300])
        # Fail-open with a marker verdict so downstream still has shape
        verdict = {
            "must_fix": [],
            "should_fix": [],
            "notes": [f"pack_reviewer parse failed: {e}"],
            "passed": False,
            "hindsight": "approach is sound (verdict could not be parsed)",
            "verification": "parse_failed",
        }
        return {"pack_review": verdict, "code_diff": diff_text, "error": None}
    if not isinstance(raw, dict):
        return {"error": f"pack_reviewer: expected JSON object, got {type(raw).__name__}"}

    hindsight_val = raw.get("hindsight", "")
    if isinstance(hindsight_val, dict):
        hindsight_str = (
            f"{hindsight_val.get('finding', '')} [{hindsight_val.get('classification', 'MINOR')}]"
            + (f" — {hindsight_val.get('note', '')}" if hindsight_val.get("note") else "")
        )
    else:
        hindsight_str = str(hindsight_val)

    verif_val = raw.get("verification", "")
    if isinstance(verif_val, dict):
        verif_str = str(verif_val.get("method") or verif_val.get("verified_complete", ""))
    else:
        verif_str = str(verif_val)

    verdict = {
        "must_fix": [str(x) for x in raw.get("must_fix", []) or []],
        "should_fix": [str(x) for x in raw.get("should_fix", []) or []],
        "notes": [str(x) for x in raw.get("notes", []) or []],
        "passed": bool(raw.get("passed", False)),
        "hindsight": hindsight_str,
        "verification": verif_str,
    }
    log.info(
        "pack_reviewer done: passed=%s must_fix=%d should_fix=%d notes=%d",
        verdict["passed"],
        len(verdict["must_fix"]),
        len(verdict["should_fix"]),
        len(verdict["notes"]),
    )
    return {"pack_review": verdict, "code_diff": diff_text, "error": None}
