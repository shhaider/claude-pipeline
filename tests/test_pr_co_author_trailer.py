"""Tests for the Co-Authored-By trailer in commits and PR bodies built by pr_node.

These tests only exercise the pure string-construction helpers in
``claude_pipeline.nodes.pr`` — no ``git`` or ``gh`` is invoked.
"""

from __future__ import annotations

from claude_pipeline.nodes.pr import (
    CO_AUTHOR_TRAILER,
    _build_commit_message,
    _build_pr_body,
)

EXPECTED_TRAILER = "Co-Authored-By: claude-pipeline <noreply@anthropic.com>"


def _state() -> dict:
    return {
        "run_id": "run-abc",
        "repo": "shhaider/claude-pipeline",
        "issue_number": 3,
        "issue_title": "Add Co-Authored-By trailer",
        "worktree_path": "/tmp/wt",
        "base_branch": "main",
        "feature_branch": "feat/co-author",
        "code_summary": "Added the trailer everywhere it should be.",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 1,
            "right_thing_answer": "yes",
            "risk_flags": [],
        },
        "plan": [
            {"name": "edit-pr", "description": "Add trailer to commit + body"},
        ],
        "verify": {"passed": True, "summary": "all green"},
    }


def test_trailer_constant_exact_value() -> None:
    assert CO_AUTHOR_TRAILER == EXPECTED_TRAILER


def test_commit_message_ends_with_trailer_after_blank_line(tmp_path) -> None:
    msg = _build_commit_message(_state())

    # Persist via tmp_path so the assertion mirrors what `git commit -m` would write.
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text(msg)
    written = msg_file.read_text()

    assert written.endswith(EXPECTED_TRAILER), written
    # Trailer must be preceded by a blank line, per git trailers convention.
    lines = written.splitlines()
    assert lines[-1] == EXPECTED_TRAILER
    assert lines[-2] == "", f"expected blank line before trailer, got: {lines[-2]!r}"
    # And the line before the blank should be actual body content, not another blank.
    assert lines[-3].strip() != ""


def test_pr_body_ends_with_trailer_line(tmp_path) -> None:
    body = _build_pr_body(_state())

    body_file = tmp_path / "PR_BODY.md"
    body_file.write_text(body)
    written = body_file.read_text()

    lines = written.splitlines()
    assert lines[-1] == EXPECTED_TRAILER, lines[-3:]
    # Trailer should be on its own line, separated from the preceding content.
    assert lines[-2] == "", f"expected blank line before trailer, got: {lines[-2]!r}"


def test_trailer_appears_exactly_once_each() -> None:
    msg = _build_commit_message(_state())
    body = _build_pr_body(_state())

    assert msg.count(EXPECTED_TRAILER) == 1
    assert body.count(EXPECTED_TRAILER) == 1
