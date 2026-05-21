"""Verify node (v0.3): run the project's tests and report pass/fail.

v0.2 verify also tried to judge acceptance criteria. That job has moved
to the governance_reviewer (which sees the diff plus all prior verdicts).
This node is now narrow: detect the test command, run it, parse the
result. Tests passing is necessary but not sufficient for release —
the reviewers downstream decide everything else.

Test execution still goes through `claude --print` rather than a
hardcoded `pytest` call because the pipeline doesn't know what stack
the target repo uses. Claude picks the test command from the repo
conventions. The model output is small and structured.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.state import PipelineState, VerifyReport

log = logging.getLogger(__name__)

# Kept for backward compatibility with any caller that imports MAX_RETRIES,
# though the v0.3 flow no longer loops back from verify to code (the
# reviewer ladder + governance_repair handles repair).
MAX_RETRIES = 2

PROMPT_TEMPLATE = """You are running the project's tests inside the worktree. You have Bash / Read / Grep / Glob tools.

Your one job: detect the test command for THIS repo and run it. Be honest about the result.

Steps:
1. Detect the test runner. Look for: `pytest` + tests/, `npm test` / `jest`, `cargo test`, `go test`, `make test`. Skip integration suites if there's a clear unit-only subset.
2. Run the unit/test suite. ALWAYS wrap the command in `timeout --kill-after=5 600` so a hang doesn't waste the pipeline's budget.
3. Capture: did tests pass? How many failing? Any obvious pre-existing failures (unrelated to the recent diff)?

Return VALID JSON only — no preamble, no markdown fence:

{{
  "passed": true | false,
  "summary": "one sentence — what command ran and what happened",
  "failing_tests": ["test_name_1", "test_name_2"],
  "suggested_fix": "if passed=false, one paragraph: what specifically to change. Empty string if passed=true."
}}

Rules:
- passed=true if the test command exited 0 (or repo has no tests — note that in summary).
- passed=false if any test failed, even pre-existing. Note pre-existing failures in summary; downstream reviewers decide if they're blocking.
- Do NOT modify any files. Read-only.
"""


def verify_node(state: PipelineState) -> dict:
    prompt = PROMPT_TEMPLATE
    log.info("verify: invoking claude (tests only)")
    try:
        result = run_claude(
            prompt,
            cwd=state["worktree_path"],
            timeout_s=900,
            model="sonnet",
        )
    except ClaudeError as e:
        return {"error": f"verify: claude call failed: {e}"}
    log.info(
        "verify: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        # Don't hard-fail — log and treat as unknown / not-passed.
        log.warning("verify: parse failed: %s; head=%s", e, result.text[:300])
        report: VerifyReport = {
            "passed": False,
            "summary": f"verify parse failed: {e}",
            "failing_tests": [],
            "suggested_fix": "(verify could not parse Claude's output; review manually)",
        }
        return {"verify": report, "error": None}
    if not isinstance(raw, dict):
        return {"error": f"verify: expected JSON object, got {type(raw).__name__}"}

    report = {
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
    """Legacy conditional edge function (v0.2). Kept so existing imports
    don't break, but v0.3 graph wiring routes verify straight to the
    reviewer ladder regardless of test outcome — reviewers need to see
    failing tests as evidence."""
    return "pr"  # unused in v0.3 graph
