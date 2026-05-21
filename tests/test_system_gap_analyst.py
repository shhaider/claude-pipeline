"""Pure-python tests for system_gap_analyst packet builder + the
blocking-gap injection into contract_writer's user packet.

No LLM calls — all tests operate on fixture state dicts and assert on
the strings the packet builders emit.
"""

from __future__ import annotations

import json

import pytest

from claude_pipeline.nodes.contract import build_contract_packet
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_state() -> dict:
    """Minimal pipeline state up to (but not past) gap-analyst input.

    Mirrors the shape produced by intake + research at the point the
    system_gap_analyst would fire.
    """
    return {
        "issue_number": 9,
        "issue_title": "Port system_gap_analyst from metabuilder",
        "issue_body": "We need an adversarial pre-pass before contract_writer.",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 2,
            "scope_plan": "Single node insertion plus packet builder.",
            "risk_flags": ["api_contract"],
            "right_thing_answer": "Yes, this matches the metabuilder roadmap.",
            "acceptance_criteria": [
                "system_gap_analyst_node exists",
                "graph topology updated",
                "tests pass",
            ],
            "wiring_plan": "Touches graph.py, state.py, new nodes/system_gap_analyst.py.",
        },
        "research_brief": (
            "## Current code shape\n\nThe pipeline currently routes "
            "research → plan directly with no adversarial pre-pass.\n"
        ),
        "research": {
            "sources_consulted": [
                "src/claude_pipeline/graph.py:67 — research edge points at plan",
                "docs/metabuilder-port-spec.md:222 — gap_analyst is roadmap item 6",
            ],
            "implementation_details": [
                "run_claude signature: run_claude(prompt, *, cwd, timeout_s, ...) -> ClaudeResult",
                "extract_json handles fenced and prose-prefixed JSON",
            ],
        },
    }


@pytest.fixture
def state_with_gap_analysis(base_state: dict) -> dict:
    """base_state plus a populated gap_analysis dict (blocking + advisory)."""
    base_state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "No prompt file at prompts/metabuilder/35_system_gap_analyst.md.",
                "recommendation": "Add the verbatim role prompt as part of this issue.",
            },
            {
                "lens": "silent-failure",
                "gap": "If gap_analysis fails, contract_writer receives no signal.",
                "recommendation": "Make contract_writer log when gap_analysis is missing.",
            },
        ],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "We do not need cto_orchestrator in this issue.",
                "recommendation": "Defer cto_orchestrator to its own issue.",
            },
        ],
        "summary": "Most important: ship the prompt file and wire the node into the graph.",
    }
    return base_state


# ---------------------------------------------------------------------------
# Test (a) — packet contains all 8 lenses
# ---------------------------------------------------------------------------


def test_packet_contains_all_eight_lenses(base_state: dict) -> None:
    packet = build_gap_analysis_packet(base_state)
    expected_lens_names = [
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    ]
    # Sanity: the LENSES constant agrees with the canonical list.
    assert [name for name, _desc in LENSES] == expected_lens_names

    # Each lens name must appear in the rendered packet.
    for lens_name in expected_lens_names:
        assert lens_name in packet, f"lens {lens_name!r} missing from packet"

    # And the count of lenses is exactly 8 — not 7, not 9.
    assert len(LENSES) == 8


# ---------------------------------------------------------------------------
# Test (b) — packet includes intake + research
# ---------------------------------------------------------------------------


def test_packet_includes_intake_and_research(base_state: dict) -> None:
    packet = build_gap_analysis_packet(base_state)

    # Intake fields surface as a JSON-encoded block.
    assert '"task_type": "new_feature"' in packet
    assert '"complexity_tier": 2' in packet
    assert "system_gap_analyst_node exists" in packet  # acceptance criterion
    assert "api_contract" in packet  # risk flag

    # Research brief text is embedded.
    assert "research → plan directly" in packet

    # Structured research feeds the codebaseAnchor block.
    assert "codebaseAnchor" in packet
    assert "src/claude_pipeline/graph.py:67" in packet
    assert "implementation_details" in packet.lower() or "Implementation details" in packet
    assert "run_claude signature" in packet


def test_packet_falls_back_to_brief_when_no_structured_research(base_state: dict) -> None:
    # Drop the structured research dict; the packet should still build a
    # codebaseAnchor block from the markdown brief alone.
    base_state.pop("research", None)
    packet = build_gap_analysis_packet(base_state)
    assert "codebaseAnchor" in packet
    assert "research → plan directly" in packet


# ---------------------------------------------------------------------------
# Test (c) — blocking gaps get injected into contract input
# ---------------------------------------------------------------------------


def test_blocking_gaps_injected_as_mandatory_into_contract_packet(
    state_with_gap_analysis: dict,
) -> None:
    packet = build_contract_packet(state_with_gap_analysis)

    # The MANDATORY block must be present and labelled as such.
    assert "MANDATORY ADDITIONAL DELIVERABLES" in packet
    assert "must be covered" in packet.lower() or "MUST be covered" in packet

    # Every blocking gap (text + lens + recommendation) must be in the packet.
    for g in state_with_gap_analysis["gap_analysis"]["blocking_gaps"]:
        assert g["lens"] in packet
        assert g["gap"] in packet
        assert g["recommendation"] in packet


def test_no_gap_block_when_gap_analysis_absent(base_state: dict) -> None:
    # When gap_analysis is missing, the contract packet should not
    # invent a mandatory/suggested block.
    assert "gap_analysis" not in base_state
    packet = build_contract_packet(base_state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet
    assert "SUGGESTED ADDITIONAL DELIVERABLES" not in packet
    # Intake and research are still there.
    assert '"task_type": "new_feature"' in packet
    assert "research → plan directly" in packet


# ---------------------------------------------------------------------------
# Test (d) — advisory gaps are present but not marked mandatory
# ---------------------------------------------------------------------------


def test_advisory_gaps_present_but_not_mandatory(
    state_with_gap_analysis: dict,
) -> None:
    packet = build_contract_packet(state_with_gap_analysis)

    # Advisory block is labelled SUGGESTED, not MANDATORY.
    assert "SUGGESTED ADDITIONAL DELIVERABLES" in packet
    assert "advisory only" in packet.lower()

    # The advisory gap text appears in the packet.
    advisory = state_with_gap_analysis["gap_analysis"]["advisory_gaps"][0]
    assert advisory["lens"] in packet
    assert advisory["gap"] in packet
    assert advisory["recommendation"] in packet

    # Crucially: the advisory gap's body text must NOT appear inside the
    # MANDATORY block — split by section heading and check.
    mandatory_start = packet.index("MANDATORY ADDITIONAL DELIVERABLES")
    suggested_start = packet.index("SUGGESTED ADDITIONAL DELIVERABLES")
    assert mandatory_start < suggested_start, (
        "MANDATORY block must precede SUGGESTED block in the packet"
    )
    mandatory_block = packet[mandatory_start:suggested_start]
    assert advisory["gap"] not in mandatory_block, (
        "advisory gap leaked into the mandatory section"
    )


# ---------------------------------------------------------------------------
# Bonus coverage — summary surfaces, JSON output schema is described
# ---------------------------------------------------------------------------


def test_gap_summary_surfaces_in_contract_packet(
    state_with_gap_analysis: dict,
) -> None:
    packet = build_contract_packet(state_with_gap_analysis)
    assert state_with_gap_analysis["gap_analysis"]["summary"] in packet


def test_gap_packet_describes_output_schema(base_state: dict) -> None:
    packet = build_gap_analysis_packet(base_state)
    # The packet must instruct the model on the output JSON shape so the
    # node's downstream parser has something to parse.
    assert "blocking_gaps" in packet
    assert "advisory_gaps" in packet
    assert "summary" in packet
    # Output must demand JSON only (no prose, no fence).
    assert "VALID JSON ONLY" in packet


def test_intake_is_round_trippable_json(base_state: dict) -> None:
    """Sanity check that the intake block we emit is parseable JSON, so
    the downstream model is not fed malformed input."""
    packet = build_gap_analysis_packet(base_state)
    # Pull the JSON block between the ```json fence and the closing ```.
    start_tag = "```json\n"
    end_tag = "\n```"
    start = packet.index(start_tag) + len(start_tag)
    end = packet.index(end_tag, start)
    parsed = json.loads(packet[start:end])
    assert parsed["task_type"] == "new_feature"
    assert parsed["complexity_tier"] == 2
