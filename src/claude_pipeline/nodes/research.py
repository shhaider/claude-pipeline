"""Research node: codebase-grounded research with implementation-level
findings.

Verbatim port of metabuilder's research_lead role:
  - System prompt = `prompts/metabuilder/04_research_lead.md` (used via
    `--append-system-prompt`).
  - User message = Python equivalent of `buildResearchPacket()` from
    `scripts/metabuilder/plan_self_upgrade.js:704`.
  - Deterministic side-channel = `gather_relevant_excerpts()` from
    `claude_pipeline.excerpts`.
  - Tier 3: model=Opus.

Output schema (per port spec):
  {
    "evidence_summary": str,
    "key_findings": [str, ...],
    "implementation_details": [str, ...],
    "gaps_identified": [str, ...],
    "confidence": "high|medium|low",
    "sources_consulted": ["file:line - what was found", ...]
  }

Falls back to a free-text brief if JSON parsing fails — keeps the
pipeline moving even when the model goes off-spec.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.excerpts import gather_relevant_excerpts
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder"
_RESEARCH_LEAD_PATH = _PROMPTS_DIR / "04_research_lead.md"


def _load_role_prompt() -> str:
    """Load the verbatim 04_research_lead.md content for use as a system
    prompt. Cached lazily — we don't want to fail at import time if the
    file is briefly missing during a partial checkout."""
    try:
        return _RESEARCH_LEAD_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing research_lead role prompt at {_RESEARCH_LEAD_PATH}: {e}"
        ) from e


# User-message template — Python port of buildResearchPacket().
USER_PACKET_TEMPLATE = """{lesson_block}

## Planning Research Task

You are acting as research_lead for a MetaBuilder planning request.

**Initiative ID:** {initiative_id}
**Planning request:** {planning_request}

**Your task:**
Research the current codebase state relevant to this planning request.
Identify: what already exists, what is missing, what the key risks are.

**Important - implementation-level research:**
You must identify specific implementation details that an implementer would need:
- Exact function signatures (name, arguments, return shape)
- Default values that would change during extraction or refactoring (e.g., hardcoded max_tokens)
- Injectable seam patterns or test hooks that must be preserved
- Test runner conventions (e.g., which test framework, any shims or adapters)
- Policy table values (e.g., mandatory source classes for specific task_class values)
These details prevent silent regressions that high-level findings miss.

**Relevant source file excerpts (from the codebase):**
{excerpts}

**Scope constraints:**
- Focus only on what is directly relevant to the planning request above
- Do not research unrelated capabilities
- Limit your output to the most important 5-8 findings
- At least 2 findings must be implementation-level details (signatures, defaults, patterns)

**Output format:**
Return a JSON object:
{{
  "evidence_summary": "2-3 sentence summary of findings",
  "key_findings": ["finding 1", "finding 2", "..."],
  "implementation_details": ["detail 1: exact function signature or default value", "..."],
  "gaps_identified": ["gap 1", "gap 2"],
  "confidence": "high|medium|low",
  "sources_consulted": ["file:line - what was found"]
}}
"""


def _build_user_packet(state: PipelineState, excerpts: str) -> str:
    intake = state.get("intake", {})
    issue_title = state.get("issue_title", "")
    issue_body = state.get("issue_body", "")

    # The "planning request" is the union of intake.scope_plan + issue
    # — enough for the model to grep for relevant tokens. Use a compact
    # form so the prompt stays readable.
    planning_request_lines = [
        f"Issue title: {issue_title}",
        "",
        f"Issue body: {issue_body}",
        "",
        f"Task type: {intake.get('task_type', '?')}",
        f"Complexity tier: {intake.get('complexity_tier', '?')}",
        f"Scope plan: {intake.get('scope_plan', '?')}",
        f"Right-thing check: {intake.get('right_thing_answer', '?')}",
        "Acceptance criteria:",
    ]
    for c in intake.get("acceptance_criteria", []):
        planning_request_lines.append(f"  - {c}")
    planning_request_lines.append(f"Wiring plan: {intake.get('wiring_plan', '?')}")
    planning_request = "\n".join(planning_request_lines)

    initiative_id = f"{state.get('repo', '?')}#{state.get('issue_number', '?')}"

    # Lesson block — metabuilder injects a prior-lessons reminder. We
    # leave it empty for now (no LessonStore in this pipeline yet).
    lesson_block = "(no prior lessons configured)"

    return USER_PACKET_TEMPLATE.format(
        lesson_block=lesson_block,
        initiative_id=initiative_id,
        planning_request=planning_request,
        excerpts=excerpts if excerpts.strip() else "(no excerpts gathered)",
    )


def research_node(state: PipelineState) -> dict:
    worktree = state.get("worktree_path") or "."

    # Build the planning-request blob we use to extract grep tokens.
    intake = state.get("intake", {})
    grep_source = "\n".join(
        [
            state.get("issue_title", ""),
            state.get("issue_body", ""),
            intake.get("scope_plan", ""),
            intake.get("wiring_plan", ""),
            "\n".join(intake.get("acceptance_criteria", []) or []),
        ]
    )

    # Deterministic preprocessing — inline real code excerpts so the
    # model doesn't hallucinate file paths.
    excerpts = gather_relevant_excerpts(grep_source, worktree)
    log.info("research: gathered excerpts (%d chars)", len(excerpts))

    user_msg = _build_user_packet(state, excerpts)

    try:
        role_prompt = _load_role_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    log.info("research: invoking claude (opus, role=research_lead)")
    try:
        result = run_claude(
            user_msg,
            cwd=worktree,
            timeout_s=600,
            model="opus",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return {"error": f"research: claude call failed: {e}"}

    log.info(
        "research: claude returned (%.1fs, cost=$%.4f, turns=%d)",
        result.duration_s,
        result.cost_usd,
        result.num_turns,
    )

    text = result.text.strip()
    if not text:
        return {"error": "research: claude returned empty output"}

    # Try structured parse first.
    parsed: dict | None = None
    try:
        raw = extract_json(text)
        if isinstance(raw, dict):
            parsed = raw
    except (ValueError, json.JSONDecodeError):
        parsed = None

    # research_brief is a markdown rendering of the packet (for the
    # downstream contract+plan nodes). Always set it so callers don't
    # need to branch on parsed-vs-not.
    if parsed is not None:
        brief_lines = [
            "## Research evidence summary",
            "",
            str(parsed.get("evidence_summary", "(missing)")),
            "",
            "## Key findings",
            "",
        ]
        for f in parsed.get("key_findings", []) or []:
            brief_lines.append(f"- {f}")
        brief_lines.extend(["", "## Implementation details", ""])
        for d in parsed.get("implementation_details", []) or []:
            brief_lines.append(f"- {d}")
        brief_lines.extend(["", "## Gaps identified", ""])
        for g in parsed.get("gaps_identified", []) or []:
            brief_lines.append(f"- {g}")
        brief_lines.extend(
            [
                "",
                f"## Confidence: {parsed.get('confidence', 'unknown')}",
                "",
                "## Sources consulted",
                "",
            ]
        )
        for s in parsed.get("sources_consulted", []) or []:
            brief_lines.append(f"- {s}")
        brief = "\n".join(brief_lines)
        log.info(
            "research done: structured packet (%d findings, %d impl details)",
            len(parsed.get("key_findings", []) or []),
            len(parsed.get("implementation_details", []) or []),
        )
        return {
            "research_brief": brief,
            "research_packet": parsed,
            "excerpts": excerpts,
            "error": None,
        }

    # Fallback — treat the whole text as a markdown brief.
    log.warning("research: JSON parse failed — using free-text fallback")
    return {
        "research_brief": text,
        "research_packet": {},
        "excerpts": excerpts,
        "error": None,
    }
