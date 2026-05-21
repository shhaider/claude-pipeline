"""Tests for the system_gap_analyst pre-lane.

Pure-Python — no LLM calls. We exercise:
  - the user packet builder (`build_gap_analysis_packet`) on a fixture state,
  - the gap-injection helper used by the contract_writer side (`build_plan_prompt`
    + `build_gap_injection_block`),
  - the node's output coercion when given a fake LLM response (by patching
    `run_claude` to return canned text).
"""

from __future__ import annotations

import json

import pytest

from claude_pipeline.nodes import plan as plan_module
from claude_pipeline.nodes import system_gap_analyst as sga_module
from claude_pipeline.nodes.plan import build_gap_injection_block, build_plan_prompt
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
    system_gap_analyst_node,
)


# --- fixtures ---------------------------------------------------------------


@pytest.fixture
def base_state() -> dict:
    """A representative PipelineState dict after intake + research have run,
    but BEFORE the gap analyst (so `gap_analysis` is absent)."""
    return {
        "run_id": "run-abc",
        "repo": "shhaider/claude-pipeline",
        "issue_number": 9,
        "issue_title": "Port system_gap_analyst adversarial pre-lane",
        "issue_body": "see metabuilder port spec",
        "worktree_path": "/tmp/wt",
        "base_branch": "main",
        "feature_branch": "issue-9",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "scope_plan": "Add a new node between research and contract.",
            "risk_flags": ["llm_routing", "api_contract"],
            "right_thing_answer": "Yes — porting metabuilder faithfully.",
            "acceptance_criteria": [
                "Node file exists",
                "Graph topology includes new edge",
                "Blocking gaps appear in plan packet",
            ],
            "wiring_plan": "Touches state.py, graph.py, plan.py, nodes/",
        },
        "research_brief": (
            "The pipeline is currently intake→research→plan→code→verify→pr. "
            "The plan node currently fills the contract_writer role. "
            "Conventions: snake_case, TypedDict state, run_claude wrapper."
        ),
    }


@pytest.fixture
def gap_analysis() -> dict:
    return {
        "blocking_gaps": [
            {
                "lens": "silent-failure",
                "gap": "extract_json swallows everything that's not balanced JSON.",
                "recommendation": "Surface a structured error and route to retry.",
            },
            {
                "lens": "developer-contract-completeness",
                "gap": "Test directory layout is not yet documented.",
                "recommendation": "Add tests/__init__.py and a section to README.",
            },
        ],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "Per-lens token-budget tracking is out of scope for MVP.",
                "recommendation": "Defer to a follow-up issue if cost spikes.",
            },
        ],
        "summary": "Framing is solid; two blocking gaps around error handling and docs.",
    }


# --- (a) packet contains all 8 lenses ---------------------------------------


def test_packet_contains_all_eight_lenses(base_state):
    """The user packet must spell out every one of the 8 metabuilder lenses
    by name — the model cannot skip a lens that's been named."""
    packet = build_gap_analysis_packet(base_state)

    expected_lens_names = {name for name, _desc in LENSES}
    assert len(expected_lens_names) == 8, "LENSES constant must define 8 entries"

    for lens_name in expected_lens_names:
        assert lens_name in packet, f"packet is missing lens {lens_name!r}"


# --- (b) packet includes intake + research ----------------------------------


def test_packet_includes_intake_and_research(base_state):
    """The packet must include intake decisions and the research brief
    verbatim — the gap analyst needs both to find gaps."""
    packet = build_gap_analysis_packet(base_state)

    # Intake fields surface (both in the structured JSON block and as bullets).
    intake = base_state["intake"]
    assert intake["task_type"] in packet
    assert intake["scope_plan"] in packet
    assert intake["wiring_plan"] in packet
    for criterion in intake["acceptance_criteria"]:
        assert criterion in packet, f"acceptance criterion {criterion!r} missing"
    for risk in intake["risk_flags"]:
        assert risk in packet, f"risk flag {risk!r} missing"

    # Research brief appears.
    assert base_state["research_brief"] in packet

    # codebaseAnchor block is present.
    assert "codebaseAnchor" in packet


# --- (c) blocking gaps get injected as MANDATORY ----------------------------


def test_blocking_gaps_injected_as_mandatory(base_state, gap_analysis):
    """When gap_analysis is in state, the plan-node prompt must inject each
    blocking gap under a MANDATORY ADDITIONAL DELIVERABLES header so the
    planner treats them as required, not optional."""
    base_state["gap_analysis"] = gap_analysis
    prompt = build_plan_prompt(base_state)

    # The header that downstream verifiers grep for.
    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt

    # Each blocking gap (lens + text + recommendation) appears.
    for g in gap_analysis["blocking_gaps"]:
        assert g["lens"] in prompt
        assert g["gap"] in prompt
        assert g["recommendation"] in prompt


# --- (d) advisory gaps present but NOT marked mandatory ---------------------


def test_advisory_gaps_are_suggestions_not_mandatory(base_state, gap_analysis):
    """Advisory gaps appear in the prompt under a non-mandatory header. They
    must NOT be co-located with the MANDATORY label."""
    base_state["gap_analysis"] = gap_analysis
    prompt = build_plan_prompt(base_state)

    advisory_header = "Advisory suggestions (not mandatory)"
    assert advisory_header in prompt

    mandatory_idx = prompt.index("MANDATORY ADDITIONAL DELIVERABLES")
    advisory_idx = prompt.index(advisory_header)
    assert advisory_idx > mandatory_idx, "advisory block must follow mandatory block"

    for g in gap_analysis["advisory_gaps"]:
        # Body of the advisory gap appears.
        assert g["gap"] in prompt
        assert g["recommendation"] in prompt

        # The advisory gap's text lives below the advisory header (NOT in
        # the mandatory section).
        gap_idx = prompt.index(g["gap"])
        assert gap_idx > advisory_idx


# --- (e) absent gap_analysis is a no-op -------------------------------------


def test_no_gap_analysis_means_no_injection(base_state):
    """If `gap_analysis` is absent from state, the plan prompt must NOT
    contain the mandatory / advisory headers — the planner runs as it did
    before this upgrade."""
    assert "gap_analysis" not in base_state
    prompt = build_plan_prompt(base_state)

    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "Advisory suggestions" not in prompt
    assert "ADVERSARIAL GAP ANALYSIS" not in prompt


# --- (f) injection helper is empty for empty/None gap_analysis --------------


def test_gap_injection_block_empty_inputs():
    """The injection helper returns an empty string for None / {} so callers
    can concatenate it unconditionally."""
    assert build_gap_injection_block(None) == ""
    assert build_gap_injection_block({}) == ""
    assert (
        build_gap_injection_block(
            {"blocking_gaps": [], "advisory_gaps": [], "summary": ""}
        )
        == ""
    )


# --- (g) node coerces a canned LLM response into the documented schema -----


class _StubResult:
    def __init__(self, text: str) -> None:
        self.text = text
        self.session_id = "sid"
        self.duration_s = 0.1
        self.cost_usd = 0.0
        self.num_turns = 1
        self.usage = {}
        self.is_error = False
        self.stop_reason = "end_turn"


def test_node_parses_canned_llm_output_into_state_slice(
    base_state, gap_analysis, monkeypatch
):
    """The node, given a well-formed LLM JSON response, must return a state
    slice with the documented `blocking_gaps`/`advisory_gaps`/`summary` keys
    populated correctly. This exercises the coercion path without an LLM."""

    canned = json.dumps(gap_analysis)

    def fake_run_claude(prompt, **kwargs):  # noqa: ARG001 - signature match
        # Sanity: the role prompt must reach the CLI via --append-system-prompt.
        extra = list(kwargs.get("extra_args") or [])
        assert "--append-system-prompt" in extra
        assert kwargs.get("model") == "claude-opus-4-7"
        return _StubResult(canned)

    monkeypatch.setattr(sga_module, "run_claude", fake_run_claude)

    slice_out = system_gap_analyst_node(base_state)

    assert slice_out["error"] is None
    ga = slice_out["gap_analysis"]
    assert [g["lens"] for g in ga["blocking_gaps"]] == [
        g["lens"] for g in gap_analysis["blocking_gaps"]
    ]
    assert [g["lens"] for g in ga["advisory_gaps"]] == [
        g["lens"] for g in gap_analysis["advisory_gaps"]
    ]
    assert ga["summary"] == gap_analysis["summary"]


def test_node_survives_unparseable_llm_output(base_state, monkeypatch):
    """If the LLM returns garbage, the node must not crash the pipeline. It
    returns an empty gap_analysis and an error marker so downstream nodes
    can proceed (and the run is still observable)."""

    def fake_run_claude(prompt, **kwargs):  # noqa: ARG001
        return _StubResult("this is not json and there is no brace")

    monkeypatch.setattr(sga_module, "run_claude", fake_run_claude)

    slice_out = system_gap_analyst_node(base_state)

    assert slice_out["gap_analysis"] == {
        "blocking_gaps": [],
        "advisory_gaps": [],
        "summary": "(gap analysis parse failed — proceeding without it)",
    }
    assert slice_out["error"] and "parse failed" in slice_out["error"]
