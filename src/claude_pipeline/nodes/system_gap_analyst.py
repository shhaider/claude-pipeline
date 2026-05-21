"""system_gap_analyst node — adversarial pre-lane before contract_writer.

Ports metabuilder's `system_gap_analyst` role (prompts/metabuilder/
35_system_gap_analyst.md) + `buildGapAnalysisPacket`. Applies 8 named
lenses to the intake + research output to surface unstated dependencies,
silent-failure modes, and architectural smells BEFORE planning starts.

Output (persisted to state["gap_analysis"]):
    {
      "blocking_gaps":  [{lens, gap, recommendation}, ...],
      "advisory_gaps":  [{lens, gap, recommendation}, ...],
      "summary":        str,
    }

Blocking gaps are injected by the downstream contract_writer (the plan
node, while the contract/planner split lands later) as MANDATORY
additional deliverables. Advisory gaps are passed as suggestions.

Fresh session, no resume. Model is pinned to Opus (Tier 3) via
`--model`. Temperature 0.2 and max_tokens 8192 are the canonical
metabuilder tier-3 settings (see docs/metabuilder-port-spec.md). The
Claude Code CLI does not currently expose flags for those two values,
so they are documented here as the target and will be wired through
when tier-based LLM routing lands (upgrade #14 in the port spec).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


# The 8 adversarial lenses, in canonical metabuilder order. Kept as a
# module-level constant so tests can assert on it without importing the
# packet builder's internal string.
LENSES: tuple[tuple[str, str], ...] = (
    (
        "infrastructure-assumed-but-not-mentioned",
        "Infrastructure (queues, feature flags, auth middleware, storage) "
        "the plan implicitly relies on but never names.",
    ),
    (
        "silent-failure",
        "Code paths where, on wrong input, errors get swallowed and "
        "success-looking output is returned.",
    ),
    (
        "cross-cutting-concerns",
        "Logging, metrics, tracing, auth, retries, timeouts — anything "
        "that should be uniform but is usually invented per-node.",
    ),
    (
        "next-stage-prerequisites",
        "Data or state a later stage will need that no earlier stage "
        "produces.",
    ),
    (
        "YAGNI-cut",
        "Scope present in intake or research that is NOT required to "
        "satisfy the stated acceptance criteria. (Always advisory, never "
        "blocking.)",
    ),
    (
        "fake-completion",
        "Paths where code can pass tests / look done without satisfying "
        "the user-visible goal (TODO stubs, mocks of the system under test).",
    ),
    (
        "architecture-smell",
        "Layering inversions, wrong abstraction, deterministic logic "
        "where an LLM call is warranted (or vice versa), or violations "
        "of the project's stated architectural rules.",
    ),
    (
        "developer-contract-completeness",
        "What a developer reading the final contract still would not "
        "know: file conventions, error style, test location, run command, "
        "exit criteria.",
    ),
)


def _prompt_path() -> Path:
    """Locate the system_gap_analyst role prompt. Lives at
    `<repo_root>/prompts/metabuilder/35_system_gap_analyst.md`."""
    # nodes/system_gap_analyst.py is 3 levels below the repo root:
    #   <root>/src/claude_pipeline/nodes/system_gap_analyst.py
    here = Path(__file__).resolve()
    return here.parent.parent.parent.parent / "prompts" / "metabuilder" / "35_system_gap_analyst.md"


def _load_role_prompt() -> str:
    """Read the verbatim role prompt from disk."""
    path = _prompt_path()
    return path.read_text(encoding="utf-8")


def _format_codebase_anchor(research_brief: str) -> str:
    """Extract `sources_consulted` + `implementation_details` from the
    research output and format them as a codebaseAnchor block.

    The research node currently returns a free-form markdown brief (not
    JSON). When research is upgraded to return the metabuilder schema,
    this function will see a JSON object and pull the named keys. Until
    then, we use the markdown brief as the anchor body verbatim and tag
    it so the model knows what it is.
    """
    sources: list[str] = []
    details: list[str] = []

    stripped = (research_brief or "").strip()
    if stripped:
        # Try JSON shape first (forward-compatible with upgrade #3).
        try:
            obj = extract_json(stripped)
        except (ValueError, json.JSONDecodeError):
            obj = None
        if isinstance(obj, dict):
            raw_sources = obj.get("sources_consulted") or []
            raw_details = obj.get("implementation_details") or []
            if isinstance(raw_sources, list):
                sources = [str(s) for s in raw_sources]
            if isinstance(raw_details, list):
                details = [str(d) for d in raw_details]

    lines: list[str] = ["## codebaseAnchor"]
    lines.append(
        "Ground truth from the research pass. Every file or symbol you "
        "cite in your output must appear below."
    )
    lines.append("")
    if sources:
        lines.append("### sources_consulted")
        for s in sources:
            lines.append(f"- {s}")
        lines.append("")
    if details:
        lines.append("### implementation_details")
        for d in details:
            lines.append(f"- {d}")
        lines.append("")
    if not sources and not details:
        lines.append("### research brief (raw)")
        lines.append("")
        lines.append(stripped or "(no research brief produced)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_lenses_block() -> str:
    """Spell out the 8 lenses by name in the user packet so the model
    cannot skip one."""
    lines = ["## The 8 lenses (apply each one explicitly)"]
    for i, (name, desc) in enumerate(LENSES, start=1):
        lines.append(f"{i}. **{name}** — {desc}")
    return "\n".join(lines)


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user message for the system_gap_analyst LLM call.

    Includes: intake decisions + research brief + codebaseAnchor + the 8
    named lenses. Returns a single string — the role prompt is supplied
    separately via --append-system-prompt.
    """
    intake = state.get("intake", {})
    research_brief = state.get("research_brief", "")
    issue_title = state.get("issue_title", "")
    issue_number = state.get("issue_number", "?")

    acceptance = intake.get("acceptance_criteria", []) or []
    acceptance_bullets = (
        "\n".join(f"  - {c}" for c in acceptance) if acceptance else "  (none provided)"
    )
    risk_flags = intake.get("risk_flags", []) or []
    risk_str = ", ".join(risk_flags) if risk_flags else "(none)"

    parts = [
        f"# Gap analysis request — issue #{issue_number}: {issue_title}",
        "",
        "You are acting as system_gap_analyst in the metabuilder planning "
        "lane. Apply each of the 8 lenses spelled out below to the intake "
        "decisions and research brief. Return JSON only — schema is in the "
        "system prompt.",
        "",
        "## intake decisions",
        "```json",
        json.dumps(intake, indent=2, ensure_ascii=False),
        "```",
        "",
        f"- **task_type:** {intake.get('task_type', '?')}",
        f"- **complexity_tier:** {intake.get('complexity_tier', '?')}",
        f"- **scope_plan:** {intake.get('scope_plan', '?')}",
        f"- **risk_flags:** {risk_str}",
        f"- **right_thing_answer:** {intake.get('right_thing_answer', '?')}",
        "- **acceptance_criteria:**",
        acceptance_bullets,
        f"- **wiring_plan:** {intake.get('wiring_plan', '?')}",
        "",
        "## research brief",
        research_brief.strip() or "(no research brief produced)",
        "",
        _format_codebase_anchor(research_brief),
        _format_lenses_block(),
        "",
        "## reminder",
        "Return JSON matching the schema in the system prompt. Empty "
        "`blocking_gaps` is acceptable. Be sharp; do not pad.",
        "",
    ]
    return "\n".join(parts)


def _coerce_gap_list(value: object) -> list[dict]:
    """Coerce a raw JSON value into a list of {lens, gap, recommendation}
    dicts. Drops entries missing any field. Stringifies values so the
    downstream contract injector can format without re-validation."""
    out: list[dict] = []
    if not isinstance(value, list):
        return out
    for entry in value:
        if not isinstance(entry, dict):
            continue
        lens = entry.get("lens")
        gap = entry.get("gap")
        rec = entry.get("recommendation")
        if not lens or not gap or not rec:
            continue
        out.append(
            {
                "lens": str(lens),
                "gap": str(gap),
                "recommendation": str(rec),
            }
        )
    return out


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial gap-analysis pass.

    Returns a state slice with `gap_analysis` populated. On parse
    failure, returns an empty gap_analysis (so downstream consumers can
    proceed) plus an error marker for visibility.
    """
    role_prompt = _load_role_prompt()
    packet = build_gap_analysis_packet(state)

    log.info(
        "system_gap_analyst: invoking claude (Tier 3 / Opus; T=0.2 + "
        "max_tokens=8192 are spec targets — CLI does not expose them yet)"
    )
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        model="claude-opus-4-7",
        extra_args=[
            "--append-system-prompt",
            role_prompt,
        ],
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.exception("system_gap_analyst: result.text was unparseable")
        return {
            "gap_analysis": {
                "blocking_gaps": [],
                "advisory_gaps": [],
                "summary": "(gap analysis parse failed — proceeding without it)",
            },
            "error": f"system_gap_analyst parse failed: {e}; text head: {result.text[:300]}",
        }

    if not isinstance(raw, dict):
        return {
            "gap_analysis": {
                "blocking_gaps": [],
                "advisory_gaps": [],
                "summary": "(gap analysis returned non-object; proceeding without it)",
            },
            "error": f"system_gap_analyst: expected JSON object, got {type(raw).__name__}",
        }

    gap_analysis = {
        "blocking_gaps": _coerce_gap_list(raw.get("blocking_gaps")),
        "advisory_gaps": _coerce_gap_list(raw.get("advisory_gaps")),
        "summary": str(raw.get("summary") or "").strip(),
    }
    log.info(
        "system_gap_analyst done: blocking=%d advisory=%d",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
