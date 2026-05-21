"""Pure-Python tests for the system_gap_analyst node and its handoff
into the contract node.

No LLM calls — only the deterministic packet builders and helpers are
exercised. The state fixtures are plain dicts.
"""

from __future__ import annotations

import pytest

from claude_pipeline.nodes.contract import (
    ADVISORY_HEADER,
    MANDATORY_HEADER,
    build_contract_packet,
)
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    SYSTEM_PROMPT_PATH,
    build_codebase_anchor,
    build_gap_analysis_packet,
)


# The eight named lenses, in the order the metabuilder port spec calls out.
EXPECTED_LENS_NAMES = [
    "infrastructure-assumed-but-not-mentioned",
    "silent-failure",
    "cross-cutting-concerns",
    "next-stage-prerequisites",
    "YAGNI-cut",
    "fake-completion",
    "architecture-smell",
    "developer-contract-completeness",
]


def _base_state() -> dict:
    return {
        "issue_number": 9,
        "issue_title": "Port system_gap_analyst adversarial pre-lane",
        "worktree_path": "/tmp/worktree-not-used-in-tests",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "scope_plan": "Single PR; one new node + graph wiring + tests.",
            "risk_flags": ["llm_routing"],
            "right_thing_answer": "Yes — gap pass is the next port milestone.",
            "acceptance_criteria": [
                "system_gap_analyst.py exists",
                "graph shows research → system_gap_analyst → contract",
                "tests pass",
            ],
            "wiring_plan": "Adds nodes/system_gap_analyst.py and nodes/contract.py; wires graph.py.",
        },
        "research_brief": (
            "## Current code shape\n"
            "- src/claude_pipeline/graph.py wires intake → research → plan → ...\n"
            "- No contract node exists today.\n"
            "## Touch points\n"
            "- graph.py, state.py, new nodes/system_gap_analyst.py.\n"
        ),
        "research_output": {
            "sources_consulted": [
                "src/claude_pipeline/graph.py:54 — build_graph wiring",
                "src/claude_pipeline/nodes/plan.py:57 — plan_node entrypoint",
            ],
            "implementation_details": [
                "PipelineState is a TypedDict in state.py (total=False)",
                "run_claude(prompt, *, cwd, timeout_s, ...) -> ClaudeResult",
            ],
        },
    }


def _state_with_gaps() -> dict:
    state = _base_state()
    state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "No prompts/ directory exists; 35_system_gap_analyst.md must be created.",
                "recommendation": "Add prompts/metabuilder/35_system_gap_analyst.md as part of this PR.",
            },
            {
                "lens": "developer-contract-completeness",
                "gap": "Acceptance criteria mention 54 v0.3 tests but repo is v0.1.0 with zero tests.",
                "recommendation": "Treat the only test requirement as the new ≥4 gap-analyst tests.",
            },
        ],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "Tier-routing override is mentioned but not enforced at v0.1.0.",
                "recommendation": "Skip tier routing in this PR; track as separate upgrade issue.",
            }
        ],
        "summary": "Framing is mostly complete; two blocking gaps around missing prompt file and test baseline.",
    }
    return state


# ---------------------------------------------------------------------------
# (a) packet contains all 8 lenses
# ---------------------------------------------------------------------------


def test_packet_contains_all_eight_lenses():
    """The gap-analyst user packet must spell out all 8 named lenses verbatim
    so the model can apply each one."""
    packet = build_gap_analysis_packet(_base_state())
    assert len(LENSES) == 8, "module-level LENSES table must have exactly 8 entries"
    for name in EXPECTED_LENS_NAMES:
        assert name in packet, f"lens {name!r} not present in packet"
    # The packet must enumerate the lenses (1. through 8.).
    for i in range(1, 9):
        assert f"{i}." in packet, f"lens enumeration {i}. missing"


# ---------------------------------------------------------------------------
# (b) packet includes intake + research
# ---------------------------------------------------------------------------


def test_packet_includes_intake_and_research():
    """Intake decisions (as JSON) and the research brief must both appear
    in the user packet — they ground the adversarial pass."""
    state = _base_state()
    packet = build_gap_analysis_packet(state)
    # Intake — at least one distinctive field value must appear.
    assert state["intake"]["task_type"] in packet
    assert state["intake"]["scope_plan"] in packet
    assert "complexity_tier" in packet
    # Research brief — verbatim substring.
    assert "Current code shape" in packet
    assert "system_gap_analyst.py" in packet


def test_packet_includes_codebase_anchor_from_research_output():
    """When research_output supplies sources_consulted and
    implementation_details, the codebaseAnchor block must surface them."""
    state = _base_state()
    anchor = build_codebase_anchor(state["research_brief"], state["research_output"])
    assert "codebaseAnchor" in anchor
    assert "Sources consulted" in anchor
    assert "graph.py:54" in anchor
    assert "Implementation details" in anchor
    assert "run_claude" in anchor


def test_codebase_anchor_falls_back_to_research_brief():
    """When no structured research_output is available, the anchor must
    still include the research brief as fallback grounding."""
    anchor = build_codebase_anchor("## Current code shape\n- file.py", None)
    assert "codebaseAnchor" in anchor
    assert "file.py" in anchor


# ---------------------------------------------------------------------------
# (c) blocking gaps get injected into contract input
# ---------------------------------------------------------------------------


def test_blocking_gaps_injected_into_contract_packet_as_mandatory():
    """Every blocking gap from gap_analysis must appear in the contract
    packet under the MANDATORY header, with its lens and gap text."""
    packet = build_contract_packet(_state_with_gaps())
    assert MANDATORY_HEADER in packet
    # Each blocking gap's lens AND text appears in the packet.
    state = _state_with_gaps()
    for item in state["gap_analysis"]["blocking_gaps"]:
        assert item["lens"] in packet
        assert item["gap"] in packet
    # The mandatory framing language must be present.
    assert "MUST appear as a deliverable" in packet
    assert "[MANDATORY]" in packet


def test_contract_packet_no_mandatory_header_when_no_blocking_gaps():
    """If gap_analysis has no blocking gaps, the MANDATORY header must
    NOT appear (otherwise we'd be lying to the model)."""
    state = _base_state()
    state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [],
        "summary": "Framing is complete.",
    }
    packet = build_contract_packet(state)
    assert MANDATORY_HEADER not in packet
    assert ADVISORY_HEADER not in packet


def test_contract_packet_works_without_gap_analysis():
    """If gap_analysis is absent (e.g. earlier node skipped), the contract
    packet must still build cleanly without the gap headers."""
    packet = build_contract_packet(_base_state())
    assert MANDATORY_HEADER not in packet
    assert ADVISORY_HEADER not in packet
    # But intake and research should still be there.
    assert "Intake decisions" in packet
    assert "Research brief" in packet


# ---------------------------------------------------------------------------
# (d) advisory gaps are present but NOT marked mandatory
# ---------------------------------------------------------------------------


def test_advisory_gaps_present_but_not_marked_mandatory():
    """Advisory gaps must appear in the contract packet but under the
    ADVISORY header — they must NOT be labelled MANDATORY."""
    state = _state_with_gaps()
    packet = build_contract_packet(state)

    assert ADVISORY_HEADER in packet
    advisory = state["gap_analysis"]["advisory_gaps"][0]
    assert advisory["gap"] in packet
    assert advisory["lens"] in packet
    assert "[SUGGESTION]" in packet
    # The advisory framing language must call out non-required status.
    assert "not required" in packet

    # Critical separation check: the advisory item's text must appear AFTER
    # the ADVISORY header, NOT after the MANDATORY header. We assert that
    # the advisory's gap-text does not appear above the ADVISORY header,
    # so it cannot be misread as mandatory.
    advisory_header_pos = packet.find(ADVISORY_HEADER)
    advisory_gap_pos = packet.find(advisory["gap"])
    assert advisory_gap_pos > advisory_header_pos, (
        "advisory gap text appeared before the ADVISORY header — could be misread as mandatory"
    )


def test_gap_summary_surfaced_in_contract_packet():
    """The free-text gap summary should appear in the contract packet so the
    model has the analyst's overall read."""
    state = _state_with_gaps()
    packet = build_contract_packet(state)
    assert state["gap_analysis"]["summary"] in packet


# ---------------------------------------------------------------------------
# Sanity: the verbatim role prompt file exists and the node module loads.
# ---------------------------------------------------------------------------


def test_role_prompt_file_exists_and_names_all_lenses():
    """The verbatim role prompt must exist on disk and reference every
    one of the 8 lenses by name."""
    assert SYSTEM_PROMPT_PATH.exists(), f"missing prompt file: {SYSTEM_PROMPT_PATH}"
    body = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    for name in EXPECTED_LENS_NAMES:
        assert name in body, f"role prompt missing lens {name!r}"


def test_node_module_exposes_callable():
    """system_gap_analyst_node must be importable as a node-shaped callable
    (state -> dict)."""
    from claude_pipeline.nodes.system_gap_analyst import system_gap_analyst_node

    assert callable(system_gap_analyst_node)


def test_graph_includes_gap_analyst_between_research_and_contract():
    """The Mermaid render must show the new node between research and
    contract — required by acceptance criteria."""
    from claude_pipeline.graph import render_mermaid

    mermaid = render_mermaid()
    assert "system_gap_analyst" in mermaid
    assert "contract" in mermaid
    # The string 'research --> system_gap_analyst' (Mermaid arrow form)
    # should appear; LangGraph's draw_mermaid uses '-->' for edges.
    assert "research --> system_gap_analyst" in mermaid
    assert "system_gap_analyst --> contract" in mermaid


# ---------------------------------------------------------------------------
# Normalizer: tolerate minor model output drift.
# ---------------------------------------------------------------------------


def test_normalize_gap_analysis_tolerates_alt_keys():
    """The output normalizer should accept `blocking`/`advisory` as
    aliases for `blocking_gaps`/`advisory_gaps`, and drop empty items."""
    from claude_pipeline.nodes.system_gap_analyst import _normalize_gap_analysis

    out = _normalize_gap_analysis(
        {
            "blocking": [
                {"lens": "silent-failure", "gap": "Swallowed exception in retry."},
                {"lens": "silent-failure", "gap": ""},  # empty → dropped
            ],
            "advisory": [
                {"lens": "YAGNI-cut", "gap": "Premature config flag.", "recommendation": "remove"}
            ],
            "summary": "Two minor issues.",
        }
    )
    assert len(out["blocking_gaps"]) == 1
    assert out["blocking_gaps"][0]["lens"] == "silent-failure"
    assert len(out["advisory_gaps"]) == 1
    assert out["advisory_gaps"][0]["recommendation"] == "remove"
    assert out["summary"] == "Two minor issues."


if __name__ == "__main__":  # pragma: no cover - manual exec aid
    pytest.main([__file__, "-v"])
