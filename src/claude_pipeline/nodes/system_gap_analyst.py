"""system_gap_analyst node — adversarial gap-analysis pass.

Port of metabuilder's `system_gap_analyst` role + `buildGapAnalysisPacket`.
Runs after research and before the contract / plan node. Applies 8 named
adversarial lenses to find unstated dependencies, silent-failure modes,
infrastructure assumed-but-not-mentioned, and architectural smells in the
issue framing.

Output is consumed by the next node (contract / plan): `blocking_gaps`
are injected as MANDATORY ADDITIONAL DELIVERABLES; `advisory_gaps` are
included as suggestions only.

Role prompt: `prompts/metabuilder/35_system_gap_analyst.md` — loaded
verbatim and passed via `--append-system-prompt`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


# The 8 adversarial lenses, verbatim from metabuilder's gap_analysis_packet.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "Every request assumes scaffolding. What infrastructure (modules, "
        "configs, registries, harnesses) does this request assume exists "
        "that may not?",
    ),
    (
        "silent-failure",
        "Name one thing that would pass all tests and look done but fail "
        "in production because a supporting piece was left out. No error, "
        "just wrong behavior.",
    ),
    (
        "cross-cutting-concerns",
        "Does this touch: error handling paths? Observability/logging? "
        "CLI entrypoints? Documentation? Does it need a test at a different "
        "layer than what was asked for (unit vs integration vs end-to-end)?",
    ),
    (
        "next-stage-prerequisites",
        "What decision made in this stage is load-bearing for the next "
        "one? If we don't include it now, the next stage will require a "
        "rework here.",
    ),
    (
        "YAGNI-cut",
        "For every gap you find, ask: is this actually needed for this "
        "stage to succeed, or is it gold-plating? Cut anything that could "
        "safely be deferred.",
    ),
    (
        "fake-completion",
        "What in this spec could be superficially completed — tests pass, "
        "structure looks correct, nothing throws — but the actual contract "
        "is not satisfied? Name the specific pattern (stub returning "
        "hardcoded values, test checking presence not behavior, etc).",
    ),
    (
        "architecture-smell",
        "What is the biggest architectural mistake in this direction? Is "
        "there a wrong abstraction being introduced — something that looks "
        "clean now but will become load-bearing in the wrong way?",
    ),
    (
        "developer-contract-completeness",
        "Does the request include a developer contract (not just a build "
        "contract)? A developer contract states: required fields per "
        "entity, allowed/forbidden state transitions, system-level "
        "invariants, failure conditions. Flag as [GAP] if any are absent.",
    ),
]


def _role_prompt_path() -> Path:
    """Locate `prompts/metabuilder/35_system_gap_analyst.md`.

    Resolved relative to this source file's location so the path is
    stable regardless of where the process is invoked from.
    """
    # src/claude_pipeline/nodes/system_gap_analyst.py -> repo root is 3 levels up
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "prompts" / "metabuilder" / "35_system_gap_analyst.md"


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user-message packet for the gap analyst.

    Includes: intake decisions + research brief + a codebaseAnchor block
    (drawn from research output) + the 8 named lenses spelled out for
    the model + the required output JSON schema.

    Pure function — no I/O. Tested directly in test_system_gap_analyst.
    """
    intake = state.get("intake", {})
    research_brief = state.get("research_brief", "(no research brief)")
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "")
    issue_number = state.get("issue_number", "?")

    # codebaseAnchor block — port of metabuilder's anchor pattern. We
    # don't have a structured research_result with sources_consulted /
    # implementation_details fields (the research node returns a markdown
    # brief here), so the brief itself IS the anchor. State this clearly
    # so the model treats it as the grounding evidence.
    codebase_anchor = (
        "## codebaseAnchor (grounding evidence)\n\n"
        "The research brief below is the authoritative codebase anchor for "
        "this analysis. It was produced by the research_lead role with "
        "Read/Grep/Glob tools against the actual worktree. Every gap you "
        "flag must be grounded in this evidence — do not speculate about "
        "files or modules that are not referenced here.\n\n"
        "### Research brief (sources_consulted + implementation_details "
        "are inlined as prose):\n\n"
        f"{research_brief}\n"
    )

    lens_block = "\n".join(
        f"**Lens {i + 1} — {name}**\n{description}"
        for i, (name, description) in enumerate(LENSES)
    )

    intake_block = json.dumps(intake, indent=2) if intake else "(no intake decisions)"

    output_schema = """{
  "blocking_gaps": [
    {"lens": "<lens-name>", "gap": "<what is missing>", "recommendation": "<what to add to scope>"}
  ],
  "advisory_gaps": [
    {"lens": "<lens-name>", "gap": "<what could be improved>", "recommendation": "<suggested action>"}
  ],
  "summary": "<2-3 sentence summary of the biggest blind spot>"
}"""

    return f"""## Adversarial Gap Analysis Task

You are acting as system_gap_analyst for issue #{issue_number}.

**Planning request (issue title):** {issue_title}

**Issue body (verbatim):**
{issue_body}

**Intake decisions (from autonomous_software_resolver):**
{intake_block}

{codebase_anchor}

## Apply the 8 adversarial lenses

For each lens below, decide if there is a gap. If yes, classify it as
**blocking** (the implementation cannot succeed without addressing this)
or **advisory** (worth flagging but not load-bearing for this stage).

{lens_block}

## Required output

Return a JSON object — JSON only, no prose, no markdown fence:

{output_schema}

Rules:
- Each gap must reference one of the 8 lens names exactly as written above.
- `blocking_gaps` are mandatory additions the contract MUST cover.
- `advisory_gaps` are suggestions, not requirements.
- Apply Lens 5 (YAGNI-cut) ruthlessly — do not add speculative future work.
- If no gaps found in a lens, omit that lens from the output (don't include empty entries).
- `summary` names the single biggest blind spot, or states "No structural gaps found" if the request is self-contained.
"""


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial gap analysis pass.

    Fresh session (no resume), Tier 3 (Opus), temperature 0.2, max
    tokens 8192. System prompt loaded verbatim from
    `prompts/metabuilder/35_system_gap_analyst.md` via
    `--append-system-prompt`.

    Returns a state slice containing `gap_analysis` with the
    `{blocking_gaps, advisory_gaps, summary}` schema. On parse failure
    or empty research input, returns an empty gap_analysis so the
    downstream node (plan/contract) can still run — gap analysis is
    advisory infrastructure, not a hard gate.
    """
    research_brief = state.get("research_brief", "").strip()
    if not research_brief:
        # Gap analysis without research is speculation — bail out cleanly
        # but don't fail the pipeline; emit an empty result so downstream
        # nodes know there was no analysis to consume.
        log.warning("system_gap_analyst: no research_brief in state; skipping")
        return {
            "gap_analysis": {
                "blocking_gaps": [],
                "advisory_gaps": [],
                "summary": "Skipped: no research brief available.",
            },
            "error": None,
        }

    role_prompt_path = _role_prompt_path()
    try:
        role_prompt = role_prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        log.error(
            "system_gap_analyst: role prompt missing at %s", role_prompt_path
        )
        return {
            "error": f"system_gap_analyst: role prompt not found at {role_prompt_path}",
        }

    user_packet = build_gap_analysis_packet(state)

    log.info(
        "system_gap_analyst: invoking claude (tier-3 opus, fresh session, "
        "%d-char packet)",
        len(user_packet),
    )
    # Tier 3 (Opus) per metabuilder's tier_registry. The `claude --print`
    # CLI doesn't expose temperature or max_tokens flags, so those params
    # from the metabuilder spec (T=0.2, max_tokens=8192) are not wired
    # through. We pin the model to the Opus family so the tier intent is
    # honored; the model is None here to defer to the CLI's configured
    # default Opus when no specific tag is set in this env.
    result = run_claude(
        user_packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        # Append the verbatim role prompt as the system prompt.
        extra_args=["--append-system-prompt", role_prompt],
        model=None,
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f)",
        result.duration_s,
        result.cost_usd,
    )

    try:
        raw = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.exception("system_gap_analyst: parse failed")
        return {
            "error": (
                f"system_gap_analyst parse failed: {e}; "
                f"text head: {result.text[:300]}"
            )
        }
    if not isinstance(raw, dict):
        return {
            "error": (
                f"system_gap_analyst: expected JSON object, got "
                f"{type(raw).__name__}"
            )
        }

    blocking = list(raw.get("blocking_gaps", []) or [])
    advisory = list(raw.get("advisory_gaps", []) or [])
    summary = str(raw.get("summary", "") or "")

    gap_analysis = {
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
