"""Pure-python tests for system_gap_analyst.

Covers the packet builder + the blocking-gap injection into plan_node's
prompt. No LLM calls — every test runs against fixture state dicts.
"""

from __future__ import annotations

import json

from claude_pipeline.nodes.plan import (
    PROMPT_TEMPLATE as PLAN_PROMPT_TEMPLATE,
    _format_gap_analysis_block,
)
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
)


# ---- fixtures ----


def _fixture_state() -> dict:
    """A representative PipelineState with intake + research populated."""
    return {
        "repo": "shhaider/claude-pipeline",
        "issue_number": 9,
        "issue_title": "Port system_gap_analyst from metabuilder",
        "issue_body": (
            "Add an adversarial gap-analysis pass between research and "
            "contract. Apply the 8 named lenses to find unstated "
            "dependencies and silent-failure modes."
        ),
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "scope_plan": "Single feature: add a new node + state field + tests",
            "risk_flags": ["llm_routing"],
            "right_thing_answer": "Yes — close the gap-analysis hole in v0.1.",
            "acceptance_criteria": [
                "new node exists with system_gap_analyst_node fn",
                "graph routes research -> gap_analyst -> next",
                "blocking gaps inject into plan prompt",
            ],
            "wiring_plan": "Touches state.py, graph.py, plan.py, README.md",
        },
        "research_brief": (
            "## Current code shape\n\n"
            "v0.1 scaffold with nodes intake/research/plan/code/verify/pr. "
            "No contract.py yet. plan.py PROMPT_TEMPLATE consumes intake "
            "and research_brief.\n"
        ),
    }


# ---- (a) packet contains all 8 lenses ----


def test_packet_contains_all_8_lenses():
    """Required: the packet must spell out every one of the 8 named lenses."""
    state = _fixture_state()
    packet = build_gap_analysis_packet(state)
    # Each lens name appears verbatim
    expected = [
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    ]
    assert len(LENSES) == 8, "LENSES table must have exactly 8 entries"
    for lens_name in expected:
        assert lens_name in packet, f"packet missing lens: {lens_name}"
    # Numbered "Lens 1" .. "Lens 8" must appear
    for i in range(1, 9):
        assert f"Lens {i}" in packet, f"packet missing 'Lens {i}' header"


# ---- (b) packet includes intake + research ----


def test_packet_includes_intake_and_research():
    """Required: packet must include both intake decisions and research brief."""
    state = _fixture_state()
    packet = build_gap_analysis_packet(state)

    # intake fields are serialized into the packet
    assert "new_feature" in packet  # task_type
    assert "llm_routing" in packet  # risk_flags entry
    assert "Single feature: add a new node" in packet  # scope_plan

    # research brief content appears in the packet (as codebaseAnchor)
    assert "v0.1 scaffold" in packet
    assert "PROMPT_TEMPLATE consumes intake" in packet

    # codebaseAnchor heading is explicit
    assert "codebaseAnchor" in packet

    # issue title + body included
    assert "Port system_gap_analyst from metabuilder" in packet
    assert "adversarial gap-analysis pass" in packet


# ---- (c) blocking gaps get injected into plan input as MANDATORY ----


def test_blocking_gaps_injected_into_plan_prompt():
    """Required: blocking gaps must appear in the plan prompt as MANDATORY
    ADDITIONAL DELIVERABLES. The plan node injects them via
    _format_gap_analysis_block, which is interpolated into PROMPT_TEMPLATE."""
    state = _fixture_state()
    state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "No prompts/ directory exists in the repo to hold role files",
                "recommendation": "Create prompts/metabuilder/ and copy the role file",
            },
            {
                "lens": "developer-contract-completeness",
                "gap": "Acceptance criteria do not state failure conditions",
                "recommendation": "Add explicit 'fails if' criteria to the contract",
            },
        ],
        "advisory_gaps": [],
        "summary": "Biggest blind spot: the role-prompt path assumes a directory that doesn't exist.",
    }

    block = _format_gap_analysis_block(state["gap_analysis"])
    # The block names the MANDATORY framing
    assert "MANDATORY ADDITIONAL DELIVERABLES" in block
    # Each blocking gap appears, with its lens name
    assert "infrastructure-assumed-but-not-mentioned" in block
    assert "No prompts/ directory exists" in block
    assert "developer-contract-completeness" in block
    assert "Acceptance criteria do not state failure conditions" in block
    # Recommendations appear too
    assert "Create prompts/metabuilder/" in block
    # Summary surfaces
    assert "Biggest blind spot" in block

    # And the block actually substitutes into the plan prompt
    rendered = PLAN_PROMPT_TEMPLATE.format(
        intake_json=json.dumps(state["intake"], indent=2),
        research_brief=state["research_brief"],
        gap_analysis_block=block,
        issue_number=state["issue_number"],
        issue_title=state["issue_title"],
    )
    assert "MANDATORY ADDITIONAL DELIVERABLES" in rendered
    assert "No prompts/ directory exists" in rendered


# ---- (d) advisory gaps appear but are NOT marked mandatory ----


def test_advisory_gaps_present_but_not_mandatory():
    """Required: advisory gaps must show up in the block as suggestions
    only — not under the MANDATORY framing."""
    gap_analysis = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "Tier override could be configurable, but isn't needed yet",
                "recommendation": "Defer until a second caller appears",
            },
            {
                "lens": "cross-cutting-concerns",
                "gap": "Observability hooks are not added for the new node",
                "recommendation": "Optional: add a log line on entry/exit",
            },
        ],
        "summary": "No structural blocking gaps. A couple of nice-to-haves only.",
    }
    block = _format_gap_analysis_block(gap_analysis)

    # The block includes the advisory section header
    assert "Advisory gaps (suggestions, not requirements)" in block
    # The advisory gap text appears
    assert "Tier override could be configurable" in block
    assert "Observability hooks are not added" in block
    # CRITICAL: with no blocking gaps, the MANDATORY framing must not appear
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in block
    # Each advisory entry is labeled as advisory (not blocking)
    assert "[advisory-1]" in block
    assert "[advisory-2]" in block
    assert "[BLOCKING-" not in block


# ---- extra: block is empty / no-op when gap_analysis is missing ----


def test_empty_gap_analysis_produces_no_block():
    """Sanity: if gap_analysis is absent (e.g. node was skipped), the
    block is empty so the existing plan prompt is unchanged."""
    assert _format_gap_analysis_block({}) == ""
    assert _format_gap_analysis_block(None) == ""  # type: ignore[arg-type]
    assert (
        _format_gap_analysis_block(
            {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}
        )
        == ""
    )


# ---- extra: output schema fields are named in the packet ----


def test_packet_states_required_output_schema():
    """The packet must tell the model the exact output keys we'll parse."""
    packet = build_gap_analysis_packet(_fixture_state())
    assert '"blocking_gaps"' in packet
    assert '"advisory_gaps"' in packet
    assert '"summary"' in packet
