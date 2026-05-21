"""Behavioural tests for the system_gap_analyst node and its plan_node integration.

Tests run without the Claude CLI — all LLM calls are monkeypatched.
"""
from __future__ import annotations

import json

import pytest

import claude_pipeline.nodes.plan as plan_mod
import claude_pipeline.nodes.system_gap_analyst as sga_mod
from claude_pipeline.claude import ClaudeResult

# All 8 verbatim adversarial lens strings — asserted in tests and grep-counted by CI.
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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _stub_result(text: str) -> ClaudeResult:
    return ClaudeResult(
        text=text,
        session_id="stub",
        duration_s=0.0,
        cost_usd=0.0,
        num_turns=1,
        is_error=False,
    )


def _gap_json(blocking=None, advisory=None, summary="stub") -> str:
    return json.dumps(
        {"blocking_gaps": blocking or [], "advisory_gaps": advisory or [], "summary": summary}
    )


def _stage_json() -> str:
    return json.dumps(
        [{"name": "stub-stage", "description": "stub", "file_touch_map": ["stub.py"]}]
    )


@pytest.fixture
def base_sga_state():
    """Minimal state that exercises all packet fields in system_gap_analyst_node."""
    return {
        "intake": {"task_type": "new_feature", "scope_plan": "ScopeTokenXYZ"},
        "research_brief": "ResearchTokenABC: JWT library required",
        "issue_number": 42,
        "issue_title": "Add login",
    }


@pytest.fixture
def base_plan_state():
    """Minimal state that satisfies plan_node's required keys."""
    return {
        "intake": {},
        "research_brief": "(none)",
        "issue_number": 1,
        "issue_title": "test",
        "worktree_path": "/tmp",
    }


# ---------------------------------------------------------------------------
# Test (a) — all 8 lenses appear verbatim in the user packet sent to Claude
# ---------------------------------------------------------------------------


def test_all_lenses_in_user_packet(monkeypatch, base_sga_state):
    captured: list[str] = []

    def fake_run_claude(prompt, **kwargs):
        captured.append(prompt)
        return _stub_result(_gap_json())

    monkeypatch.setattr(sga_mod, "run_claude", fake_run_claude)

    result = sga_mod.system_gap_analyst_node(base_sga_state)

    assert captured, "run_claude was never called — node short-circuited unexpectedly"
    packet = captured[0]
    for lens in LENSES:
        assert lens in packet, f"lens '{lens}' missing from user packet"

    assert result.get("error") is None, f"node returned error: {result.get('error')}"


# ---------------------------------------------------------------------------
# Test (b) — intake and research_brief are threaded into the user packet
# ---------------------------------------------------------------------------


def test_intake_and_research_in_packet(monkeypatch, base_sga_state):
    captured: list[str] = []

    def fake_run_claude(prompt, **kwargs):
        captured.append(prompt)
        return _stub_result(_gap_json())

    monkeypatch.setattr(sga_mod, "run_claude", fake_run_claude)

    sga_mod.system_gap_analyst_node(base_sga_state)

    assert captured, "run_claude was never called"
    packet = captured[0]
    # Distinctive token from intake.scope_plan
    assert "ScopeTokenXYZ" in packet, "intake content not found in user packet"
    # Distinctive token from research_brief
    assert "ResearchTokenABC" in packet, "research_brief not found in user packet"


# ---------------------------------------------------------------------------
# Test (c) — blocking gaps inject into plan prompt as MANDATORY ADDITIONAL DELIVERABLES
# ---------------------------------------------------------------------------


def test_blocking_gaps_inject_as_mandatory(monkeypatch, base_plan_state):
    captured: list[str] = []

    def fake_run_claude(prompt, **kwargs):
        captured.append(prompt)
        return _stub_result(_stage_json())

    monkeypatch.setattr(plan_mod, "run_claude", fake_run_claude)

    base_plan_state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "fake-completion",
                "description": "BlockingGap42Desc",
                "recommendation": "Fix the contract immediately",
            }
        ],
        "advisory_gaps": [],
        "summary": "test",
    }

    plan_mod.plan_node(base_plan_state)

    assert captured, "run_claude was never called"
    prompt = captured[0]
    assert "BlockingGap42Desc" in prompt, "blocking gap description absent from plan prompt"
    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt, (
        "MANDATORY ADDITIONAL DELIVERABLES heading missing from plan prompt"
    )


# ---------------------------------------------------------------------------
# Test (d) — advisory gaps appear in plan prompt but are NOT marked mandatory
# ---------------------------------------------------------------------------


def test_advisory_gaps_not_marked_mandatory(monkeypatch, base_plan_state):
    captured: list[str] = []

    def fake_run_claude(prompt, **kwargs):
        captured.append(prompt)
        return _stub_result(_stage_json())

    monkeypatch.setattr(plan_mod, "run_claude", fake_run_claude)

    base_plan_state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "description": "AdvisoryGap99Desc",
                "recommendation": "Consider removing speculative scope",
            }
        ],
        "summary": "test",
    }

    plan_mod.plan_node(base_plan_state)

    assert captured, "run_claude was never called"
    prompt = captured[0]
    assert "AdvisoryGap99Desc" in prompt, "advisory gap description absent from plan prompt"
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt, (
        "MANDATORY ADDITIONAL DELIVERABLES must NOT appear when only advisory gaps are present"
    )
