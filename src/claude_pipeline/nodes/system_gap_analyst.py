"""System gap analyst node: adversarial pre-lane between research and plan.

Ports metabuilder's `system_gap_analyst` role (prompt at
`prompts/metabuilder/35_system_gap_analyst.md`) and its
`buildGapAnalysisPacket` user-message builder.

Applies 8 named lenses to the intake + research brief to find unstated
dependencies, silent-failure modes, and architectural smells BEFORE the
plan node turns the request into deliverables. Blocking gaps are
injected into the plan node's prompt as mandatory additional
deliverables; advisory gaps are passed through as suggestions.

Tier 3 (Opus). Fresh session. T=0.2. max_tokens=8192.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

# Resolve the prompt path relative to the package root so it works
# regardless of cwd. `__file__` is .../src/claude_pipeline/nodes/system_gap_analyst.py
# the prompt lives at .../prompts/metabuilder/35_system_gap_analyst.md
_PROMPT_PATH = (
    Path(__file__).resolve().parents[3]
    / "prompts"
    / "metabuilder"
    / "35_system_gap_analyst.md"
)


# The 8 lenses, spelled out verbatim into the user packet (mirrors
# metabuilder's buildGapAnalysisPacket). Listed here as data so tests
# can assert all 8 are present in the rendered packet.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "Every request assumes scaffolding. What does this request assume "
        "exists that may not? Name the specific infrastructure (runner, "
        "registry, harness, report writer) that the request quietly relies "
        "on without naming.",
    ),
    (
        "silent-failure",
        "Name one thing that would pass all tests and look done but fail "
        "in production because a supporting piece was left out. No error, "
        "just wrong behavior.",
    ),
    (
        "cross-cutting-concerns",
        "Does this touch error-handling paths? Observability/logging? CLI "
        "entrypoints? ROADMAP_ADDITIONS? Does it need a test at a different "
        "layer (unit vs integration vs GUI) than what was asked for?",
    ),
    (
        "next-stage-prerequisites",
        "What decision made in this stage is load-bearing for the next one? "
        "If we don't include it now, the next stage will require a rework "
        "here.",
    ),
    (
        "YAGNI-cut",
        "For every gap considered, ask: is this actually needed for this "
        "stage to succeed, or is it gold-plating? Cut anything that could "
        "safely be deferred.",
    ),
    (
        "fake-completion",
        "What in this spec could be superficially completed — tests pass, "
        "structure looks correct, nothing throws — but the actual contract "
        "is not satisfied? Name the specific pattern: stub returning "
        "hardcoded values, test checking presence not behavior, acceptance "
        "criteria that miss a key edge case, prompt file that exists but "
        "is hollow.",
    ),
    (
        "architecture-smell",
        "What is the biggest architectural mistake in this direction? What "
        "would a senior engineer who has seen this pattern fail before say? "
        "Is there a wrong abstraction being introduced — something that "
        "looks clean now but will become load-bearing in the wrong way?",
    ),
    (
        "developer-contract-completeness",
        "Does the request include a developer contract (not just a build "
        "contract)? A developer contract must state: (1) required fields "
        "per entity, (2) allowed and forbidden state transitions, (3) "
        "system-level invariants that must hold simultaneously, (4) "
        "failure conditions — any of which means incomplete. Flag any "
        "of these that are absent.",
    ),
]


def _load_system_prompt() -> str:
    """Read 35_system_gap_analyst.md as the system prompt."""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"system_gap_analyst prompt not found at {_PROMPT_PATH}"
        )
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _format_codebase_anchor(research_brief: str) -> str:
    """Pull a `codebaseAnchor` block out of the research brief.

    Metabuilder's buildGapAnalysisPacket assembles the anchor from the
    research output's `sources_consulted` + `implementation_details`
    fields. Our research node emits a markdown brief instead of
    structured JSON, so we surface the whole brief verbatim under the
    `codebaseAnchor` heading and let the model extract anchors from it.
    """
    if not research_brief.strip():
        return "(no research brief — gap analysis must flag this as a blocker)"
    return research_brief.strip()


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Build the user message for the system_gap_analyst LLM call.

    Mirrors metabuilder's `buildGapAnalysisPacket` shape. Must include:
      - intake decisions
      - research brief
      - codebaseAnchor block (drawn from research)
      - 8 named lenses spelled out for the model
      - the JSON output schema

    Pure-python and side-effect-free so tests can exercise it without
    spawning Claude.
    """
    intake = state.get("intake", {}) or {}
    research_brief = state.get("research_brief", "") or ""
    issue_title = state.get("issue_title", "") or ""
    issue_body = state.get("issue_body", "") or ""

    lens_block = "\n\n".join(
        f"**Lens {i + 1} — {name}**\n{desc}"
        for i, (name, desc) in enumerate(LENSES)
    )

    intake_json = json.dumps(intake, indent=2)

    packet = f"""## Gap Analysis Request

You are acting as `system_gap_analyst` for the claude-pipeline. Run AFTER
research and BEFORE the contract / plan writer. Apply the 8 adversarial
lenses below to the intake decisions + research brief and produce a
structured gap list. Each gap will be considered for inclusion in the
plan as a mandatory deliverable (blocking) or a suggestion (advisory).

### Planning request

ISSUE: {issue_title}

{issue_body}

### Intake decisions

```json
{intake_json}
```

### Research brief

{research_brief or "(no research brief was produced)"}

### codebaseAnchor

The block below is the canonical "what the code looks like right now"
anchor. Every gap you assert about current state MUST be grounded here
or in the research brief — do NOT assert "file X is missing" without
evidence in this anchor or the brief.

```
{_format_codebase_anchor(research_brief)}
```

### The 8 lenses (apply EACH and report findings)

{lens_block}

### Output schema (return VALID JSON only, no prose, no markdown fence)

```json
{{
  "blocking_gaps": [
    {{"lens": "<one of the 8 lens names>", "gap": "what is missing", "recommendation": "what to add to the plan"}}
  ],
  "advisory_gaps": [
    {{"lens": "<one of the 8 lens names>", "gap": "what is missing", "recommendation": "suggestion for the planner"}}
  ],
  "summary": "2-3 sentence summary of the biggest blind spot in this framing"
}}
```

Rules:
- `blocking_gaps` are gaps the plan MUST cover — without them the work fails.
- `advisory_gaps` are gaps the planner SHOULD consider — they are not mandatory.
- 3-7 gaps total across both buckets. Cut anything that's gold-plating.
- If no structural gaps exist, return empty arrays and say so in `summary`.
- `lens` MUST be one of: {", ".join(name for name, _ in LENSES)}.

Begin.
"""
    return packet


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial gap-analysis pass.

    Loads `35_system_gap_analyst.md` as the system prompt (via
    `--append-system-prompt`), builds the user packet, and invokes
    Claude in a fresh session (no resume) at Tier 3 / Opus, T=0.2,
    max_tokens=8192. Parses the result into the gap_analysis dict.
    """
    try:
        system_prompt = _load_system_prompt()
    except FileNotFoundError as e:
        return {"error": f"system_gap_analyst: {e}"}

    user_packet = build_gap_analysis_packet(state)

    # Write the system prompt to a tempfile so claude --append-system-prompt
    # can read it. (Some claude CLI versions take the prompt inline, some
    # via file. Inline via the flag is simpler.)
    extra_args = [
        "--append-system-prompt",
        system_prompt,
    ]

    log.info("system_gap_analyst: invoking claude (fresh session, Tier 3)")
    result = run_claude(
        user_packet,
        cwd=state.get("worktree_path"),
        timeout_s=600,
        extra_args=extra_args,
        model="claude-opus-4-7",
    )
    log.info(
        "system_gap_analyst: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    try:
        parsed = extract_json(result.text)
    except (ValueError, json.JSONDecodeError) as e:
        return {
            "error": (
                f"system_gap_analyst parse failed: {e}; "
                f"text head: {result.text[:300]}"
            )
        }
    if not isinstance(parsed, dict):
        return {
            "error": (
                "system_gap_analyst: expected JSON object, "
                f"got {type(parsed).__name__}"
            )
        }

    blocking = parsed.get("blocking_gaps") or []
    advisory = parsed.get("advisory_gaps") or []
    summary = parsed.get("summary") or ""
    if not isinstance(blocking, list) or not isinstance(advisory, list):
        return {
            "error": (
                "system_gap_analyst: blocking_gaps/advisory_gaps must be arrays"
            )
        }

    gap_analysis = {
        "blocking_gaps": blocking,
        "advisory_gaps": advisory,
        "summary": str(summary),
    }
    log.info(
        "system_gap_analyst done: %d blocking, %d advisory",
        len(blocking),
        len(advisory),
    )
    return {"gap_analysis": gap_analysis, "error": None}
