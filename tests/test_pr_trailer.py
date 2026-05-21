"""Unit tests for the Co-Authored-By trailer in commit messages and PR bodies."""

from __future__ import annotations

from claude_pipeline.nodes.pr import (
    _COAUTHOR_TRAILER,
    _build_commit_message,
    _build_pr_body,
)


def _minimal_state() -> dict:
    return {
        "issue_number": 42,
        "issue_title": "Add coauthor trailer",
        "run_id": "run-abc-123",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 1,
            "right_thing_answer": "yes",
            "risk_flags": [],
        },
        "plan": [
            {"name": "stage-one", "description": "do the thing"},
        ],
        "code_summary": "Made the change.",
        "verify": {"passed": True, "summary": "all good"},
    }


def test_commit_message_has_trailer(tmp_path):
    state = _minimal_state()
    msg = _build_commit_message(state)

    assert _COAUTHOR_TRAILER in msg
    lines = msg.splitlines()
    assert lines[-1] == _COAUTHOR_TRAILER
    # The trailer must be preceded by exactly one blank line separating it from the body.
    assert lines[-2] == ""
    assert lines[-3] != ""


def test_pr_body_ends_with_trailer(tmp_path):
    state = _minimal_state()
    body = _build_pr_body(state)

    assert _COAUTHOR_TRAILER in body
    assert body.splitlines()[-1] == _COAUTHOR_TRAILER
