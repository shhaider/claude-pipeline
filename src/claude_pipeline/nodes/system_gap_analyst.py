"""system_gap_analyst node: adversarial Tier-3 pre-lane for the plan phase.

Applies 8 adversarial lenses to intake + research before the contract writer
runs, surfacing blocking and advisory gaps in the proposed plan.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..claude import extract_json, run_claude

log = logging.getLogger(__name__)

_PROMPT_PATH = (
    Path(__file__).resolve().parents[3] / "prompts" / "metabuilder" / "35_system_gap_analyst.md"
)

_EMPTY_GAPS: dict = {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}


def build_gap_analysis_packet(state: dict) -> str:
    intake = state.get("intake", {}) or {}
    research_brief = state.get("research_brief", "") or ""
    codebase_anchor = state.get("codebaseAnchor", "") or ""

    risk_flags = intake.get("risk_flags", []) or []
    acceptance_criteria = intake.get("acceptance_criteria", []) or []

    return f"""\
## Intake Decisions

- task_type: {intake.get("task_type", "(not set)")}
- complexity_tier: {intake.get("complexity_tier", "(not set)")}
- scope_plan: {intake.get("scope_plan", "(not set)")}
- right_thing_answer: {intake.get("right_thing_answer", "(not set)")}
- wiring_plan: {intake.get("wiring_plan", "(not set)")}
- risk_flags: {", ".join(risk_flags) if risk_flags else "(none)"}
- acceptance_criteria:
{chr(10).join(f"  - {c}" for c in acceptance_criteria) if acceptance_criteria else "  (none)"}

## Research Brief

{research_brief if research_brief else "(not yet available)"}

## codebaseAnchor

{codebase_anchor if codebase_anchor else "(not provided)"}

## Adversarial Lens Checklist

Apply all eight lenses to the intake and research above. For each, report every
gap found — do not self-censor.

1. infrastructure-assumed-but-not-mentioned — every implicit infrastructure dep the plan relies on without stating it
2. silent-failure — every point where an error could be swallowed or cause a downstream step to proceed on bad data
3. cross-cutting-concerns — concerns affecting multiple stages addressed in none (auth, logging, retries, locking)
4. next-stage-prerequisites — stage-to-stage handoff schema mismatches or missing fields between consecutive stages
5. YAGNI-cut — speculative elements with no corresponding verifiable acceptance criterion
6. fake-completion — scenarios where acceptance criteria pass green while the feature is actually broken for real usage
7. architecture-smell — structural decisions that cause disproportionate pain at scale or future-change cost
8. developer-contract-completeness — every interface boundary (TypedDict fields, CLI flags, file formats, env contracts) that is underspecified

Respond with the JSON schema defined in your system prompt.
"""


def system_gap_analyst_node(state: dict) -> dict:
    prompt_text = _PROMPT_PATH.read_text(encoding="utf-8")
    packet = build_gap_analysis_packet(state)

    log.info("system_gap_analyst: invoking claude (Tier-3 adversarial gap pass)")
    try:
        result = run_claude(
            packet,
            model="claude-opus-4-7",
            extra_args=["--append-system-prompt", prompt_text],
        )
    except Exception as exc:
        log.error("system_gap_analyst: run_claude failed: %s", exc)
        return {"gap_analysis": dict(_EMPTY_GAPS), "error": f"system_gap_analyst: {exc}"}

    try:
        parsed = extract_json(result.text)
    except (ValueError, TypeError) as exc:
        log.error("system_gap_analyst: JSON parse failed: %s", exc)
        return {
            "gap_analysis": dict(_EMPTY_GAPS),
            "error": f"system_gap_analyst: JSON parse failed: {exc}",
        }

    if not isinstance(parsed, dict):
        return {
            "gap_analysis": dict(_EMPTY_GAPS),
            "error": f"system_gap_analyst: expected dict, got {type(parsed).__name__}",
        }

    gap_analysis = {
        "blocking_gaps": parsed.get("blocking_gaps") or [],
        "advisory_gaps": parsed.get("advisory_gaps") or [],
        "summary": parsed.get("summary") or "",
    }

    log.info(
        "system_gap_analyst done: %d blocking, %d advisory (%.1fs, cost=$%.4f, turns=%d)",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )
    return {"gap_analysis": gap_analysis, "error": None}
