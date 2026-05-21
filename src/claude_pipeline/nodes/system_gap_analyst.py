"""system_gap_analyst node: adversarial 8-lens pre-pass before the
contract is written.

Ported from metabuilder's `system_gap_analyst` lane (see
`docs/metabuilder-port-spec.md` and `prompts/metabuilder/35_system_gap_analyst.md`).
Runs between `research` and `contract`. Its output is a `GapAnalysis`
dict that the contract node consumes — blocking gaps become MANDATORY
additional deliverables; advisory gaps become suggestions.

The node is a fresh Claude session (no --resume), Tier 3 (Opus),
temperature 0.2, max_tokens 8192. The role prompt is loaded verbatim
from `prompts/metabuilder/35_system_gap_analyst.md` and injected via
`--append-system-prompt`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import GapAnalysis, PipelineState

log = logging.getLogger(__name__)

# Repo-root anchor for locating the verbatim role prompt. The package
# lives at src/claude_pipeline/nodes/system_gap_analyst.py — the prompt
# lives at <repo>/prompts/metabuilder/35_system_gap_analyst.md.
_REPO_ROOT = Path(__file__).resolve().parents[3]
SYSTEM_PROMPT_PATH = _REPO_ROOT / "prompts" / "metabuilder" / "35_system_gap_analyst.md"

# The eight named adversarial lenses. Order and spelling match the
# metabuilder port spec (docs/metabuilder-port-spec.md) and the
# verbatim role prompt at prompts/metabuilder/35_system_gap_analyst.md.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "Does the framing assume infra (tables, queues, env vars, secrets, feature flags, file layout) the issue never named?",
    ),
    (
        "silent-failure",
        "Where could this code fail without raising — swallowed exceptions, ignored return codes, retries that mask root cause, logs without alerts?",
    ),
    (
        "cross-cutting-concerns",
        "What spans the change without belonging to one file — logging, metrics, tracing, auth, idempotency, schema versioning, migration ordering, backwards compat?",
    ),
    (
        "next-stage-prerequisites",
        "What must this stage produce so downstream work (next nodes, next issues) is unblocked — interfaces, fixtures, names, schemas?",
    ),
    (
        "YAGNI-cut",
        "What is in the framing but should be removed as premature — speculative abstractions, single-consumer knobs, 'we'll need this later' hooks?",
    ),
    (
        "fake-completion",
        "How could this be marked done while broken — tests that don't exercise the new path, flag-gated code nobody flips, mocked deps that don't match reality, happy-path-only coverage?",
    ),
    (
        "architecture-smell",
        "Layering inversions, circular deps, god-objects, leaky abstractions, premature optimization, duplicated state, hidden coupling.",
    ),
    (
        "developer-contract-completeness",
        "Would the implementer have to guess WHAT to build (not how)? Exact signatures, paths, return shapes, error types, test commands, acceptance criteria — anything missing forces a judgment call.",
    ),
]


def build_codebase_anchor(research_brief: str, research_output: dict | None = None) -> str:
    """Produce a `codebaseAnchor` block from research output.

    Mirrors metabuilder's anchor block: a concise, evidence-bearing
    snippet that grounds the gap-analyst in actual code (file paths,
    signatures, defaults). Drawn from research output's
    `sources_consulted` and `implementation_details` when available;
    falls back to the markdown research brief otherwise.
    """
    parts: list[str] = ["## codebaseAnchor"]
    if research_output and isinstance(research_output, dict):
        sources = research_output.get("sources_consulted") or []
        details = research_output.get("implementation_details") or []
        if sources:
            parts.append("**Sources consulted:**")
            parts.extend(f"- {s}" for s in sources)
        if details:
            parts.append("\n**Implementation details:**")
            parts.extend(f"- {d}" for d in details)
        if not sources and not details:
            parts.append("(research output supplied no anchor sources)")
    else:
        # Fallback: inline the research brief as anchor. Not as
        # structured as the metabuilder version, but it grounds the
        # model in the same source-of-truth the contract will use.
        parts.append("**Research brief (used as anchor — no structured sources available):**")
        parts.append(research_brief.strip() if research_brief else "(no research brief)")
    return "\n".join(parts)


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Port of metabuilder's `buildGapAnalysisPacket`.

    Assembles the user message for the system_gap_analyst LLM call.
    Includes: intake decisions, research brief, codebaseAnchor block,
    and the eight named lenses spelled out verbatim for the model.
    """
    intake = state.get("intake", {})
    research_brief = state.get("research_brief", "(no research brief)")
    research_output = state.get("research_output") if isinstance(state, dict) else None
    anchor = build_codebase_anchor(research_brief, research_output)

    lens_block = "\n".join(
        f"{i + 1}. **{name}** — {hint}" for i, (name, hint) in enumerate(LENSES)
    )

    parts = [
        "## Adversarial Gap Analysis Task",
        "",
        "You are acting as `system_gap_analyst` BEFORE a contract is written.",
        "Find what is MISSING from the framing below. Do not design the solution.",
        "",
        f"**Issue #{state.get('issue_number', '?')}: {state.get('issue_title', '')}**",
        "",
        "### Intake decisions",
        "```json",
        json.dumps(intake, indent=2, sort_keys=True),
        "```",
        "",
        "### Research brief",
        research_brief.strip() if research_brief else "(no research brief)",
        "",
        anchor,
        "",
        "### The eight lenses to apply",
        lens_block,
        "",
        "For each lens, find at most a few specific gaps. Skip lenses with nothing to flag.",
        "Mark BLOCKING only if shipping without it produces wrong, unsafe, or measurably incomplete work.",
        "",
        "### Output",
        "Return VALID JSON ONLY — no prose, no markdown fence:",
        "",
        '{"blocking_gaps": [{"lens": "...", "gap": "...", "recommendation": "..."}],',
        ' "advisory_gaps":  [{"lens": "...", "gap": "...", "recommendation": "..."}],',
        ' "summary": "2-3 sentences on the framing\'s completeness"}',
        "",
        "Begin:",
    ]
    return "\n".join(parts)


def _load_system_prompt() -> str:
    if not SYSTEM_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"system_gap_analyst role prompt missing at {SYSTEM_PROMPT_PATH}"
        )
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _coerce_gap_item(raw: object, fallback_lens: str = "") -> dict | None:
    if not isinstance(raw, dict):
        return None
    lens = str(raw.get("lens") or fallback_lens or "").strip()
    gap = str(raw.get("gap") or "").strip()
    recommendation = str(raw.get("recommendation") or "").strip()
    if not gap:
        return None
    return {"lens": lens, "gap": gap, "recommendation": recommendation}


def _normalize_gap_analysis(parsed: object) -> GapAnalysis:
    """Coerce model output into the documented GapAnalysis shape.

    Tolerates minor key drift (e.g. `blocking` vs `blocking_gaps`).
    Drops items missing the `gap` field. Always returns a dict with
    all three keys present.
    """
    if not isinstance(parsed, dict):
        return {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}

    raw_blocking = parsed.get("blocking_gaps") or parsed.get("blocking") or []
    raw_advisory = parsed.get("advisory_gaps") or parsed.get("advisory") or []
    summary = str(parsed.get("summary") or "").strip()

    blocking: list[dict] = []
    for item in raw_blocking if isinstance(raw_blocking, list) else []:
        coerced = _coerce_gap_item(item)
        if coerced is not None:
            blocking.append(coerced)

    advisory: list[dict] = []
    for item in raw_advisory if isinstance(raw_advisory, list) else []:
        coerced = _coerce_gap_item(item)
        if coerced is not None:
            advisory.append(coerced)

    return {
        "blocking_gaps": blocking,
        "advisory_gaps": advisory,
        "summary": summary,
    }


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial 8-lens gap pass.

    Returns a state slice containing `gap_analysis`. Errors are surfaced
    via the `error` key (consistent with other nodes); a parse failure
    yields an empty gap_analysis so the contract node can still run.
    """
    system_prompt = _load_system_prompt()
    packet = build_gap_analysis_packet(state)

    log.info("system_gap_analyst: invoking claude (fresh session, Tier 3)")
    result = run_claude(
        packet,
        cwd=state["worktree_path"],
        timeout_s=600,
        model="claude-opus-4-7",
        extra_args=[
            "--append-system-prompt",
            system_prompt,
        ],
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        parsed = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("system_gap_analyst: parse failed (%s); returning empty analysis", e)
        return {
            "gap_analysis": {"blocking_gaps": [], "advisory_gaps": [], "summary": ""},
            "error": f"system_gap_analyst parse failed: {e}; text head: {result.text[:300]}",
        }

    gap_analysis = _normalize_gap_analysis(parsed)
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(gap_analysis.get("blocking_gaps", [])),
        len(gap_analysis.get("advisory_gaps", [])),
    )
    return {"gap_analysis": gap_analysis, "error": None}
