"""system_gap_analyst node — adversarial pre-lane before plan/contract.

Ports metabuilder's `system_gap_analyst` role (see
`prompts/metabuilder/35_system_gap_analyst.md` for the verbatim system
prompt and `docs/metabuilder-port-spec.md` for the full porting
reference).

The node runs AFTER research and BEFORE plan. It walks the
intake decisions + research brief through 8 named lenses and emits
structured `blocking_gaps` + `advisory_gaps`. plan_node injects
blocking gaps as MANDATORY ADDITIONAL DELIVERABLES into the contract
it builds.

LLM params (metabuilder canonical):
  - Tier 3 / Opus (model='claude-opus-4-7' here; the tier router does
    not exist yet, so we name the model directly).
  - Temperature 0.2, max_tokens 8192 — NOT enforceable today: the
    `claude --print` CLI doesn't expose those flags and there is no
    tier router. Documented intent; will be enforced when the tier
    router lands (roadmap item 14 in docs/metabuilder-port-spec.md).
  - Fresh session, no resume (run_claude already starts fresh per call).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

# The 8 named lenses, in the order the role prompt expects.
LENSES: list[tuple[str, str]] = [
    (
        "infrastructure-assumed-but-not-mentioned",
        "What infrastructure (DBs, queues, env vars, secrets, services, "
        "network paths, file-system layout, OS features) does the task "
        "silently depend on but never name?",
    ),
    (
        "silent-failure",
        "Where can this code fail without anyone noticing? Swallowed "
        "exceptions, missing error logs, retries that mask root cause, "
        "defaults that hide misconfig, success returned on partial "
        "completion.",
    ),
    (
        "cross-cutting-concerns",
        "Concerns that span the change but aren't owned by any one "
        "stage: auth, authz, tenancy, observability, metrics, audit "
        "logging, rate limiting, caching, backwards compatibility, "
        "migration ordering.",
    ),
    (
        "next-stage-prerequisites",
        "What does the next piece of work (the obvious follow-up "
        "issue) need this change to set up that it currently does not? "
        "A foreign key, a schema field, a hook, a config knob, a test "
        "seam.",
    ),
    (
        "YAGNI-cut",
        "What is being built that is not needed for the stated "
        "acceptance criteria? Premature abstraction, speculative "
        "configurability, multiple implementations of one thing.",
    ),
    (
        "fake-completion",
        "Ways the implementer can mark the task done without actually "
        "meeting the goal: tests that don't exercise the new behavior, "
        "mocks that hide the real failure mode, tautological success "
        "criteria, a flag flipped without the underlying behavior.",
    ),
    (
        "architecture-smell",
        "Patterns that work but signal future pain: god-objects, "
        "circular deps, hidden coupling, ambient state, magic strings "
        "duplicated across files, configuration that drifts, layering "
        "inversions, temporary workarounds that will outlive the task.",
    ),
    (
        "developer-contract-completeness",
        "Is the developer contract (function signatures, data shapes, "
        "error types, side effects, ordering guarantees, idempotency, "
        "thread-safety) specified well enough that two implementers "
        "would build the same thing?",
    ),
]


def _role_prompt_path() -> Path:
    """Locate prompts/metabuilder/35_system_gap_analyst.md relative to
    the repo root. The package lives at <repo>/src/claude_pipeline/, so
    walk up two levels from this file to reach <repo>/."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "prompts"
        / "metabuilder"
        / "35_system_gap_analyst.md"
    )


def _format_lens_block() -> str:
    """Render the 8 lenses as an enumerated bullet list for the user
    packet. Each entry is `(N) <name> — <question>`."""
    lines: list[str] = []
    for i, (name, question) in enumerate(LENSES, start=1):
        lines.append(f"({i}) {name} — {question}")
    return "\n".join(lines)


def _format_codebase_anchor(state: PipelineState) -> str:
    """Build the codebaseAnchor block.

    Metabuilder's `buildGapAnalysisPacket` pulls structured
    `sources_consulted` + `implementation_details` from research's JSON
    output. Our research_node currently emits a free-form markdown
    brief (roadmap item 3 will upgrade it). Until then we treat the
    whole brief as the anchor and label it clearly so the model knows
    these are the only ground-truth file references it should rely on.
    """
    brief = state.get("research_brief", "").strip()
    if not brief:
        return (
            "## codebaseAnchor\n\n"
            "(no research brief available — proceed without grounded "
            "file references, and flag this as a gap)"
        )
    return (
        "## codebaseAnchor\n\n"
        "The following research brief is the ONLY ground-truth source "
        "of file paths, function names, and existing patterns. Do not "
        "invent file paths that do not appear here.\n\n"
        f"{brief}"
    )


def build_gap_analysis_packet(state: PipelineState) -> str:
    """Port of metabuilder's `buildGapAnalysisPacket(initiative, research)`.

    Pure function — no I/O, no Claude call. Returns the user-message
    string that the node sends to Claude. Exposed for unit tests.
    """
    intake = state.get("intake", {})
    intake_json = json.dumps(intake, indent=2, sort_keys=True, ensure_ascii=False)
    issue_number = state.get("issue_number", "?")
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "")

    return f"""## Adversarial gap analysis — pre-contract

You are reviewing a software task BEFORE the contract writer drafts
deliverables. Your job is to surface what is missing, unstated,
silently assumed, or architecturally smelly in the framing below.

## Task framing

**Issue #{issue_number}: {issue_title}**

ISSUE BODY:
{issue_body}

## Intake decisions

```json
{intake_json}
```

{_format_codebase_anchor(state)}

## Apply each of the 8 lenses in order

For each lens, ask the lens-specific question and emit zero or more
gaps tagged with that lens. Be specific — name the missing thing, not
the category.

{_format_lens_block()}

## Output

Return a single JSON object matching this schema exactly. No prose
preamble, no markdown fence:

{{
  "blocking_gaps": [
    {{"lens": "<one of the 8 names>", "gap": "...", "recommendation": "..."}}
  ],
  "advisory_gaps": [
    {{"lens": "<one of the 8 names>", "gap": "...", "recommendation": "..."}}
  ],
  "summary": "2-4 sentences on the most important gaps and the overall risk"
}}

Rules:
- `lens` must be one of the 8 names above, spelled exactly.
- Empty arrays are allowed if a lens genuinely finds nothing.
- Prefer fewer high-quality gaps over many weak ones.
- Do NOT propose stages, file paths, or implementation steps — the
  planner will turn your gaps into deliverables.
"""


def system_gap_analyst_node(state: PipelineState) -> dict:
    """Run the adversarial gap-analysis pass.

    Reads intake + research_brief from state, calls Claude (Tier 3 /
    Opus, fresh session) with the role prompt appended as system
    prompt, parses the JSON output, returns
    {"gap_analysis": {...}, "error": None}.

    On any failure (missing role prompt, Claude error, malformed JSON,
    wrong shape) returns {"error": "..."} per the existing
    error-slice convention used by research_node and plan_node.
    """
    role_prompt = _role_prompt_path()
    if not role_prompt.exists():
        return {
            "error": (
                f"system_gap_analyst: role prompt not found at {role_prompt}"
            )
        }

    packet = build_gap_analysis_packet(state)

    log.info(
        "system_gap_analyst: invoking claude (Tier 3 / Opus, fresh session)"
    )
    try:
        result = run_claude(
            packet,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="claude-opus-4-7",
            extra_args=["--append-system-prompt", str(role_prompt)],
        )
    except ClaudeError as e:
        return {"error": f"system_gap_analyst: claude call failed: {e}"}

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
                "system_gap_analyst: expected JSON object, got "
                f"{type(parsed).__name__}"
            )
        }

    gap_analysis: dict = {
        "blocking_gaps": list(parsed.get("blocking_gaps") or []),
        "advisory_gaps": list(parsed.get("advisory_gaps") or []),
        "summary": str(parsed.get("summary") or ""),
    }

    log.info(
        "system_gap_analyst done: %d blocking, %d advisory "
        "(%.1fs, cost=$%.4f, turns=%d)",
        len(gap_analysis["blocking_gaps"]),
        len(gap_analysis["advisory_gaps"]),
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )
    return {"gap_analysis": gap_analysis, "error": None}
