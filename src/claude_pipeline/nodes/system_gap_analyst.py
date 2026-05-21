"""system_gap_analyst node: adversarial gap-finding pass that runs
BEFORE the contract_writer.

Ports metabuilder's `system_gap_analyst` role + `buildGapAnalysisPacket`
(from `scripts/metabuilder/plan_self_upgrade.js`). Applies 8 named
lenses to surface unstated dependencies, silent-failure modes,
cross-cutting concerns, and architectural smells while there is still
time to bake them into the contract.

LLM params (Tier 3 / Opus, per `docs/metabuilder-port-spec.md`):
- model:        claude-opus-4-7
- temperature:  0.2
- max_tokens:   8192
- session:      fresh (no resume)

Output is a structured `gap_analysis` dict on PipelineState:

    {
      "blocking_gaps":  [{lens, gap, recommendation}, ...],
      "advisory_gaps":  [{lens, gap, recommendation}, ...],
      "summary":        "<2-3 sentence steer for contract_writer>"
    }

`blocking_gaps` are wired into `contract_writer`'s user packet as
MANDATORY ADDITIONAL DELIVERABLES. `advisory_gaps` ride along as
suggestions only.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


# Path resolution: prompts/ lives at the repo root, two parents above
# this file (src/claude_pipeline/nodes/system_gap_analyst.py).
_REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = _REPO_ROOT / "prompts" / "metabuilder" / "35_system_gap_analyst.md"


# The 8 adversarial lenses (verbatim names from metabuilder's
# buildGapAnalysisPacket). Order matches the role prompt above.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "Config, env vars, services, dependencies, file paths, or platforms "
        "the work needs but that nobody has called out in the intake or research.",
    ),
    (
        "silent-failure",
        "Places where a bug or missing dependency would not throw, would not page, "
        "and would not appear in tests, but would corrupt state or hide regressions.",
    ),
    (
        "cross-cutting-concerns",
        "Logging, metrics, tracing, retries, timeouts, idempotency, auth, audit trails "
        "— concerns that should land in every module but are easy to forget when "
        "scoping a single feature.",
    ),
    (
        "next-stage-prerequisites",
        "Work this contract assumes is done by some later stage, or work some later "
        "stage assumes is done here but isn't on the list.",
    ),
    (
        "YAGNI-cut",
        "Scope this contract is carrying that is not load-bearing for the stated goal. "
        "Cutting it makes the deliverable smaller and the contract sharper.",
    ),
    (
        "fake-completion",
        "Deliverables whose acceptance criteria can pass while the deliverable still "
        "does not do its job — tests asserting on the wrong thing, returns-200 checks "
        "when the meaningful failure is a wrong payload.",
    ),
    (
        "architecture-smell",
        "Coupling, layering inversions, hidden global state, leaked abstractions, or "
        "shapes that will be painful to live with even if they ship correctly.",
    ),
    (
        "developer-contract-completeness",
        "For each acceptance criterion: can a developer finish without asking a "
        "clarifying question? If not, what is missing from the contract?",
    ),
]


def _build_codebase_anchor(state: PipelineState) -> str:
    """Pull the `sources_consulted` + `implementation_details` slices out
    of research output to form a `codebaseAnchor` block.

    Research is currently stored as `research_brief` (markdown text). If
    a future research-node revision produces a structured dict with
    `sources_consulted` / `implementation_details` keys (the metabuilder
    shape), we surface those directly. Otherwise we fall back to the raw
    markdown brief and let the model extract anchors itself.
    """
    research = state.get("research")
    if isinstance(research, dict):
        sources = research.get("sources_consulted") or []
        impls = research.get("implementation_details") or []
        parts: list[str] = []
        if sources:
            parts.append("**Sources consulted (file:line — finding):**")
            parts.extend(f"- {s}" for s in sources)
        if impls:
            parts.append("")
            parts.append("**Implementation details (signatures, defaults, patterns):**")
            parts.extend(f"- {d}" for d in impls)
        if parts:
            return "\n".join(parts)

    brief = state.get("research_brief")
    if brief:
        return (
            "**Research brief (no structured anchor available — extract anchors yourself):**\n"
            + str(brief)
        )
    return "(no research output available — flag this as a blocking gap)"


def _format_lenses() -> str:
    """Render the 8 lenses as a numbered list for the user packet."""
    lines: list[str] = []
    for i, (name, description) in enumerate(LENSES, start=1):
        lines.append(f"({i}) **{name}** — {description}")
    return "\n".join(lines)


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user packet for the system_gap_analyst LLM call.

    Port of metabuilder's `buildGapAnalysisPacket`. Includes:
      - intake decisions (the 7-decision resolver output)
      - research brief / structured research output
      - codebaseAnchor block (sources_consulted + implementation_details)
      - the 8 named lenses spelled out for the model

    Pure-python; deterministic; safe to unit-test without an LLM.
    """
    intake = state.get("intake", {})
    issue_number = state.get("issue_number", "?")
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "")
    research_brief = state.get("research_brief", "(no research brief)")

    codebase_anchor = _build_codebase_anchor(state)
    lenses_block = _format_lenses()

    sections: list[str] = [
        "## Adversarial Gap Analysis Task",
        "",
        "You are acting as **system_gap_analyst** for a claude-pipeline planning request.",
        "Your output runs BEFORE the contract_writer. Your blocking gaps will be "
        "injected into the contract as MANDATORY ADDITIONAL DELIVERABLES.",
        "",
        f"**Issue #{issue_number}:** {issue_title}",
        "",
        "**Issue body:**",
        issue_body or "(no body)",
        "",
        "## Intake decisions",
        "",
        "```json",
        json.dumps(intake, indent=2, sort_keys=True),
        "```",
        "",
        "## Research brief",
        "",
        research_brief,
        "",
        "## codebaseAnchor",
        "",
        codebase_anchor,
        "",
        "## The 8 adversarial lenses",
        "",
        "Walk through each lens in order. For each, ask 'is there anything here?' "
        "and only emit a gap when you can name a concrete thing.",
        "",
        lenses_block,
        "",
        "## Output",
        "",
        "Return VALID JSON ONLY — no prose, no markdown fence, no preamble. Shape:",
        "",
        "{",
        '  "blocking_gaps": [{"lens": "<one of the 8 names>", "gap": "...", "recommendation": "..."}],',
        '  "advisory_gaps": [{"lens": "<one of the 8 names>", "gap": "...", "recommendation": "..."}],',
        '  "summary": "<2-3 sentences: the most important thing the contract_writer must not miss>"',
        "}",
        "",
        "Begin:",
    ]
    return "\n".join(sections)


def _normalize_gap_list(raw: object) -> list[dict]:
    """Coerce a gap-list field into a clean list of {lens, gap, recommendation} dicts.

    Drops malformed entries silently — better to lose a noisy item than
    to fail the whole gap-analysis output. Empty list is a legitimate result.
    """
    if not isinstance(raw, list):
        return []
    cleaned: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        lens = item.get("lens")
        gap = item.get("gap")
        rec = item.get("recommendation")
        if not (isinstance(lens, str) and isinstance(gap, str) and isinstance(rec, str)):
            continue
        cleaned.append({"lens": lens, "gap": gap, "recommendation": rec})
    return cleaned


def system_gap_analyst_node(state: PipelineState) -> dict:
    """LangGraph node entry point.

    Runs as a fresh session (no `--resume`) with Tier 3 / Opus params.
    Loads the role prompt as `--append-system-prompt`. Returns a state
    slice with `gap_analysis` populated.
    """
    if not PROMPT_PATH.exists():
        return {
            "error": (
                f"system_gap_analyst: role prompt not found at {PROMPT_PATH}. "
                "Expected `prompts/metabuilder/35_system_gap_analyst.md`."
            ),
        }

    packet = build_gap_analysis_packet(state)
    log.info("system_gap_analyst: invoking claude (fresh session, Tier 3)")
    result = run_claude(
        packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        model="claude-opus-4-7",
        extra_args=[
            "--append-system-prompt",
            PROMPT_PATH.read_text(),
            "--max-tokens",
            "8192",
            "--temperature",
            "0.2",
        ],
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
                f"system_gap_analyst parse failed: {e}; "
                f"text head: {result.text[:300]}"
            ),
        }
    if not isinstance(raw, dict):
        return {
            "error": (
                "system_gap_analyst: expected JSON object, "
                f"got {type(raw).__name__}"
            ),
        }

    gap_analysis = {
        "blocking_gaps": _normalize_gap_list(raw.get("blocking_gaps")),
        "advisory_gaps": _normalize_gap_list(raw.get("advisory_gaps")),
        "summary": str(raw.get("summary", "")),
    }
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
    )
    return {"gap_analysis": gap_analysis, "error": None}
