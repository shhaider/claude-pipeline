"""Pure-python tests for build_gap_analysis_packet and build_contract_packet.

No LLM calls, no subprocesses, no network — all tests operate on pure-python
packet builder functions.
"""

from claude_pipeline.nodes.contract import build_contract_packet
from claude_pipeline.nodes.system_gap_analyst import build_gap_analysis_packet

# all 8 lenses — single source of truth for lens-name assertions
LENSES = [
    "infrastructure-assumed-but-not-mentioned",
    "silent-failure",
    "cross-cutting-concerns",
    "next-stage-prerequisites",
    "YAGNI-cut",
    "fake-completion",
    "architecture-smell",
    "developer-contract-completeness",
]


def test_gap_analysis_packet_contains_all_8_lenses():
    state = {
        "intake": {"task_type": "new_feature", "complexity_tier": 2},
        "research_brief": "Minimal brief.",
    }
    packet = build_gap_analysis_packet(state)
    assert isinstance(packet, str)
    assert len(LENSES) == 8  # all 8 lenses declared above
    for lens in LENSES:
        assert lens in packet, f"lens missing from packet: {lens!r}"


def test_gap_analysis_packet_includes_intake_and_research():
    state = {
        "intake": {
            "right_thing_answer": "SENTINEL_INTAKE_42",
            "scope_plan": "SENTINEL_SCOPE",
        },
        "research_brief": "SENTINEL_RESEARCH_99",
    }
    packet = build_gap_analysis_packet(state)
    assert "SENTINEL_INTAKE_42" in packet, "intake sentinel missing from packet"
    assert "SENTINEL_RESEARCH_99" in packet, "research sentinel missing from packet"


def test_contract_packet_injects_blocking_gaps_as_mandatory_block():
    # blocking_gaps → MANDATORY ADDITIONAL DELIVERABLES section
    state = {
        "intake": {},
        "research_brief": "",
        "gap_analysis": {
            "blocking_gaps": [
                {
                    "lens": "silent-failure",
                    "gap": "GAP_X",
                    "recommendation": "REC_Y",
                }
            ],
            "advisory_gaps": [],
            "summary": "",
        },
    }
    packet = build_contract_packet(state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" in packet
    assert "silent-failure" in packet
    assert "GAP_X" in packet
    assert "REC_Y" in packet


def test_contract_packet_injects_advisory_gaps_as_suggestions():
    # advisory_gaps → SUGGESTIONS section
    state = {
        "intake": {},
        "research_brief": "",
        "gap_analysis": {
            "blocking_gaps": [],
            "advisory_gaps": [
                {
                    "lens": "YAGNI-cut",
                    "gap": "A_GAP",
                    "recommendation": "A_REC",
                }
            ],
            "summary": "",
        },
    }
    packet = build_contract_packet(state)
    assert "SUGGESTIONS" in packet
    assert "YAGNI-cut" in packet
    assert "A_GAP" in packet
    assert "A_REC" in packet
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet


def test_contract_packet_omits_injection_when_gap_analysis_absent():
    state = {
        "intake": {"task_type": "bug_fix"},
        "research_brief": "Some brief.",
    }
    packet = build_contract_packet(state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet
    assert "SUGGESTIONS" not in packet
