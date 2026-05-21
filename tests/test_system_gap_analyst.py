"""Tests for the system_gap_analyst pre-lane.

Pure-python: exercises the packet builder and the plan-injection
renderer directly with fixture state dicts. Does NOT invoke `claude`.
"""

from __future__ import annotations

import pytest

from claude_pipeline.nodes.plan import _render_gap_blocks
from claude_pipeline.nodes.system_gap_analyst import (
    CANONICAL_LENS_SLUGS,
    LENSES,
    _build_gap_analysis_packet,
)


# Sanity: the 8 lens slugs are the canonical set.
CANONICAL_SLUGS = {
    "infrastructure-assumed-but-not-mentioned",
    "silent-failure",
    "cross-cutting-concerns",
    "next-stage-prerequisites",
    "YAGNI-cut",
    "fake-completion",
    "architecture-smell",
    "developer-contract-completeness",
}


@pytest.fixture
def fixture_state() -> dict:
    return {
        "repo": "acme/widgets",
        "issue_number": 42,
        "issue_title": "Add a /healthz endpoint",
        "issue_body": "We need a tiny health endpoint for the load balancer.",
        "worktree_path": "/tmp/does-not-matter",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 1,
            "scope_plan": "Add one route handler and wire it up.",
            "risk_flags": [],
            "right_thing_answer": "Yes, simple health probe.",
            "acceptance_criteria": [
                "GET /healthz returns 200",
                "Response body includes a uptime field",
                "Unit test covers the new route",
            ],
            "wiring_plan": "Touch the HTTP router module and add one handler.",
        },
        "research_brief": (
            "## Current code shape\n\n"
            "The router lives at `src/widgets/http.py` and exposes a register()\n"
            "function. There is no existing health endpoint.\n\n"
            "## Recommended approach\n\nAdd a thin handler.\n"
        ),
    }


def test_canonical_lens_slugs_match_node_constant():
    assert CANONICAL_LENS_SLUGS == CANONICAL_SLUGS
    assert {slug for slug, _ in LENSES} == CANONICAL_SLUGS


def test_packet_contains_all_eight_lenses(fixture_state):
    packet = _build_gap_analysis_packet(fixture_state)
    for slug in CANONICAL_SLUGS:
        assert slug in packet, f"packet missing lens slug {slug!r}"


def test_packet_includes_intake_and_research(fixture_state):
    packet = _build_gap_analysis_packet(fixture_state)
    # Intake fields
    assert "new_feature" in packet
    for criterion in fixture_state["intake"]["acceptance_criteria"]:
        assert criterion in packet
    # Research brief substring
    assert "src/widgets/http.py" in packet
    # Issue identity
    assert "#42" in packet
    assert "/healthz endpoint" in packet


def test_packet_omits_anchor_gracefully_when_missing(fixture_state):
    # No research_anchor key — should not raise; should fall back to
    # the research brief under the Codebase anchor heading.
    packet = _build_gap_analysis_packet(fixture_state)
    assert "## Codebase anchor" in packet
    assert "src/widgets/http.py" in packet  # brief content reappears under the anchor


def test_packet_uses_structured_anchor_when_present(fixture_state):
    fixture_state["research_anchor"] = {
        "sources_consulted": ["src/widgets/http.py:12 — register() entry point"],
        "implementation_details": ["register(app) signature returns None"],
    }
    packet = _build_gap_analysis_packet(fixture_state)
    assert "Sources consulted" in packet
    assert "register() entry point" in packet
    assert "Implementation details" in packet


def test_plan_injection_marks_blocking_as_mandatory():
    gap_analysis = {
        "blocking_gaps": [
            {
                "lens": "silent-failure",
                "gap": "Handler returns 200 even when the DB is down",
                "recommendation": "Probe the DB and surface a 503 on failure",
            },
            {
                "lens": "cross-cutting-concerns",
                "gap": "No logging on the new route",
                "recommendation": "Emit one INFO log per request",
            },
        ],
        "advisory_gaps": [],
        "summary": "Two blocking framing gaps.",
    }
    block = _render_gap_blocks(gap_analysis)
    assert "MANDATORY" in block
    assert "MUST" in block
    assert "Handler returns 200 even when the DB is down" in block
    assert "No logging on the new route" in block
    assert "silent-failure" in block
    assert "cross-cutting-concerns" in block


def test_plan_injection_advisory_not_mandatory():
    gap_analysis = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "Proposed config flag has no consumer",
                "recommendation": "Drop the flag until a consumer exists",
            },
        ],
        "summary": "One advisory consideration.",
    }
    block = _render_gap_blocks(gap_analysis)
    assert "MANDATORY" not in block
    assert "MUST" not in block
    assert "Advisory" in block
    assert "Proposed config flag has no consumer" in block
    assert "YAGNI-cut" in block


def test_plan_injection_empty_gap_analysis_renders_empty_string():
    assert _render_gap_blocks({}).strip() == ""
    assert _render_gap_blocks({"blocking_gaps": [], "advisory_gaps": []}).strip() == ""
    assert _render_gap_blocks(None).strip() == ""


def test_plan_injection_both_blocking_and_advisory():
    gap_analysis = {
        "blocking_gaps": [
            {
                "lens": "fake-completion",
                "gap": "Test asserts 200 only",
                "recommendation": "Assert body shape too",
            },
        ],
        "advisory_gaps": [
            {
                "lens": "next-stage-prerequisites",
                "gap": "No /readyz scaffolding",
                "recommendation": "Leave a router seam",
            },
        ],
        "summary": "Mixed.",
    }
    block = _render_gap_blocks(gap_analysis)
    assert "MANDATORY" in block
    assert "Advisory" in block
    assert "Test asserts 200 only" in block
    assert "No /readyz scaffolding" in block
