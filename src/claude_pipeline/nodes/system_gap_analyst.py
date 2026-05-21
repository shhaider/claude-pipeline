"""system_gap_analyst node: adversarial pre-lane between research and plan.

Applies 8 named lenses to the intake + research output and emits
blocking + advisory gaps. Blocking gaps become MANDATORY ADDITIONAL
DELIVERABLES that the planner must cover; advisory gaps are
suggestions.

The system prompt lives in `prompts/metabuilder/35_system_gap_analyst.md`
and is loaded via `--append-system-prompt`. The user packet is built by
`_build_gap_analysis_packet` (port of metabuilder's
`buildGapAnalysisPacket`).

When the contract/planner split lands (roadmap item 4 in
`docs/metabuilder-port-spec.md`) the injection target moves from
plan_node to the contract node — for now it targets plan_node.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import GapAnalysis, GapAnalysisItem, PipelineState

log = logging.getLogger(__name__)


# Canonical lens slugs — downstream parsing depends on these exact names.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "Dependencies, services, env vars, migrations, or feature flags the framing assumes exist but never names.",
    ),
    (
        "silent-failure",
        "Paths where code reports success while doing nothing useful (swallowed exceptions, empty loops, no-op branches, unverified status writes).",
    ),
    (
        "cross-cutting-concerns",
        "Logging, auth, telemetry, error envelopes, rate limits, retries, idempotency, observability that the framing skipped.",
    ),
    (
        "next-stage-prerequisites",
        "Hooks or seams the next piece of work will require that this work must set up to avoid a rewrite later.",
    ),
    (
        "YAGNI-cut",
        "Speculative scope not required by the issue; flag for removal.",
    ),
    (
        "fake-completion",
        "Checks, statuses, or 'done' signals that could pass without actually doing the work.",
    ),
    (
        "architecture-smell",
        "Coupling, layering violations, hidden state, god-objects, or circular dependencies the proposed framing would introduce.",
    ),
    (
        "developer-contract-completeness",
        "Ambiguities a downstream implementer would still need to ask about (undefined types, unclear ownership, missing acceptance criteria).",
    ),
]

CANONICAL_LENS_SLUGS: frozenset[str] = frozenset(slug for slug, _ in LENSES)

# Repo root is repo/src/claude_pipeline/nodes/system_gap_analyst.py
# → parents[3] = repo/
SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "prompts"
    / "metabuilder"
    / "35_system_gap_analyst.md"
)

OUTPUT_SHAPE_REMINDER = """{
  "blocking_gaps":  [{"lens": "<one-of-the-8-slugs>", "gap": "<one sentence>", "recommendation": "<one sentence>"}],
  "advisory_gaps":  [{"lens": "<slug>", "gap": "...", "recommendation": "..."}],
  "summary": "<2-3 sentence overall framing assessment>"
}"""


def _format_codebase_anchor(state: PipelineState) -> str:
    """Best-effort codebase anchor block.

    Current research_node emits free-form markdown, not the structured
    JSON the metabuilder spec assumes. So: if state["research_anchor"]
    is a dict (forward-compat with later roadmap items), format its
    sources_consulted + implementation_details as bullet lists.
    Otherwise fall back to the research brief verbatim.
    """
    anchor = state.get("research_anchor")
    if isinstance(anchor, dict):
        lines: list[str] = []
        sources = anchor.get("sources_consulted")
        if isinstance(sources, list) and sources:
            lines.append("**Sources consulted:**")
            lines.extend(f"- {s}" for s in sources)
        details = anchor.get("implementation_details")
        if isinstance(details, list) and details:
            if lines:
                lines.append("")
            lines.append("**Implementation details:**")
            lines.extend(f"- {d}" for d in details)
        if lines:
            return "\n".join(lines)
    # Fallback: use the research brief as the anchor.
    return str(state.get("research_brief", "(no research brief)"))


def _build_gap_analysis_packet(state: PipelineState) -> str:
    """Port of metabuilder's buildGapAnalysisPacket.

    Assembles the user message for system_gap_analyst from intake,
    research brief, codebase anchor, issue text, and the 8-lens menu.
    """
    intake = state.get("intake", {})
    issue_number = state.get("issue_number", "?")
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "(no body)")

    lens_bullets = "\n".join(f"- `{slug}` — {desc}" for slug, desc in LENSES)

    sections = [
        "## Intake decisions",
        json.dumps(intake, indent=2),
        "",
        "## Research brief",
        str(state.get("research_brief", "(no research brief)")),
        "",
        "## Codebase anchor",
        _format_codebase_anchor(state),
        "",
        f"## Issue\n#{issue_number}: {issue_title}\n\n{issue_body}",
        "",
        "## Adversarial lenses",
        lens_bullets,
        "",
        "## Output",
        "Return a single JSON object matching the shape below — JSON only, no fences, no prose. Empty arrays are valid and expected when the framing is solid.",
        "",
        OUTPUT_SHAPE_REMINDER,
    ]
    return "\n".join(sections)


def _coerce_gap_items(raw: object, *, kind: str) -> list[GapAnalysisItem]:
    """Validate and coerce a raw list of gap dicts. Drops any item with
    an unknown lens slug (logs a warning) but does not error the node.
    Raises ValueError on shape failures the caller should treat as
    structural parse failures.
    """
    if not isinstance(raw, list):
        raise ValueError(f"{kind}: expected list, got {type(raw).__name__}")
    out: list[GapAnalysisItem] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"{kind}[{i}]: expected object, got {type(item).__name__}")
        required = {"lens", "gap", "recommendation"}
        missing = required - set(item.keys())
        if missing:
            raise ValueError(f"{kind}[{i}]: missing fields {sorted(missing)}")
        lens = str(item["lens"])
        if lens not in CANONICAL_LENS_SLUGS:
            log.warning(
                "system_gap_analyst: dropping %s[%d] with unknown lens %r",
                kind, i, lens,
            )
            continue
        out.append(
            {
                "lens": lens,
                "gap": str(item["gap"]),
                "recommendation": str(item["recommendation"]),
            }
        )
    return out


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run adversarial gap analysis on intake + research output."""
    if not SYSTEM_PROMPT_PATH.exists():
        return {
            "error": (
                f"system_gap_analyst: system prompt missing at {SYSTEM_PROMPT_PATH}"
            ),
        }

    packet = _build_gap_analysis_packet(state)
    log.info("system_gap_analyst: invoking claude (packet len=%d)", len(packet))

    # Tier 3 / temp 0.2 / max_tokens 8192 per metabuilder spec; the
    # `claude --print` CLI doesn't expose temp/max_tokens, so only model
    # is set here. Tracked for a future transport upgrade.
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        model="claude-opus-4-7",
        extra_args=["--append-system-prompt", str(SYSTEM_PROMPT_PATH)],
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "error": (
                f"system_gap_analyst: parse failed: {e}; text head: {result.text[:300]}"
            ),
        }
    if not isinstance(raw, dict):
        return {
            "error": f"system_gap_analyst: expected JSON object, got {type(raw).__name__}",
        }

    summary = raw.get("summary", "")
    if not isinstance(summary, str):
        return {"error": f"system_gap_analyst: summary not a string ({type(summary).__name__})"}

    try:
        blocking = _coerce_gap_items(raw.get("blocking_gaps", []), kind="blocking_gaps")
        advisory = _coerce_gap_items(raw.get("advisory_gaps", []), kind="advisory_gaps")
    except ValueError as e:
        return {"error": f"system_gap_analyst: {e}"}

    gap_analysis: GapAnalysis = {
        "blocking_gaps": blocking,
        "advisory_gaps": advisory,
        "summary": summary,
    }
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(blocking),
        len(advisory),
    )
    return {"gap_analysis": gap_analysis, "error": None}
