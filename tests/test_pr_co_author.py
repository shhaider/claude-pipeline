"""Tests for the Co-Authored-By trailer in commit messages and PR bodies."""

from __future__ import annotations

from claude_pipeline.nodes.pr import (
    CO_AUTHOR_TRAILER,
    _build_commit_message,
    _build_pr_body,
)


EXPECTED_TRAILER = "Co-Authored-By: claude-pipeline <noreply@anthropic.com>"


def _sample_state(tmp_path) -> dict:
    return {
        "run_id": "run-abc123",
        "repo": "owner/name",
        "issue_number": 42,
        "issue_title": "Add foo to bar",
        "worktree_path": str(tmp_path),
        "base_branch": "main",
        "feature_branch": "pipeline/issue-42",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 2,
            "right_thing_answer": "yes",
            "risk_flags": [],
        },
        "plan": [{"name": "code", "description": "write the thing"}],
        "code_summary": "Added foo to bar.",
        "verify": {"passed": True, "summary": "all green"},
    }


def test_trailer_constant_is_exact():
    assert CO_AUTHOR_TRAILER == EXPECTED_TRAILER


def test_commit_message_ends_with_co_author_trailer(tmp_path):
    state = _sample_state(tmp_path)
    msg = _build_commit_message(state)

    assert msg.endswith(EXPECTED_TRAILER)
    # Per git trailer convention: blank line between body and trailer block.
    lines = msg.split("\n")
    assert lines[-1] == EXPECTED_TRAILER
    assert lines[-2] == ""
    assert lines[-3] != ""


def test_pr_body_ends_with_co_author_trailer(tmp_path):
    state = _sample_state(tmp_path)
    body = _build_pr_body(state)

    assert EXPECTED_TRAILER in body
    assert body.rstrip("\n").endswith(EXPECTED_TRAILER)
    lines = body.split("\n")
    assert lines[-1] == EXPECTED_TRAILER
    assert lines[-2] == ""
