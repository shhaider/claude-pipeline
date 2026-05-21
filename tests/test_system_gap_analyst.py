"""Pure-python tests for the system_gap_analyst pre-lane.

No LLM calls. We exercise build_gap_analysis_packet (the packet the
analyst sends to Claude) and build_contract_packet (the packet the
contract writer sends to Claude with blocking gaps injected as
MANDATORY ADDITIONAL DELIVERABLES).
"""

from __future__ import annotations

from claude_pipeline.nodes.contract import build_contract_packet
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
)


LENS_NAMES = [
    "infrastructure-assumed-but-not-mentioned",
    "silent-failure",
    "cross-cutting-concerns",
    "next-stage-prerequisites",
    "YAGNI-cut",
    "fake-completion",
    "architecture-smell",
    "developer-contract-completeness",
]


def _fixture_intake() -> dict:
    return {
        "task_type": "new_feature",
        "complexity_tier": 3,
        "scope_plan": "Single feature with subphases",
        "risk_flags": ["llm_routing"],
        "right_thing_answer": "Yes — adversarial pre-lane is a known good pattern",
        "acceptance_criteria": [
            "ACCEPT_SENTINEL_42 — node file exists",
            "Mermaid topology includes new edges",
        ],
        "wiring_plan": "Touches state.py, graph.py, nodes/system_gap_analyst.py",
    }


def _fixture_gap_analysis() -> dict:
    return {
        "blocking_gaps": [
            {
                "lens": "silent-failure",
                "gap": "NEEDS_DB_MIGRATION — schema column added without backfill",
                "recommendation": "Add a migration step with backfill before deploy",
            }
        ],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "ADVISORY_SENTINEL — could ship structured metrics but defer",
                "recommendation": "Defer",
            }
        ],
        "summary": "Schema-without-backfill is the biggest blind spot.",
    }


# ---- (a) packet contains all 8 named lenses -------------------------------


def test_packet_contains_all_eight_lens_names():
    packet = build_gap_analysis_packet(_fixture_intake(), "research brief here")
    for name in LENS_NAMES:
        assert name in packet, f"lens name {name!r} missing from packet"
    assert len(LENSES) == 8, "LENSES export must have exactly 8 entries"


# ---- (b) packet includes intake + research --------------------------------


def test_packet_embeds_intake_and_research_brief():
    intake = _fixture_intake()
    research_brief = "RESEARCH_SENTINEL_99 — touches state.py and graph.py"
    packet = build_gap_analysis_packet(intake, research_brief)
    assert "ACCEPT_SENTINEL_42" in packet, "intake acceptance criteria not embedded"
    assert "RESEARCH_SENTINEL_99" in packet, "research_brief not embedded"
    assert "new_feature" in packet, "intake task_type not embedded"


def test_packet_uses_structured_research_packet_when_present():
    intake = _fixture_intake()
    research_packet = {
        "sources_consulted": ["src/foo.py:10 — STRUCTURED_SOURCE_SENTINEL"],
        "implementation_details": ["IMPL_DETAIL_SENTINEL: use TypedDict total=False"],
    }
    packet = build_gap_analysis_packet(intake, "fallback brief", research_packet)
    assert "STRUCTURED_SOURCE_SENTINEL" in packet
    assert "IMPL_DETAIL_SENTINEL" in packet


# ---- (c) blocking gaps injected into contract packet ----------------------


def test_blocking_gaps_injected_into_contract_packet_under_mandatory():
    contract_packet = build_contract_packet(
        intake=_fixture_intake(),
        research_brief="research brief here",
        gap_analysis=_fixture_gap_analysis(),
    )
    # Header is present.
    assert "MANDATORY ADDITIONAL DELIVERABLES" in contract_packet
    # CONTENT is present (not just the key) — fake-completion guard.
    assert "NEEDS_DB_MIGRATION" in contract_packet
    # Lens label is preserved alongside the gap.
    assert "silent-failure" in contract_packet
    # The mandatory-language reminder is also emitted.
    assert "must also map to at least one deliverable" in contract_packet


# ---- (d) advisory gaps present, not marked mandatory ----------------------


def test_advisory_gaps_under_suggestions_only():
    contract_packet = build_contract_packet(
        intake=_fixture_intake(),
        research_brief="research brief here",
        gap_analysis=_fixture_gap_analysis(),
    )
    assert "SUGGESTIONS" in contract_packet
    assert "ADVISORY_SENTINEL" in contract_packet
    # Advisory content must NOT appear in the MANDATORY block.
    mandatory_start = contract_packet.index("MANDATORY ADDITIONAL DELIVERABLES")
    suggestions_start = contract_packet.index("SUGGESTIONS")
    mandatory_block = contract_packet[mandatory_start:suggestions_start]
    assert "ADVISORY_SENTINEL" not in mandatory_block, (
        "advisory gap leaked into MANDATORY block"
    )


def test_advisory_only_omits_mandatory_header():
    only_advisory = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {"lens": "YAGNI-cut", "gap": "OPTIONAL_ONLY_SENTINEL", "recommendation": "Defer"}
        ],
        "summary": "No blocking issues.",
    }
    contract_packet = build_contract_packet(
        intake=_fixture_intake(),
        research_brief="brief",
        gap_analysis=only_advisory,
    )
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in contract_packet
    assert "SUGGESTIONS" in contract_packet
    assert "OPTIONAL_ONLY_SENTINEL" in contract_packet


# ---- (e) safety: missing gap_analysis must not crash ----------------------


def test_contract_packet_safe_when_gap_analysis_missing():
    packet = build_contract_packet(
        intake=_fixture_intake(),
        research_brief="brief",
        gap_analysis=None,
    )
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet
    assert "SUGGESTIONS" not in packet
    # Primary goal still rendered.
    assert "ACCEPT_SENTINEL_42" in packet


def test_contract_packet_safe_when_gap_analysis_empty_dict():
    packet = build_contract_packet(
        intake=_fixture_intake(),
        research_brief="brief",
        gap_analysis={},
    )
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in packet
    assert "SUGGESTIONS" not in packet
