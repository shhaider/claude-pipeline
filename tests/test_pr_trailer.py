"""Regression tests locking in the Co-Authored-By trailer in pr.py outputs.

Two surfaces are covered:
- _build_pr_body: the string posted as the PR description
- pr_node: the commit message passed to git commit -m

All subprocess seams are patched so no real git or GitHub CLI is invoked.
"""

from __future__ import annotations

import types

import claude_pipeline.nodes.pr as pr_module
from claude_pipeline.nodes.pr import _build_pr_body

TRAILER = "Co-Authored-By: claude-pipeline <noreply@anthropic.com>"


def _make_state(tmp_path):
    return {
        "issue_title": "Fix the widget",
        "issue_number": 42,
        "run_id": "test-run-001",
        "worktree_path": str(tmp_path),
        "feature_branch": "pipeline/issue-42",
        "repo": "owner/repo",
        "base_branch": "main",
        "intake": {
            "task_type": "bug_fix",
            "complexity_tier": 1,
            "right_thing_answer": "yes",
            "risk_flags": [],
        },
        "verify": {
            "passed": True,
            "summary": "All checks passed.",
        },
        "plan": [
            {"name": "S1", "description": "Implement fix"},
        ],
        "code_summary": "Fixed the widget.",
    }


def test_pr_body_ends_with_coauthor_trailer(tmp_path):
    state = _make_state(tmp_path)
    body = _build_pr_body(state)

    assert TRAILER in body

    non_empty_lines = [line for line in body.splitlines() if line.strip()]
    assert non_empty_lines[-1] == TRAILER

    assert f"\n\n{TRAILER}" in body


def test_commit_message_contains_coauthor_trailer(tmp_path, monkeypatch):
    captured = []

    def fake_git(cwd, *args, check=True):
        captured.append((cwd,) + args)
        if args and args[0] == "status":
            return "M widget.py"
        return ""

    fake_proc = types.SimpleNamespace(
        returncode=0,
        stdout="https://github.com/owner/repo/pull/42\n",
        stderr="",
    )

    def fake_run(cmd, **kwargs):
        return fake_proc

    monkeypatch.setattr(pr_module, "_git", fake_git)
    monkeypatch.setattr(pr_module.subprocess, "run", fake_run)

    state = _make_state(tmp_path)
    pr_module.pr_node(state)

    commit_calls = [
        c for c in captured
        if len(c) >= 4 and c[1] == "commit" and c[2] == "-m"
    ]
    assert commit_calls, "pr_node must invoke _git(..., 'commit', '-m', <msg>)"

    commit_msg = commit_calls[0][3]
    assert TRAILER in commit_msg
    assert f"\n\n{TRAILER}" in commit_msg
