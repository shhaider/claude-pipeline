"""Tests for system_gap_analyst packet builder and contract gap injection.

All tests are pure-Python and offline — no live LLM calls are made.
"""

from __future__ import annotations

import types

import pytest

from claude_pipeline.nodes.contract import build_contract_packet
from claude_pipeline.nodes.system_gap_analyst import (
    build_gap_analysis_packet,
    system_gap_analyst_node,
)


@pytest.fixture
def base_state():
    return {
        "repo": "owner/repo",
        "issue_number": 1,
        "issue_title": "Test issue",
        "issue_body": "Test body",
        "worktree_path": "/tmp/fake_worktree",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 2,
            "scope_plan": "single task",
            "right_thing_answer": "yes",
            "risk_flags": [],
            "wiring_plan": "some modules",
            "acceptance_criteria": ["criterion 1"],
        },
        "research_brief": "Test research brief content.",
    }


def test_gap_packet_contains_all_8_lenses(base_state):
    """Packet must enumerate all 8 adversarial lenses verbatim."""
    packet = build_gap_analysis_packet(base_state)
    all_8_lenses = [  # all 8 lenses
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    ]
    for lens in all_8_lenses:
        assert lens in packet, f"Lens '{lens}' missing from gap analysis packet"


def test_gap_packet_includes_intake_and_research(base_state):
    """Packet must embed upstream intake decisions and research brief."""
    base_state["intake"]["task_type"] = "INTAKE_SENTINEL_xyz"
    base_state["research_brief"] = "RESEARCH_SENTINEL_xyz"
    packet = build_gap_analysis_packet(base_state)
    assert "INTAKE_SENTINEL_xyz" in packet, "Intake data not embedded in gap analysis packet"
    assert "RESEARCH_SENTINEL_xyz" in packet, "Research brief not embedded in gap analysis packet"


def test_blocking_gaps_injected_as_mandatory_in_contract_packet(base_state):
    """blocking_gaps must appear under the MANDATORY ADDITIONAL DELIVERABLES header."""
    base_state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "silent-failure",
                "gap": "BLOCKING_SENTINEL_abc",
                "recommendation": "fix it",
            }
        ],
        "advisory_gaps": [],
        "summary": "one blocking gap found",
    }
    packet = build_contract_packet(base_state)
    assert "BLOCKING_SENTINEL_abc" in packet
    assert "MANDATORY ADDITIONAL DELIVERABLES" in packet
    mandatory_idx = packet.index("MANDATORY ADDITIONAL DELIVERABLES")
    sentinel_idx = packet.index("BLOCKING_SENTINEL_abc")
    assert sentinel_idx > mandatory_idx, (
        "Blocking gap sentinel must appear after the MANDATORY ADDITIONAL DELIVERABLES header"
    )


def test_advisory_gaps_present_but_not_mandatory(base_state):
    """advisory_gaps must be present in the packet but outside the mandatory block."""
    base_state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "ADVISORY_SENTINEL_def",
                "recommendation": "consider removing",
            }
        ],
        "summary": "one advisory gap found",
    }
    packet = build_contract_packet(base_state)
    assert "ADVISORY_SENTINEL_def" in packet
    # Advisory content must appear after the "Advisory suggestions" section header.
    advisory_section_idx = packet.index("Advisory suggestions")
    sentinel_idx = packet.index("ADVISORY_SENTINEL_def")
    assert sentinel_idx > advisory_section_idx, (
        "Advisory gap sentinel must appear after the Advisory suggestions header"
    )
    # Advisory sentinel must NOT be present in the text before the advisory section.
    mandatory_block = packet[:advisory_section_idx]
    assert "ADVISORY_SENTINEL_def" not in mandatory_block, (
        "Advisory gap must not appear inside the mandatory block"
    )


def test_system_gap_analyst_node_returns_gap_analysis_slice(base_state, monkeypatch):
    """Node must return {'gap_analysis': {...}, 'error': None} on a successful run."""
    stub_text = '{"blocking_gaps": [], "advisory_gaps": [], "summary": "ok"}'
    stub_result = types.SimpleNamespace(
        text=stub_text,
        is_error=False,
        duration_s=0.1,
        cost_usd=0.0,
        num_turns=1,
    )

    import claude_pipeline.nodes.system_gap_analyst as sga_mod

    monkeypatch.setattr(sga_mod, "run_claude", lambda *a, **kw: stub_result)

    result = system_gap_analyst_node(base_state)

    assert "gap_analysis" in result
    assert result["error"] is None
    assert result["gap_analysis"]["blocking_gaps"] == []
    assert result["gap_analysis"]["advisory_gaps"] == []
    assert result["gap_analysis"]["summary"] == "ok"
