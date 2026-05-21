"""Intake node: take the raw GitHub issue and produce 7 structured
decisions about what kind of work this is.

Mirrors metabuilder's `autonomous_software_resolver.js` in shape.
Future enhancement (filed as an upgrade issue against this repo):
multi-turn clarification when confidence is low.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import IntakeDecisions, PipelineState

log = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a software intake specialist. Read the GitHub issue below and produce 7 structured decisions about how to handle it.

REPO: {repo}
ISSUE #{issue_number}: {issue_title}

ISSUE BODY:
{issue_body}

Produce VALID JSON ONLY — no prose, no markdown fence, no preamble. The shape:

{{
  "task_type": "bug_fix | new_feature | refactor | test_addition | documentation | exploration",
  "complexity_tier": 1 | 2 | 3,
  "scope_plan": "one sentence describing scope and whether to split into subphases",
  "risk_flags": ["auth", "db_schema", "api_contract", "llm_routing", "concurrency", "security"],
  "right_thing_answer": "one sentence: is this the right thing to build, or is there a better framing?",
  "acceptance_criteria": ["testable criterion 1", "testable criterion 2", "testable criterion 3"],
  "wiring_plan": "which existing modules will this touch; one paragraph"
}}

Rules:
- complexity_tier: 1 = trivial (single file, no design choices), 2 = moderate (a few files, clear shape), 3 = complex (many files, design choices needed)
- risk_flags: include ONLY the categories that genuinely apply. Empty array if none.
- acceptance_criteria: each must be objectively verifiable (a test would pass/fail it)
- right_thing_answer: if the issue is misframed, say so and propose what to do instead

JSON only. Begin:
"""


def intake_node(state: PipelineState) -> dict:
    """Read issue, return state slice with intake decisions."""
    prompt = PROMPT_TEMPLATE.format(
        repo=state["repo"],
        issue_number=state["issue_number"],
        issue_title=state.get("issue_title", "(no title)"),
        issue_body=state.get("issue_body", "(no body)"),
    )
    log.info("intake: invoking claude for issue #%d", state["issue_number"])
    result = run_claude(
        prompt,
        cwd=state.get("worktree_path"),
        timeout_s=300,
    )
    log.info("intake: claude returned (%.1fs, cost=$%.4f)", result.duration_s, result.cost_usd)

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.exception("intake: result.text was unparseable")
        return {
            "error": f"intake parse failed: {e}; text head: {result.text[:300]}",
        }
    if not isinstance(raw, dict):
        return {"error": f"intake: expected JSON object, got {type(raw).__name__}"}

    required = {
        "task_type",
        "complexity_tier",
        "scope_plan",
        "risk_flags",
        "right_thing_answer",
        "acceptance_criteria",
        "wiring_plan",
    }
    missing = required - set(raw.keys())
    if missing:
        return {"error": f"intake missing required fields: {sorted(missing)}"}

    decisions: IntakeDecisions = {
        "task_type": str(raw["task_type"]),
        "complexity_tier": int(raw["complexity_tier"]),
        "scope_plan": str(raw["scope_plan"]),
        "risk_flags": list(raw["risk_flags"]),
        "right_thing_answer": str(raw["right_thing_answer"]),
        "acceptance_criteria": list(raw["acceptance_criteria"]),
        "wiring_plan": str(raw["wiring_plan"]),
    }
    log.info(
        "intake done: task_type=%s tier=%d criteria=%d",
        decisions["task_type"],
        decisions["complexity_tier"],
        len(decisions["acceptance_criteria"]),
    )
    return {"intake": decisions, "error": None}
