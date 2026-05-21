"""system_gap_analyst node — adversarial pre-lane that runs BEFORE the
contract_writer.

Applies 8 named lenses to surface what is missing from the intake +
research framing: unstated infrastructure, silent-failure modes,
cross-cutting concerns, architecture smells, etc. Output is consumed by
the contract_writer node, which folds blocking gaps into the contract as
MANDATORY deliverables and advisory gaps as suggestions.

Port of metabuilder's `system_gap_analyst` role:
  - system prompt: prompts/metabuilder/35_system_gap_analyst.md (verbatim)
  - user packet:   build_gap_analysis_packet (Python port of
                   `buildGapAnalysisPacket`)

Tier 3 (Opus). Temperature 0.2. Max tokens 8192. Fresh session (no resume).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import GapAnalysis, GapFinding, PipelineState

log = logging.getLogger(__name__)


SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "prompts"
    / "metabuilder"
    / "35_system_gap_analyst.md"
)


LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "queues, tables, env vars, secrets, IAM, feature flags, schedules that "
        "the framing presupposes but no one has agreed to provision.",
    ),
    (
        "silent-failure",
        "places where the code will appear to succeed (200, exit 0, log 'done') "
        "while dropping work, swallowing errors, or producing data downstream "
        "code will mis-trust.",
    ),
    (
        "cross-cutting-concerns",
        "logging, metrics, tracing, auth, rate-limiting, idempotency, retry "
        "semantics, request IDs, audit trails — things every component should "
        "do but planners forget.",
    ),
    (
        "next-stage-prerequisites",
        "work this stage MUST do because a named downstream consumer depends "
        "on it (a column needed by next-sprint reporting, a flag needed by ops).",
    ),
    (
        "YAGNI-cut",
        "scope that is in the framing but obviously not needed for the stated "
        "acceptance criteria. Surface so the contract can explicitly drop it.",
    ),
    (
        "fake-completion",
        "patterns that look done but aren't: stub functions returning the right "
        "shape, trivial-truth tests, migrations without indexes, flags toggled "
        "with no code path.",
    ),
    (
        "architecture-smell",
        "tight coupling across module boundaries, business logic in a controller, "
        "shared mutable state, leaked implementation details, new globals, "
        "hot-path work inside a lock.",
    ),
    (
        "developer-contract-completeness",
        "what the implementer needs to know that the packet does not yet say: "
        "missing acceptance criteria, missing failure-mode commitments, missing "
        "rollback story, missing observability story.",
    ),
]


def _format_lenses() -> str:
    lines = []
    for i, (name, desc) in enumerate(LENSES, start=1):
        lines.append(f"  {i}. **{name}** — {desc}")
    return "\n".join(lines)


def _build_codebase_anchor(research_brief: str) -> str:
    """Port of metabuilder's codebaseAnchor block — pulls
    ``sources_consulted`` and ``implementation_details`` out of the
    research brief (which may be markdown or a JSON-shaped object).

    The research node returns markdown today, so we degrade gracefully:
    if we can find a JSON object inside the brief, we use its fields;
    otherwise we embed the whole brief as the anchor body so the model
    still has the codebase grounding.
    """
    sources: list[str] = []
    impl_details: list[str] = []
    try:
        parsed = extract_json(research_brief)
        if isinstance(parsed, dict):
            sources = [str(s) for s in parsed.get("sources_consulted", []) or []]
            impl_details = [
                str(d) for d in parsed.get("implementation_details", []) or []
            ]
    except (ValueError, json.JSONDecodeError):
        pass

    parts = ["## Codebase anchor"]
    if sources:
        parts.append("**Sources consulted:**")
        parts.extend(f"- {s}" for s in sources)
    if impl_details:
        parts.append("\n**Implementation details:**")
        parts.extend(f"- {d}" for d in impl_details)
    if not sources and not impl_details:
        parts.append(
            "_No structured codebase anchor available — research brief embedded "
            "as plain context below._"
        )
    return "\n".join(parts)


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user message for the system_gap_analyst LLM call.

    Mirrors metabuilder's ``buildGapAnalysisPacket``. Must include:
    intake decisions + research brief + codebaseAnchor block + the 8
    named lenses spelled out for the model.
    """
    intake = state.get("intake", {}) or {}
    research_brief = state.get("research_brief", "") or ""
    codebase_anchor = _build_codebase_anchor(research_brief)

    return (
        f"## Adversarial gap-analysis task\n\n"
        f"You are acting as **system_gap_analyst** before the contract_writer "
        f"runs. Apply each of the 8 named lenses to the framing below and "
        f"surface anything missing.\n\n"
        f"**Issue #{state.get('issue_number', '?')}: "
        f"{state.get('issue_title', '(no title)')}**\n\n"
        f"## Intake decisions\n"
        f"```json\n{json.dumps(intake, indent=2)}\n```\n\n"
        f"## Research brief\n"
        f"{research_brief or '(no research brief)'}\n\n"
        f"{codebase_anchor}\n\n"
        f"## The eight lenses (apply each one explicitly)\n"
        f"{_format_lenses()}\n\n"
        f"## Output\n"
        f"Return VALID JSON ONLY — no preamble, no fence:\n\n"
        f"```\n"
        f"{{\n"
        f"  \"blocking_gaps\": [{{\"lens\": \"...\", \"gap\": \"...\", \"recommendation\": \"...\"}}],\n"
        f"  \"advisory_gaps\":  [{{\"lens\": \"...\", \"gap\": \"...\", \"recommendation\": \"...\"}}],\n"
        f"  \"summary\": \"one sentence — the most important thing you found, "
        f"or 'no significant gaps'\"\n"
        f"}}\n"
        f"```\n"
        f"`lens` MUST be one of the eight names spelled exactly. Empty arrays are "
        f"fine if the framing is genuinely clean.\n"
    )


def _load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _coerce_finding(raw: object) -> GapFinding | None:
    if not isinstance(raw, dict):
        return None
    return {
        "lens": str(raw.get("lens", "")),
        "gap": str(raw.get("gap", "")),
        "recommendation": str(raw.get("recommendation", "")),
    }


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial gap analyst. Fresh session, Tier 3 (Opus),
    temperature 0.2, max_tokens 8192."""
    packet = build_gap_analysis_packet(state)
    system_prompt = _load_system_prompt()

    log.info("system_gap_analyst: invoking claude (Opus, T=0.2, 8192 tok)")
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=900,
        model="claude-opus-4-7",
        extra_args=[
            "--append-system-prompt",
            system_prompt,
            "--max-tokens",
            "8192",
            "--temperature",
            "0.2",
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
        return {
            "error": (
                f"system_gap_analyst parse failed: {e}; "
                f"text head: {result.text[:300]}"
            )
        }
    if not isinstance(raw, dict):
        return {
            "error": (
                f"system_gap_analyst: expected JSON object, "
                f"got {type(raw).__name__}"
            )
        }

    blocking = [
        f
        for f in (_coerce_finding(x) for x in raw.get("blocking_gaps", []) or [])
        if f is not None
    ]
    advisory = [
        f
        for f in (_coerce_finding(x) for x in raw.get("advisory_gaps", []) or [])
        if f is not None
    ]
    analysis: GapAnalysis = {
        "blocking_gaps": blocking,
        "advisory_gaps": advisory,
        "summary": str(raw.get("summary", "")),
    }
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory — %s",
        len(blocking),
        len(advisory),
        analysis["summary"][:80],
    )
    return {"gap_analysis": analysis, "error": None}
