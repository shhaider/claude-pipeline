"""Pure-python tests for the system_gap_analyst port.

No LLM calls. Tests cover:
  (a) the packet builder includes all 8 lenses
  (b) the packet includes intake + research
  (c) blocking gaps get injected into the plan (contract) node's prompt
      as MANDATORY ADDITIONAL DELIVERABLES
  (d) advisory gaps appear in the plan prompt but are NOT marked mandatory
  (e) parse_gap_analysis_result normalizes ill-shaped model output
  (f) the role prompt file exists at the documented path
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_pipeline.nodes.plan import build_gap_injection_block, build_plan_prompt
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
    parse_gap_analysis_result,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _fixture_state() -> dict:
    """A minimal PipelineState dict with intake + research filled in."""
    return {
        "run_id": "test-run-001",
        "repo": "shhaider/claude-pipeline",
        "issue_number": 9,
        "issue_title": "Port system_gap_analyst",
        "issue_body": "Body of the issue",
        "worktree_path": str(REPO_ROOT),
        "base_branch": "main",
        "feature_branch": "abc-issue-9",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "scope_plan": "Add adversarial gap analysis between research and plan.",
            "risk_flags": ["llm_routing"],
            "right_thing_answer": "Yes — caught by metabuilder port spec.",
            "acceptance_criteria": [
                "system_gap_analyst node exists",
                "graph wires it between research and plan",
                "tests pass",
            ],
            "wiring_plan": "graph.py, state.py, nodes/system_gap_analyst.py",
        },
        "research_brief": (
            "## Current code shape\n\n"
            "graph.py wires intake→research→plan→code→verify→pr. "
            "There is no gap-analysis pass today.\n\n"
            "## Touch points\n\nstate.py PipelineState TypedDict; graph.py build_graph."
        ),
    }


# ---------------------------------------------------------------------------
# (a) packet contains all 8 lenses
# ---------------------------------------------------------------------------

def test_packet_includes_all_eight_named_lenses():
    state = _fixture_state()
    packet = build_gap_analysis_packet(state)
    # Both the constant LENSES and the rendered packet must agree there are 8.
    assert len(LENSES) == 8, "metabuilder spec defines exactly 8 lenses"
    lens_names = [name for name, _ in LENSES]
    for name in lens_names:
        assert name in packet, f"lens '{name}' must appear in the gap-analysis packet"
    # The lens names that must appear per the issue spec, verbatim:
    for required in (
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    ):
        assert required in packet


# ---------------------------------------------------------------------------
# (b) packet includes intake + research
# ---------------------------------------------------------------------------

def test_packet_includes_intake_and_research():
    state = _fixture_state()
    packet = build_gap_analysis_packet(state)
    # Intake decisions surfaced (as JSON values inside the packet):
    assert "new_feature" in packet  # task_type from intake
    assert "Add adversarial gap analysis between research and plan." in packet  # scope_plan
    # Research brief surfaced:
    assert "intake→research→plan→code→verify→pr" in packet
    assert "PipelineState TypedDict" in packet
    # Issue identifier surfaced:
    assert "issue #9" in packet
    # Codebase-anchor section present (per buildGapAnalysisPacket port):
    assert "codebaseAnchor" in packet


def test_packet_codebase_anchor_extracts_structured_research_when_available():
    """When research returns a JSON dict (post-roadmap-item-#3 shape),
    the codebase anchor must pull sources_consulted + implementation_details."""
    state = _fixture_state()
    state["research_brief"] = {
        "evidence_summary": "Found relevant files.",
        "key_findings": ["finding 1"],
        "implementation_details": [
            "PipelineState is a TypedDict in src/claude_pipeline/state.py:43",
        ],
        "gaps_identified": [],
        "confidence": "high",
        "sources_consulted": ["src/claude_pipeline/graph.py:54 — build_graph"],
    }
    packet = build_gap_analysis_packet(state)
    assert "Sources consulted:" in packet
    assert "src/claude_pipeline/graph.py:54 — build_graph" in packet
    assert "Implementation details:" in packet
    assert "PipelineState is a TypedDict" in packet


# ---------------------------------------------------------------------------
# (c) blocking gaps get injected into contract (plan) input as MANDATORY
# ---------------------------------------------------------------------------

def test_blocking_gaps_injected_as_mandatory_into_plan_prompt():
    state = _fixture_state()
    state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "PipelineState has no slot for gap_analysis output.",
                "recommendation": "Add a `gap_analysis: dict` field to PipelineState.",
            },
            {
                "lens": "developer-contract-completeness",
                "gap": "No tests exercise the packet builder.",
                "recommendation": "Add pure-python tests for the packet builder.",
            },
        ],
        "advisory_gaps": [],
        "summary": "Two blocking gaps around state shape and test coverage.",
    }
    prompt = build_plan_prompt(state)
    # Mandatory header present:
    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt
    # Each blocking gap's lens, gap text, and recommendation appear:
    for blocking in state["gap_analysis"]["blocking_gaps"]:
        assert blocking["lens"] in prompt
        assert blocking["gap"] in prompt
        assert blocking["recommendation"] in prompt
    # Mandatory marker for each:
    assert prompt.count("REQUIRED:") == len(state["gap_analysis"]["blocking_gaps"])
    # Summary surfaced:
    assert "Summary: Two blocking gaps" in prompt


# ---------------------------------------------------------------------------
# (d) advisory gaps present but NOT marked mandatory
# ---------------------------------------------------------------------------

def test_advisory_gaps_present_but_not_marked_mandatory():
    state = _fixture_state()
    state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "Mermaid render in graph.py duplicates build_graph wiring.",
                "recommendation": "Consider extracting a shared wire() helper later.",
            }
        ],
        "summary": "One YAGNI consideration, no blockers.",
    }
    prompt = build_plan_prompt(state)
    # Advisory gap text appears...
    assert "Mermaid render in graph.py duplicates build_graph wiring." in prompt
    assert "extracting a shared wire() helper later." in prompt
    # ...but NOT under a mandatory header:
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "REQUIRED:" not in prompt
    # Suggestion header is present instead:
    assert "Suggestions to consider (not mandatory):" in prompt


def test_no_gap_analysis_yields_no_injection_block():
    """When gap_analysis is absent (e.g. resuming a v0.3 checkpoint),
    the plan prompt must build identically to the pre-port version."""
    state = _fixture_state()
    assert "gap_analysis" not in state
    prompt = build_plan_prompt(state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "Suggestions to consider" not in prompt
    assert "ADVERSARIAL GAP ANALYSIS" not in prompt
    # And the base structural pieces are still there:
    assert "INTAKE:" in prompt
    assert "RESEARCH BRIEF:" in prompt
    assert "ISSUE #9: Port system_gap_analyst" in prompt


# ---------------------------------------------------------------------------
# (e) parser tolerates ill-shaped model output
# ---------------------------------------------------------------------------

def test_parse_handles_clean_json():
    text = (
        '{"blocking_gaps": ['
        '{"lens": "silent-failure", "gap": "g", "recommendation": "r"}'
        '], "advisory_gaps": [], "summary": "ok"}'
    )
    out = parse_gap_analysis_result(text)
    assert out["blocking_gaps"] == [
        {"lens": "silent-failure", "gap": "g", "recommendation": "r"}
    ]
    assert out["advisory_gaps"] == []
    assert out["summary"] == "ok"


def test_parse_drops_malformed_gap_entries():
    """Items missing one of {lens, gap, recommendation} get dropped, not crashed on."""
    text = (
        '{"blocking_gaps": ['
        '{"lens": "silent-failure", "gap": "g", "recommendation": "r"},'
        '{"lens": "fake-completion", "gap": "missing-rec"},'
        '"not-a-dict"'
        '], "advisory_gaps": null, "summary": null}'
    )
    out = parse_gap_analysis_result(text)
    assert len(out["blocking_gaps"]) == 1
    assert out["blocking_gaps"][0]["lens"] == "silent-failure"
    assert out["advisory_gaps"] == []
    assert out["summary"] == ""


def test_parse_returns_empty_shape_on_unparseable_text():
    out = parse_gap_analysis_result("this is not JSON at all")
    assert out == {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}


# ---------------------------------------------------------------------------
# (f) role prompt file is on disk where the issue says it is
# ---------------------------------------------------------------------------

def test_role_prompt_file_exists():
    p = REPO_ROOT / "prompts" / "metabuilder" / "35_system_gap_analyst.md"
    assert p.is_file(), f"role prompt must exist at {p}"
    content = p.read_text()
    # The 8 lens names must appear in the role prompt verbatim:
    for required in (
        "infrastructure-assumed-but-not-mentioned",
        "silent-failure",
        "cross-cutting-concerns",
        "next-stage-prerequisites",
        "YAGNI-cut",
        "fake-completion",
        "architecture-smell",
        "developer-contract-completeness",
    ):
        assert required in content


# ---------------------------------------------------------------------------
# Sanity: build_gap_injection_block alone is empty for empty input
# ---------------------------------------------------------------------------

def test_gap_injection_block_empty_when_nothing_to_inject():
    assert build_gap_injection_block(None) == ""
    assert build_gap_injection_block({}) == ""
    assert (
        build_gap_injection_block(
            {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}
        )
        == ""
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
