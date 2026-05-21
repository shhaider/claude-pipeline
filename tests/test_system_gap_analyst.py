"""Pure-python tests for the system_gap_analyst pre-lane.

No LLM calls — exercise the packet builder and the contract_writer's
blocking-gap injection using fixture state dicts.
"""

from __future__ import annotations

import pytest

from claude_pipeline.nodes.contract import build_contract_packet
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
)


LENS_NAMES = [name for name, _ in LENSES]


@pytest.fixture
def base_state() -> dict:
    """A representative pipeline state at the point system_gap_analyst
    fires: intake decisions + research brief populated, gap_analysis
    and contract not yet set."""
    return {
        "run_id": "run_test_001",
        "repo": "shhaider/claude-pipeline",
        "issue_number": 9,
        "issue_title": "Port system_gap_analyst",
        "worktree_path": "/tmp/wt",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "scope_plan": "Add adversarial pre-lane node + wire into graph.",
            "risk_flags": ["api_contract"],
            "right_thing_answer": "Yes — gaps in intake silently rot plans.",
            "acceptance_criteria": [
                "system_gap_analyst node exists",
                "graph topology has the new node between research and contract",
                "blocking gaps reach contract_writer",
            ],
            "wiring_plan": "src/claude_pipeline/{nodes,graph,state}.py",
        },
        "research_brief": (
            "## Current code shape\n"
            "- src/claude_pipeline/graph.py — LangGraph wiring\n"
            "- src/claude_pipeline/nodes/research.py — research node\n"
            "## Touch points\n"
            "- build_graph() — add new node + edges\n"
        ),
    }


@pytest.fixture
def gap_analysis_with_findings() -> dict:
    return {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "Plan presupposes a prompts/metabuilder/ dir with files committed.",
                "recommendation": "Add a deliverable that creates the prompt file.",
            },
            {
                "lens": "developer-contract-completeness",
                "gap": "No acceptance criterion for graph topology change.",
                "recommendation": "Add 'mermaid render shows new node' as criterion.",
            },
        ],
        "advisory_gaps": [
            {
                "lens": "cross-cutting-concerns",
                "gap": "New node has no structured logging fields.",
                "recommendation": "Mirror research node's log.info pattern.",
            },
        ],
        "summary": "Two blocking gaps around prompt-file provisioning and topology criteria.",
    }


# (a) packet contains all 8 lenses ---------------------------------------------

def test_gap_packet_contains_all_eight_lenses(base_state):
    packet = build_gap_analysis_packet(base_state)
    # All 8 lens names must appear verbatim in the packet so the model
    # is told exactly what to apply.
    assert len(LENS_NAMES) == 8, "expected exactly 8 lenses defined"
    for lens in LENS_NAMES:
        assert lens in packet, f"lens {lens!r} missing from gap-analysis packet"


def test_gap_packet_lenses_are_the_metabuilder_eight(base_state):
    expected = {
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    }
    assert set(LENS_NAMES) == expected


# (b) packet includes intake + research ----------------------------------------

def test_gap_packet_includes_intake_decisions(base_state):
    packet = build_gap_analysis_packet(base_state)
    # Intake fields must surface so the analyst is grounded in the framing.
    assert "new_feature" in packet  # task_type value
    assert "complexity_tier" in packet
    assert "api_contract" in packet  # risk_flag value
    assert base_state["intake"]["scope_plan"] in packet


def test_gap_packet_includes_research_brief(base_state):
    packet = build_gap_analysis_packet(base_state)
    assert "## Research brief" in packet
    assert "LangGraph wiring" in packet  # snippet from the brief fixture
    # Codebase anchor block must be present even when research brief is
    # plain markdown (graceful degradation).
    assert "## Codebase anchor" in packet


def test_gap_packet_includes_issue_identifier(base_state):
    packet = build_gap_analysis_packet(base_state)
    assert "Issue #9" in packet
    assert "Port system_gap_analyst" in packet


# (c) blocking gaps get injected into contract input ---------------------------

def test_blocking_gaps_injected_as_mandatory_into_contract_packet(
    base_state, gap_analysis_with_findings
):
    state = {**base_state, "gap_analysis": gap_analysis_with_findings}
    packet = build_contract_packet(state)

    # The MANDATORY heading must be present.
    assert "MANDATORY ADDITIONAL DELIVERABLES" in packet
    # Each blocking gap's text and recommendation must appear.
    for g in gap_analysis_with_findings["blocking_gaps"]:
        assert g["gap"] in packet, f"blocking gap text missing: {g['gap']!r}"
        assert g["recommendation"] in packet
        assert g["lens"] in packet
    # The contract output schema must require source_goal tagging so
    # the contract writer can't silently drop a blocking gap.
    assert "gap_analysis_blocking" in packet


def test_blocking_gaps_absent_when_gap_analysis_empty(base_state):
    state = {**base_state, "gap_analysis": {"blocking_gaps": [], "advisory_gaps": []}}
    packet = build_contract_packet(state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet
    assert "Advisory suggestions" not in packet


def test_contract_packet_works_without_gap_analysis_key(base_state):
    # Backwards-compat: contract_writer must still build a valid packet
    # if state doesn't have gap_analysis yet (e.g. resumed run from
    # before this upgrade).
    packet = build_contract_packet(base_state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet
    assert "contract_title" in packet  # output-schema text always present


# (d) advisory gaps are present but not marked mandatory -----------------------

def test_advisory_gaps_injected_as_suggestions_not_mandatory(
    base_state, gap_analysis_with_findings
):
    state = {**base_state, "gap_analysis": gap_analysis_with_findings}
    packet = build_contract_packet(state)

    advisory = gap_analysis_with_findings["advisory_gaps"][0]
    # Advisory section heading must be present.
    assert "Advisory suggestions" in packet
    # Advisory text and recommendation must surface.
    assert advisory["gap"] in packet
    assert advisory["recommendation"] in packet

    # Advisory gaps must NOT be flagged as mandatory.
    advisory_idx = packet.index(advisory["gap"])
    blocking_idx = packet.index("MANDATORY ADDITIONAL DELIVERABLES")
    assert advisory_idx > blocking_idx, (
        "advisory section should appear AFTER the mandatory section, "
        "so prompt order makes the distinction clear"
    )

    # Spot-check: the word 'suggestion' must appear in the advisory
    # framing (it's how the contract writer is told these are optional).
    advisory_block_start = packet.index("Advisory suggestions")
    advisory_block = packet[advisory_block_start:]
    assert "suggestion" in advisory_block.lower()
    assert "NOT mandatory" in advisory_block
