"""Pure-python tests for the system_gap_analyst node.

No LLM calls — tests exercise the packet builder and the
gap-injection into the plan node's prompt using fixture state dicts.
"""

from __future__ import annotations

import pytest

from claude_pipeline.nodes.plan import _format_gap_analysis_block, build_plan_prompt
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
)


# ---------- fixtures ----------


@pytest.fixture
def intake_decisions() -> dict:
    return {
        "task_type": "new_feature",
        "complexity_tier": 2,
        "scope_plan": "Add a fault-injection harness with a CLI flag.",
        "risk_flags": ["concurrency"],
        "right_thing_answer": "Yes — fault injection is the right next step.",
        "acceptance_criteria": [
            "harness can inject errors at named injection points",
            "CLI flag --inject toggles the harness",
            "existing tests still pass",
        ],
        "wiring_plan": "Touches cli.py and a new harness module.",
    }


@pytest.fixture
def research_brief() -> str:
    return (
        "## Current code shape\n"
        "- cli.py uses argparse, no plugin system.\n"
        "- nodes/*.py each shell out to claude --print.\n"
        "## Touch points\n"
        "- cli.py needs a new flag.\n"
        "## Recommended approach\n"
        "Add a thin harness module; wire it from cli.py.\n"
    )


@pytest.fixture
def base_state(intake_decisions, research_brief) -> dict:
    return {
        "repo": "shhaider/claude-pipeline",
        "issue_number": 42,
        "issue_title": "Add fault injection harness",
        "issue_body": "We need a fault-injection harness for soak tests.",
        "intake": intake_decisions,
        "research_brief": research_brief,
    }


@pytest.fixture
def gap_analysis() -> dict:
    return {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "Issue assumes an injection-point registry exists; it does not.",
                "recommendation": "Add a registry module mapping names → callable hooks.",
            },
            {
                "lens": "developer-contract-completeness",
                "gap": "No invariants stated for what 'injection enabled' means at runtime.",
                "recommendation": "Define a developer contract for harness state transitions.",
            },
        ],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "Cross-process fault injection is not in scope.",
                "recommendation": "Defer to a follow-up issue.",
            },
        ],
        "summary": "The framing omits the registry and the developer contract.",
    }


# ---------- packet builder ----------


def test_packet_contains_all_8_lenses(base_state):
    """(a) packet contains all 8 lenses, in order, spelled out."""
    packet = build_gap_analysis_packet(base_state)
    expected_names = [
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    ]
    # The module's LENSES table must match the issue's contract exactly.
    assert [name for name, _ in LENSES] == expected_names
    # Each lens must appear in the rendered packet.
    for name in expected_names:
        assert name in packet, f"lens {name!r} missing from packet"
    # Lenses must be numbered 1..8 in the body.
    for i in range(1, 9):
        assert f"Lens {i} —" in packet, f"Lens {i} header missing"


def test_packet_includes_intake_and_research(base_state):
    """(b) packet includes intake decisions and the research brief."""
    packet = build_gap_analysis_packet(base_state)

    # Intake values surface (we render via json.dumps; check key snippets).
    assert "new_feature" in packet
    assert "fault-injection harness" in packet
    assert "concurrency" in packet
    assert "harness can inject errors at named injection points" in packet

    # Research brief surfaces verbatim under both the brief heading and
    # the codebaseAnchor heading (anchor is built from the brief).
    assert "## Touch points" in packet
    assert "Recommended approach" in packet
    assert "### codebaseAnchor" in packet
    assert "### Research brief" in packet

    # Output schema is present.
    assert "blocking_gaps" in packet
    assert "advisory_gaps" in packet
    assert '"summary"' in packet


def test_packet_handles_empty_research(intake_decisions):
    """Packet must still render when no research brief was produced —
    gap analyst is expected to flag the absence in that case."""
    state = {
        "repo": "x/y",
        "issue_number": 1,
        "issue_title": "t",
        "issue_body": "b",
        "intake": intake_decisions,
        "research_brief": "",
    }
    packet = build_gap_analysis_packet(state)
    # Must mention that no brief was produced so the model can flag it.
    assert "no research brief" in packet.lower()


# ---------- gap injection into plan prompt ----------


def test_blocking_gaps_injected_as_mandatory_deliverables(base_state, gap_analysis):
    """(c) blocking gaps get injected into contract/plan input as
    MANDATORY ADDITIONAL DELIVERABLES."""
    state = {**base_state, "gap_analysis": gap_analysis}
    prompt = build_plan_prompt(state)

    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt
    # Each blocking gap's text and lens should appear.
    for gap in gap_analysis["blocking_gaps"]:
        assert gap["gap"] in prompt
        assert gap["lens"] in prompt
        assert gap["recommendation"] in prompt
    # The summary should surface too.
    assert gap_analysis["summary"] in prompt
    # And the plan rules must reference the mandatory-deliverable contract.
    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt
    assert "MUST be covered by some stage" in prompt


def test_advisory_gaps_present_but_not_mandatory(base_state, gap_analysis):
    """(d) advisory gaps are present in the prompt but marked as
    SUGGESTIONS, not mandatory."""
    state = {**base_state, "gap_analysis": gap_analysis}
    prompt = build_plan_prompt(state)

    assert "SUGGESTIONS" in prompt
    advisory_gap = gap_analysis["advisory_gaps"][0]
    assert advisory_gap["gap"] in prompt
    assert advisory_gap["recommendation"] in prompt
    # Advisory gap must NOT be under the MANDATORY block. Use the
    # SUGGESTIONS header as the cut-point: everything advisory comes after it.
    mandatory_idx = prompt.find("MANDATORY ADDITIONAL DELIVERABLES")
    suggestions_idx = prompt.find("SUGGESTIONS")
    advisory_text_idx = prompt.find(advisory_gap["gap"])
    assert mandatory_idx >= 0 and suggestions_idx >= 0
    assert advisory_text_idx > suggestions_idx, (
        "advisory gap appeared in or before the MANDATORY block"
    )

    # Blocking gaps must NOT appear in the suggestions section.
    blocking_in_suggestions = prompt[suggestions_idx:].find(
        gap_analysis["blocking_gaps"][0]["gap"]
    )
    assert blocking_in_suggestions == -1, (
        "blocking gap leaked into the SUGGESTIONS section"
    )


def test_plan_prompt_without_gap_analysis_omits_block(base_state):
    """When no gap_analysis is present (e.g. resumed older run),
    the plan prompt must not reference mandatory-deliverables or
    suggestions at all."""
    prompt = build_plan_prompt(base_state)  # no gap_analysis key
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "SUGGESTIONS" not in prompt
    assert "GAP ANALYSIS SUMMARY" not in prompt


def test_format_gap_block_empty_inputs():
    """The renderer is defensive against missing or partial inputs."""
    assert _format_gap_analysis_block(None) == ""
    assert _format_gap_analysis_block({}) == ""
    # Summary-only is allowed.
    only_summary = _format_gap_analysis_block({"summary": "nothing to flag"})
    assert "GAP ANALYSIS SUMMARY" in only_summary
    assert "MANDATORY" not in only_summary
    assert "SUGGESTIONS" not in only_summary
