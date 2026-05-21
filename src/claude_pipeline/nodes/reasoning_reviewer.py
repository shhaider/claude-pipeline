"""software_reasoning_reviewer node — v0.3 simplification of metabuilder's 8b.

System prompt: `prompts/metabuilder/34_software_reasoning_reviewer.md`.
This reviewer is narrow: it ONLY looks for the 8 categories listed in
the role prompt:
  1. hot-path-bypass
  2. fake-complete
  3. interface-error
  4. dependency-inversion
  5. error-suppression
  6. schema-drift (schema coherence drift)
  7. implicit-interface  (port note: role prompt calls it
     "implicit interface contracts" — kept distinct from schema-drift)
  8. policy-bypass

Output JSON:
  {
    reasoning_verdict: "PASS|CONCERN|FAIL",
    overall_assessment: str,
    concerns: [{category, severity, description, fix}, ...],
    blocking_concerns: [str, ...]
  }

LLM params: Tier 3 / Opus, max_tokens 8192, T=0.2.
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
_REASONING_PATH = _PROMPTS_DIR / "34_software_reasoning_reviewer.md"


def _load_role_prompt() -> str:
    try:
        return _REASONING_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing software_reasoning_reviewer role prompt at {_REASONING_PATH}: {e}"
        ) from e


def _render_expanded_prompts(stages: list[dict[str, Any]]) -> str:
    """Inline the expanded prompts the implementer received. The reasoning
    reviewer's whole edge is reading those prompts for subtle drift, not
    just the diff."""
    parts: list[str] = []
    for i, s in enumerate(stages):
        sid = s.get("stage_id") or f"S{i + 1}"
        name = s.get("name", "?")
        prompt_text = s.get("expanded_prompt") or ""
        if not prompt_text and s.get("prompt_path"):
            try:
                prompt_text = Path(s["prompt_path"]).read_text(encoding="utf-8")
            except OSError:
                prompt_text = ""
        # Cap per-stage at 8 KB so we don't blow context with 5 stages
        if len(prompt_text) > 8000:
            prompt_text = prompt_text[:8000] + "\n\n[... truncated ...]"
        parts.append(f"### Stage {sid} — {name}\n\n```\n{prompt_text or '(no expanded prompt)'}\n```")
    return "\n\n".join(parts) or "(no stages)"


def build_reasoning_review_packet(state: PipelineState, diff_text: str) -> str:
    stages = state.get("plan", []) or []
    contract = state.get("contract", {}) or {}
    delivs = contract.get("deliverables", []) or []
    verify = state.get("verify", {}) or {}
    pack = state.get("pack_review", {}) or {}

    deliv_lines: list[str] = []
    for d in delivs:
        deliv_lines.append(f"- {d.get('id', '?')}: {d.get('name', '?')} — {d.get('description', '')}")

    lines = [
        "## software_reasoning_reviewer task",
        "",
        "You are acting as software_reasoning_reviewer. Your job is narrow: find",
        "subtle reasoning mistakes from the 8 categories in your role prompt.",
        "Do NOT review style, completeness, or governance — those are other roles.",
        "",
        "## Categories to scan for (named verbatim in your role prompt)",
        "",
        "1. hot-path-bypass — assumed live but only conditional",
        "2. fake-complete — looks done but skips the hard case silently",
        "3. interface-error — wrong signature / wrong function name",
        "4. dependency-inversion — calling test-only or unbuilt modules from live",
        "5. error-suppression — try/catch that swallows what should surface",
        "6. schema-drift — field-name mismatch between writer and reader",
        "7. policy-bypass — task_class / source class / gate mismatch",
        "8. anchor-drift — code references an anchor/identifier that doesn't exist in the repo",
        "",
        "## Contract deliverables",
        "",
        "\n".join(deliv_lines) or "(none)",
        "",
        "## Expanded implementation prompts (what the coder was told)",
        "",
        _render_expanded_prompts(stages),
        "",
        "## Diff under review",
        "",
        "```diff",
        diff_text or "(empty diff)",
        "```",
        "",
        "## Test results (verify node)",
        "",
        f"- **Passed:** {verify.get('passed', False)}",
        f"- **Summary:** {verify.get('summary', '(none)')}",
        "",
        "## pack_reviewer verdict (for cross-reference, NOT to relitigate)",
        "",
        f"- passed: {pack.get('passed', '?')}",
        f"- must_fix count: {len(pack.get('must_fix', []) or [])}",
        f"- hindsight: {pack.get('hindsight', '(none)')}",
        "",
        "## Required output (JSON only)",
        "",
        "```json",
        "{",
        '  "reasoning_verdict": "PASS" | "CONCERN" | "FAIL",',
        '  "overall_assessment": "one paragraph",',
        '  "concerns": [',
        "    {",
        '      "category": "hot-path-bypass | fake-complete | interface-error | dependency-inversion | error-suppression | schema-drift | policy-bypass | anchor-drift",',
        '      "severity": "must-fix | should-fix | note",',
        '      "description": "specific failure mode — name files/functions",',
        '      "fix": "smallest specific change"',
        "    }",
        "  ],",
        '  "blocking_concerns": ["concise titles of must-fix concerns only"]',
        "}",
        "```",
        "",
        "Rules:",
        "- reasoning_verdict=PASS only if blocking_concerns is empty.",
        "- reasoning_verdict=CONCERN if there are should-fix / note items but no must-fix.",
        "- reasoning_verdict=FAIL if any concern has severity=must-fix.",
        "- Stay inside the 8 categories. Do NOT raise style/format/test-quality concerns.",
        "- Output JSON only. No markdown fence. No commentary outside the object.",
    ]
    return "\n".join(lines)


def reasoning_reviewer_node(state: PipelineState) -> dict:
    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    diff_text = state.get("code_diff", "") or capture_diff(
        state["worktree_path"], state.get("base_branch", "main")
    )
    user_msg = build_reasoning_review_packet(state, diff_text)

    log.info("reasoning_reviewer: invoking claude (opus, fresh session)")
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="opus",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return {"error": f"reasoning_reviewer: claude call failed: {e}"}

    log.info(
        "reasoning_reviewer: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning(
            "reasoning_reviewer: parse failed: %s; head=%s", e, result.text[:300]
        )
        verdict = {
            "reasoning_verdict": "CONCERN",
            "overall_assessment": f"reasoning_reviewer parse failed: {e}",
            "concerns": [],
            "blocking_concerns": [],
        }
        return {"reasoning_review": verdict, "code_diff": diff_text, "error": None}
    if not isinstance(raw, dict):
        return {
            "error": f"reasoning_reviewer: expected JSON object, got {type(raw).__name__}"
        }

    concerns_in = raw.get("concerns", []) or []
    concerns: list[dict[str, str]] = []
    for c in concerns_in:
        if not isinstance(c, dict):
            continue
        concerns.append(
            {
                "category": str(c.get("category", "")),
                "severity": str(c.get("severity", "")),
                "description": str(c.get("description", "")),
                "fix": str(c.get("fix", "")),
            }
        )
    verdict = {
        "reasoning_verdict": str(raw.get("reasoning_verdict", "CONCERN")).upper(),
        "overall_assessment": str(raw.get("overall_assessment", "")),
        "concerns": concerns,
        "blocking_concerns": [str(x) for x in raw.get("blocking_concerns", []) or []],
    }
    log.info(
        "reasoning_reviewer done: verdict=%s concerns=%d blocking=%d",
        verdict["reasoning_verdict"],
        len(verdict["concerns"]),
        len(verdict["blocking_concerns"]),
    )
    return {"reasoning_review": verdict, "code_diff": diff_text, "error": None}
