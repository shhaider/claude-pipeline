"""Behavioural tests for the system_gap_analyst node and its plan-prompt
injection. All LLM calls are monkeypatched — no subprocess invocations,
no Claude CLI required."""

from __future__ import annotations

import json

import pytest

import claude_pipeline.nodes.plan as plan_mod
import claude_pipeline.nodes.system_gap_analyst as sga_mod
from claude_pipeline.claude import ClaudeResult

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


def _stub_result(text: str) -> ClaudeResult:
    return ClaudeResult(
        text=text,
        session_id="stub",
        duration_s=0.0,
        cost_usd=0.0,
        num_turns=1,
        is_error=False,
    )


def _gap_json(blocking=None, advisory=None, summary="stub"):
    return json.dumps(
        {
            "blocking_gaps": blocking or [],
            "advisory_gaps": advisory or [],
            "summary": summary,
        }
    )


def _stage_json():
    return json.dumps(
        [
            {
                "name": "stub-stage",
                "description": "stub",
                "file_touch_map": ["stub.py"],
            }
        ]
    )


@pytest.fixture
def base_sga_state():
    return {
        "intake": {"task_type": "new_feature", "scope_plan": "ScopeTokenXYZ"},
        "research_brief": "ResearchTokenABC: JWT library required",
        "issue_number": 42,
        "issue_title": "Add login",
        "repo": "fake/repo",
        "worktree_path": "/tmp",
    }


@pytest.fixture
def base_plan_state():
    return {
        "intake": {},
        "research_brief": "(none)",
        "issue_number": 1,
        "issue_title": "test",
        "worktree_path": "/tmp",
    }


def test_all_lenses_in_user_packet(monkeypatch, base_sga_state):
    """AC §4(a): all 8 lens strings appear verbatim in the user packet
    passed to run_claude."""
    captured = {}

    def fake_run_claude(prompt, **kwargs):
        captured["prompt"] = prompt
        captured["kwargs"] = kwargs
        return _stub_result(_gap_json())

    monkeypatch.setattr(sga_mod, "run_claude", fake_run_claude)

    out = sga_mod.system_gap_analyst_node(base_sga_state)
    assert "error" not in out or out["error"] is None
    prompt = captured["prompt"]
    for lens in LENSES:
        assert lens in prompt, f"missing lens in user packet: {lens}"


def test_intake_and_research_in_packet(monkeypatch, base_sga_state):
    """AC §4(b): intake.scope_plan and research_brief sentinels land in
    the captured user packet. Returned state slice contains gap_analysis."""
    captured = {}

    def fake_run_claude(prompt, **kwargs):
        captured["prompt"] = prompt
        return _stub_result(
            _gap_json(
                blocking=[
                    {
                        "lens": "silent-failure",
                        "gap": "no error path",
                        "recommendation": "wrap caller",
                    }
                ],
                summary="ok",
            )
        )

    monkeypatch.setattr(sga_mod, "run_claude", fake_run_claude)

    out = sga_mod.system_gap_analyst_node(base_sga_state)
    prompt = captured["prompt"]
    assert "ScopeTokenXYZ" in prompt
    assert "ResearchTokenABC" in prompt
    assert "gap_analysis" in out
    assert out["gap_analysis"]["blocking_gaps"][0]["gap"] == "no error path"
    assert out["gap_analysis"]["summary"] == "ok"


def test_blocking_gaps_inject_as_mandatory(monkeypatch, base_plan_state):
    """AC §4(c): when gap_analysis.blocking_gaps is populated, the
    captured plan_node prompt contains the literal string MANDATORY
    ADDITIONAL DELIVERABLES AND the distinctive gap description."""
    captured = {}

    def fake_run_claude(prompt, **kwargs):
        captured["prompt"] = prompt
        return _stub_result(_stage_json())

    monkeypatch.setattr(plan_mod, "run_claude", fake_run_claude)

    state = dict(base_plan_state)
    state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "MissingRedisQueueSentinel",
                "recommendation": "Provision Redis",
            }
        ],
        "advisory_gaps": [],
        "summary": "one blocking",
    }

    out = plan_mod.plan_node(state)
    assert out.get("error") is None, out
    prompt = captured["prompt"]
    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt
    assert "MissingRedisQueueSentinel" in prompt


def test_advisory_gaps_not_marked_mandatory(monkeypatch, base_plan_state):
    """AC §4(d): when only advisory_gaps is populated, the prompt
    contains the advisory description but does NOT contain the
    substring MANDATORY ADDITIONAL DELIVERABLES."""
    captured = {}

    def fake_run_claude(prompt, **kwargs):
        captured["prompt"] = prompt
        return _stub_result(_stage_json())

    monkeypatch.setattr(plan_mod, "run_claude", fake_run_claude)

    state = dict(base_plan_state)
    state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "YAGNI-cut",
                "gap": "AdvisoryTokenLMN: speculative feature",
                "recommendation": "drop it",
            }
        ],
        "summary": "advisory only",
    }

    out = plan_mod.plan_node(state)
    assert out.get("error") is None, out
    prompt = captured["prompt"]
    assert "AdvisoryTokenLMN" in prompt
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "ADVISORY SUGGESTIONS" in prompt
