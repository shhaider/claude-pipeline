import pytest

from claude_pipeline.nodes.pr import _build_commit_message, _build_pr_body

TRAILER = "Co-Authored-By: claude-pipeline <noreply@anthropic.com>"


def test_build_commit_message_includes_co_authored_by_trailer(tmp_path):
    state = {
        "issue_title": "Fix thing",
        "issue_number": 42,
        "run_id": "abc123",
        "repo_dir": tmp_path,
    }
    msg = _build_commit_message(state)
    assert TRAILER in msg
    assert msg.endswith(TRAILER)
    lines = msg.split("\n")
    i = lines.index(TRAILER)
    assert lines[i - 1] == ""


def test_build_pr_body_includes_co_authored_by_trailer(tmp_path):
    state = {
        "issue_title": "Fix thing",
        "issue_number": 42,
        "run_id": "abc123",
        "intake": {},
        "plan": {},
        "verify": {},
        "code_summary": {},
        "repo_dir": tmp_path,
    }
    body = _build_pr_body(state)
    assert TRAILER in body
    assert body.endswith(TRAILER)
    lines = body.split("\n")
    i = lines.index(TRAILER)
    assert lines[i - 1] == ""
