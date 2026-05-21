"""Verify node: check whether the implementation satisfies the
acceptance criteria and the project's tests pass.

For MVP this is a single Claude call that:
1. Runs the project's tests (whatever they are — Claude figures it out)
2. Checks acceptance criteria against the diff
3. Returns a structured VerifyReport

If FAIL and retry_count < MAX_RETRIES, the graph loops back to CODE.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState, VerifyReport

log = logging.getLogger(__name__)

MAX_RETRIES = 2

PROMPT_TEMPLATE = """You are verifying a completed implementation. You have Bash / Read / Grep tools inside the worktree.

ACCEPTANCE CRITERIA (must ALL be satisfied):
{acceptance_criteria_bullets}

RESEARCH BRIEF (for context on conventions):
{research_brief_head}

IMPLEMENTATION SUMMARY:
{code_summary}

Your job, in order:
1. Run the project's tests. Detect the test command yourself (look for `pytest`, `npm test`, `jest`, `cargo test`, `go test`, or whatever fits the repo). Wrap any long-running test command in `timeout --kill-after=5 600`.
2. Read `git diff --stat` and `git diff` to see what changed.
3. For each acceptance criterion, decide PASS or FAIL based on the code + test output.

Return VALID JSON only — no preamble, no markdown fence:

{{
  "passed": true | false,
  "summary": "one sentence overall verdict",
  "failing_tests": ["test_name_1", "test_name_2"],
  "suggested_fix": "if passed=false, one paragraph: what specifically to change. Empty string if passed=true."
}}

Rules:
- passed=true ONLY if tests run AND pass AND every acceptance criterion is satisfied.
- If the repo has no tests at all, that's fine — still pass if criteria are met. Note it in summary.
- If a test failure looks pre-existing (unrelated to this change), say so in summary and still pass.

Begin:
"""


def verify_node(state: PipelineState) -> dict:
    intake = state.get("intake", {})
    research = state.get("research_brief", "")
    prompt = PROMPT_TEMPLATE.format(
        acceptance_criteria_bullets="\n".join(
            f"  - {c}" for c in intake.get("acceptance_criteria", [])
        )
        or "  (none — auto-pass)",
        research_brief_head=research[:2000],
        code_summary=state.get("code_summary", "(no summary)"),
    )
    log.info("verify: invoking claude")
    result = run_claude(
        prompt,
        cwd=state["worktree_path"],
        timeout_s=900,
    )
    log.info("verify: claude returned (%.1fs, cost=$%.4f, turns=%d)", result.duration_s, result.cost_usd, result.num_turns)

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {"error": f"verify parse failed: {e}; text head: {result.text[:300]}"}
    if not isinstance(raw, dict):
        return {"error": f"verify: expected JSON object, got {type(raw).__name__}"}

    report: VerifyReport = {
        "passed": bool(raw.get("passed", False)),
        "summary": str(raw.get("summary", "")),
        "failing_tests": [str(t) for t in raw.get("failing_tests", []) or []],
        "suggested_fix": str(raw.get("suggested_fix", "")),
    }
    log.info(
        "verify done: passed=%s summary=%s",
        report["passed"],
        report["summary"][:80],
    )
    return {"verify": report, "error": None}


def should_retry(state: PipelineState) -> str:
    """LangGraph conditional edge function. Returns next node name."""
    verify = state.get("verify", {})
    if verify.get("passed", False):
        return "pr"
    retry = state.get("retry_count", 0)
    if retry >= MAX_RETRIES:
        log.warning("verify failed and max retries (%d) reached — proceeding to pr anyway", MAX_RETRIES)
        return "pr"
    log.info("verify failed, looping back to code (retry %d/%d)", retry + 1, MAX_RETRIES)
    return "retry_code"
