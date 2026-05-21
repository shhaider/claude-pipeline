"""Intake node: 7-decision autonomous resolver, ported from metabuilder.

Verbatim port of `skills/metabuilder/intake/autonomous_software_resolver.js`
lines 65-83 (the inline JS prompt template), with deterministic fallback
heuristics on parse / timeout failure (HEURISTIC_DEFAULTS).

LLM params (per port spec): model=Opus, T=0.3, max_tokens=1000, 30s timeout.
The metabuilder version posts directly to a proxy at 127.0.0.1:4020; this
port routes through the standard `claude --print` CLI instead. The CLI does
not expose temperature/max_tokens at the print level, so we rely on its
defaults plus the explicit JSON-only instruction in the prompt.
"""

from __future__ import annotations

import json
import logging

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.state import IntakeDecisions, PipelineState

log = logging.getLogger(__name__)

# Verbatim from autonomous_software_resolver.js lines 65-83. The only
# substitution is python-style {} for JS ${}.
PROMPT_TEMPLATE = """You are a software development intake specialist. The user wants you to make ALL decisions for their task.

CONTEXT: {context_json}
HISTORY: {history_str}

Resolve these 7 decisions. For each: value, one-sentence reasoning, confidence 0-1.
1. task_type - bug_fix / new_feature / refactor / test_addition / documentation / exploration
2. complexity_tier - 1 (trivial), 2 (moderate), 3 (complex)
3. scope_plan - single task or subphases? One sentence
4. risk_flags - array from: auth, db_schema, api_contract, llm_routing, concurrency, security
5. right_thing_answer - is this the right thing to build? One sentence
6. acceptance_criteria - array of 3 testable criteria
7. wiring_plan - which existing modules this touches

Respond with VALID JSON only:
{{"decisions": [{{"field":"task_type","value":"...","reasoning":"...","confidence":0.85}}, ...]}}
"""


# Deterministic fallback used when LLM parse / timeout fails.
# Ports `buildFallbackDecisions(partialPayload)` from the JS resolver.
HEURISTIC_DEFAULTS = {
    "task_type": "new_feature",
    "complexity_tier": 2,
    "scope_plan": "Single task, no subphase split.",
    "risk_flags": [],
    "right_thing_answer": (
        "Heuristic fallback — proceed with the literal request as stated."
    ),
    "acceptance_criteria": [
        "Implementation compiles and passes the project's existing tests.",
        "No previously-passing test starts failing.",
        "The change does what the issue body asks for.",
    ],
    "wiring_plan": (
        "Heuristic fallback — unknown wiring; implementer must inspect "
        "the worktree and decide which modules to touch."
    ),
}

REQUIRED_FIELDS = {
    "task_type",
    "complexity_tier",
    "scope_plan",
    "risk_flags",
    "right_thing_answer",
    "acceptance_criteria",
    "wiring_plan",
}


def _decisions_array_to_dict(raw: dict) -> dict:
    """Normalize metabuilder's `decisions[{field,value,reasoning,confidence}]`
    shape down to a flat `{field: value}` dict.

    Also accepts the already-flat shape (older / simpler variants).
    """
    if "decisions" in raw and isinstance(raw["decisions"], list):
        flat: dict = {}
        for d in raw["decisions"]:
            if not isinstance(d, dict):
                continue
            field = d.get("field")
            if not field:
                continue
            flat[field] = d.get("value")
        return flat
    # Already flat
    return {k: raw.get(k) for k in REQUIRED_FIELDS}


def _coerce_int_tier(v: object) -> int:
    """complexity_tier may arrive as int, str ("2"), or "tier 2". Coerce."""
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        for tok in v.split():
            if tok.isdigit():
                return int(tok)
        if v.isdigit():
            return int(v)
    return 2  # safe default


def _coerce_str_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str) and v.strip():
        # comma-separated fallback
        return [s.strip() for s in v.split(",") if s.strip()]
    return []


def _build_partial_payload(state: PipelineState) -> dict:
    """Mirror metabuilder's partialPayload — the snapshot the resolver
    sees before resolving. For this pipeline that's the issue."""
    return {
        "repo": state.get("repo", ""),
        "issue_number": state.get("issue_number"),
        "issue_title": state.get("issue_title", ""),
        "issue_body": state.get("issue_body", ""),
    }


def _intake_with_heuristic_fallback(state: PipelineState, reason: str) -> dict:
    """Build a state-slice using HEURISTIC_DEFAULTS, logging the reason."""
    log.warning("intake: falling back to heuristic defaults — %s", reason)
    decisions: IntakeDecisions = dict(HEURISTIC_DEFAULTS)  # type: ignore[assignment]
    return {"intake": decisions, "error": None}


def intake_node(state: PipelineState) -> dict:
    """Read issue, return state slice with intake decisions."""
    partial_payload = _build_partial_payload(state)
    prompt = PROMPT_TEMPLATE.format(
        context_json=json.dumps(partial_payload, indent=2),
        history_str="(no prior intake history for this run)",
    )
    log.info(
        "intake: invoking claude (opus) for issue #%d",
        state.get("issue_number", 0),
    )
    try:
        result = run_claude(
            prompt,
            cwd=state.get("worktree_path"),
            timeout_s=120,  # was 300; resolver is cheap, fail fast
            model="opus",
        )
    except ClaudeError as e:
        return _intake_with_heuristic_fallback(state, f"LLM call failed: {e}")

    log.info(
        "intake: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("intake: result.text was unparseable: %s", e)
        return _intake_with_heuristic_fallback(state, f"JSON parse failed: {e}")

    if not isinstance(raw, dict):
        return _intake_with_heuristic_fallback(
            state, f"expected JSON object, got {type(raw).__name__}"
        )

    flat = _decisions_array_to_dict(raw)
    missing = REQUIRED_FIELDS - {k for k, v in flat.items() if v is not None}
    if missing:
        # Per metabuilder: partial → fill from heuristics, don't hard-fail.
        log.warning("intake: missing fields %s — backfilling from heuristics", sorted(missing))
        for k in missing:
            flat[k] = HEURISTIC_DEFAULTS[k]

    decisions: IntakeDecisions = {
        "task_type": str(flat["task_type"]),
        "complexity_tier": _coerce_int_tier(flat["complexity_tier"]),
        "scope_plan": str(flat["scope_plan"]),
        "risk_flags": _coerce_str_list(flat["risk_flags"]),
        "right_thing_answer": str(flat["right_thing_answer"]),
        "acceptance_criteria": _coerce_str_list(flat["acceptance_criteria"]),
        "wiring_plan": str(flat["wiring_plan"]),
    }
    log.info(
        "intake done: task_type=%s tier=%d criteria=%d",
        decisions["task_type"],
        decisions["complexity_tier"],
        len(decisions["acceptance_criteria"]),
    )
    return {"intake": decisions, "error": None}
