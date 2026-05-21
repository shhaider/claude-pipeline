"""system_gap_analyst node — adversarial pre-lane.

Runs BETWEEN research and contract/plan. Applies 8 named adversarial lenses
to the intake + research output to surface unstated dependencies, silent-
failure modes, and architectural smells that the contract_writer MUST cover
(blocking) or SHOULD consider (advisory).

Ported from metabuilder's `system_gap_analyst` role + `buildGapAnalysisPacket`
(see docs/metabuilder-port-spec.md §plan-3a).

LLM params: Tier 3 (Opus) / temperature 0.2 / max_tokens 8192 / fresh session.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

# Path to the verbatim role prompt, relative to the repo root.
_PROMPT_REL_PATH = "prompts/metabuilder/35_system_gap_analyst.md"

# The 8 lenses, verbatim. These get spelled out in the user packet so the
# model sees them even if the role prompt is somehow truncated.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "Does the framing assume a database, queue, secret store, scheduled "
        "job, IAM permission, env var, deploy step, or service dependency "
        "that is not named in intake or research?",
    ),
    (
        "silent-failure",
        "What code paths could fail without raising, logging, or surfacing "
        "a test failure? (bare except, fire-and-forget tasks, wrong-but-"
        "plausible defaults, retries that mask permanent failure.)",
    ),
    (
        "cross-cutting-concerns",
        "Does the framing touch a subsystem that requires coordinated "
        "changes elsewhere? (migration + ORM + serializer + admin + tests; "
        "API field + spec + client regen + consumer notice.)",
    ),
    (
        "next-stage-prerequisites",
        "Does this task unblock known next-stage work, and does the "
        "contract leave the next stage with a hook to land into?",
    ),
    (
        "YAGNI-cut",
        "What does the framing include that should NOT be built right now? "
        "Flag scope with no acceptance criterion attached.",
    ),
    (
        "fake-completion",
        "What would let an implementer call this 'done' while user-visible "
        "behavior is still broken? (stub returns, asserts-ran-not-effect, "
        "flagged-off-no-flip-plan.)",
    ),
    (
        "architecture-smell",
        "Does the framing push the codebase toward an anti-pattern? "
        "(god-modules, circular imports, business logic in controllers, "
        "untyped state through four layers.)",
    ),
    (
        "developer-contract-completeness",
        "Does the deliverable list the contract_writer is about to produce "
        "have everything a downstream implementer needs to be unambiguous? "
        "(acceptance criteria, file_touch_map, success conditions.)",
    ),
]


def _load_role_prompt(worktree_path: str | Path) -> str:
    """Load the verbatim role prompt from prompts/metabuilder/.

    Tries the worktree first (the issue spec keeps prompts in-repo), then
    walks up from this file as a fallback. Raises FileNotFoundError if
    neither location has it — the node is useless without the role prompt.
    """
    candidates = [
        Path(worktree_path) / _PROMPT_REL_PATH,
        Path(__file__).resolve().parents[3] / _PROMPT_REL_PATH,
    ]
    for p in candidates:
        if p.is_file():
            return p.read_text()
    raise FileNotFoundError(
        f"system_gap_analyst role prompt not found at any of: {candidates}"
    )


def _format_codebase_anchor(research_brief: str | dict) -> str:
    """Extract a codebase anchor block from research output.

    Metabuilder's buildResearchPacket returns JSON with `sources_consulted`
    and `implementation_details` fields. This pipeline's current research
    node returns a free-form markdown brief instead (see nodes/research.py),
    so we accept either shape: if the brief is a dict with those keys, we
    extract them; otherwise we use the full brief as the anchor.

    Once the research node is upgraded (roadmap item #3) to return the
    JSON shape, this function picks the structured fields up automatically.
    """
    if isinstance(research_brief, dict):
        sources = research_brief.get("sources_consulted") or []
        impl = research_brief.get("implementation_details") or []
        lines = ["## codebaseAnchor"]
        if sources:
            lines.append("")
            lines.append("**Sources consulted:**")
            lines.extend(f"- {s}" for s in sources)
        if impl:
            lines.append("")
            lines.append("**Implementation details:**")
            lines.extend(f"- {d}" for d in impl)
        if len(lines) == 1:
            lines.append("")
            lines.append("(no structured sources/details in research output)")
        return "\n".join(lines)

    text = (research_brief or "").strip()
    return (
        "## codebaseAnchor\n\n"
        "(research output is a free-form brief — anchor is the full brief)\n\n"
        f"{text}"
        if text
        else "## codebaseAnchor\n\n(no research output available)"
    )


def _format_lenses() -> str:
    lines = ["## The 8 adversarial lenses (apply each in order)"]
    for i, (name, prompt) in enumerate(LENSES, start=1):
        lines.append("")
        lines.append(f"**{i}. {name}** — {prompt}")
    return "\n".join(lines)


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user message for system_gap_analyst.

    Mirrors metabuilder's `buildGapAnalysisPacket`. Contents:
      - intake decisions (verbatim JSON)
      - research brief / output (verbatim)
      - codebaseAnchor block (sources_consulted + implementation_details)
      - the 8 named lenses spelled out
      - the output JSON schema
    """
    intake = state.get("intake", {}) or {}
    research = state.get("research_brief", "") or ""
    codebase_anchor = _format_codebase_anchor(research)
    # Render the research brief section: dict → pretty-printed JSON,
    # str → verbatim. Anything else falls back to repr().
    if isinstance(research, dict):
        research_section = "```json\n" + json.dumps(research, indent=2) + "\n```"
    elif isinstance(research, str):
        research_section = research if research else "(no research brief available)"
    else:
        research_section = repr(research)
    lenses = _format_lenses()

    parts = [
        "# Gap Analysis Task",
        "",
        "You are acting as system_gap_analyst BEFORE the contract_writer "
        "produces a deliverables contract. Apply each of the 8 lenses below "
        "to the intake + research output and emit gaps the contract MUST "
        "(blocking) or SHOULD (advisory) cover.",
        "",
        f"**Initiative:** issue #{state.get('issue_number', '?')} — "
        f"{state.get('issue_title', '')}",
        "",
        "## Intake decisions",
        "",
        "```json",
        json.dumps(intake, indent=2),
        "```",
        "",
        "## Research brief",
        "",
        research_section,
        "",
        codebase_anchor,
        "",
        lenses,
        "",
        "## Output schema",
        "",
        "Return a single JSON object (no fence, no prose) with this shape:",
        "",
        "```json",
        "{",
        '  "blocking_gaps": [',
        '    {"lens": "<lens-name>", "gap": "<...>", "recommendation": "<...>"}',
        "  ],",
        '  "advisory_gaps": [',
        '    {"lens": "<lens-name>", "gap": "<...>", "recommendation": "<...>"}',
        "  ],",
        '  "summary": "<2-3 sentence overall risk summary>"',
        "}",
        "```",
        "",
        "Begin:",
    ]
    return "\n".join(parts)


def _normalize_gaps(raw: object) -> list[dict]:
    """Coerce the model's gap list into a list[dict] with str fields.

    Drops items that don't have all three required fields. Defensive against
    the model returning a single dict instead of a list, or omitting fields.
    """
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        lens = item.get("lens")
        gap = item.get("gap")
        rec = item.get("recommendation")
        if not (lens and gap and rec):
            continue
        out.append(
            {
                "lens": str(lens),
                "gap": str(gap),
                "recommendation": str(rec),
            }
        )
    return out


def parse_gap_analysis_result(text: str) -> dict:
    """Parse the model's JSON output into a normalized gap_analysis dict.

    Always returns a dict with keys {blocking_gaps, advisory_gaps, summary}.
    On parse failure, returns an empty-but-well-shaped dict so downstream
    nodes don't crash — the pipeline degrades gracefully when this lane
    misfires.
    """
    try:
        parsed = extract_json(text)
    except (ValueError, json.JSONDecodeError):
        log.warning("system_gap_analyst: failed to parse JSON; defaulting to empty")
        return {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}

    if not isinstance(parsed, dict):
        log.warning(
            "system_gap_analyst: expected JSON object, got %s; defaulting to empty",
            type(parsed).__name__,
        )
        return {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}

    return {
        "blocking_gaps": _normalize_gaps(parsed.get("blocking_gaps")),
        "advisory_gaps": _normalize_gaps(parsed.get("advisory_gaps")),
        "summary": str(parsed.get("summary") or ""),
    }


def system_gap_analyst_node(state: PipelineState) -> dict:
    """LangGraph node entry point.

    Loads the role prompt, builds the packet, invokes claude with a fresh
    session at Tier 3 (Opus, T=0.2, max_tokens=8192), parses JSON, returns
    {"gap_analysis": dict}. On any failure, returns an empty gap_analysis
    rather than crashing the pipeline — gap analysis is an enhancement, not
    a hard requirement.
    """
    role_prompt = _load_role_prompt(state["worktree_path"])
    packet = build_gap_analysis_packet(state)

    log.info("system_gap_analyst: invoking claude (Tier 3 / Opus)")
    result = run_claude(
        packet,
        cwd=state["worktree_path"],
        timeout_s=600,
        model="claude-opus-4-7",
        extra_args=[
            "--append-system-prompt",
            role_prompt,
        ],
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    gap_analysis = parse_gap_analysis_result(result.text)
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
