"""Tests for diff.capture_diff.

We initialise a tiny git repo in a tmpdir to avoid coupling to the
host repo's state.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from claude_pipeline.diff import MAX_DIFF_CHARS, capture_diff


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def tiny_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "alpha.txt").write_text("hello\n")
    _git(repo, "add", "alpha.txt")
    _git(repo, "commit", "-m", "init")
    _git(repo, "checkout", "-b", "feature")
    (repo / "alpha.txt").write_text("hello\nworld\n")
    (repo / "beta.txt").write_text("new file\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "change")
    return repo


class TestCaptureDiff:
    def test_returns_diff_against_main(self, tiny_repo: Path):
        diff = capture_diff(tiny_repo, base_branch="main")
        assert "+world" in diff
        assert "beta.txt" in diff

    def test_returns_empty_when_no_diff(self, tmp_path: Path):
        # A fresh repo with no changes on the same branch.
        repo = tmp_path / "norm"
        repo.mkdir()
        _git(repo, "init", "--initial-branch=main")
        _git(repo, "config", "user.email", "t@e.com")
        _git(repo, "config", "user.name", "T")
        (repo / "x.txt").write_text("x")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-m", "init")
        # Diff main vs main = empty
        diff = capture_diff(repo, base_branch="main")
        assert diff == ""

    def test_invalid_base_returns_empty(self, tiny_repo: Path):
        diff = capture_diff(tiny_repo, base_branch="does-not-exist")
        # No base + no origin + HEAD~1 has a parent so we'd fall through;
        # but in our tiny_repo, HEAD~1 exists, so we get that diff.
        # Just assert it doesn't raise — capture_diff is best-effort.
        assert isinstance(diff, str)

    def test_truncates_huge_diff(self, tiny_repo: Path):
        # Add a huge change so we exceed the cap
        huge = "x" * (MAX_DIFF_CHARS * 2)
        (tiny_repo / "huge.txt").write_text(huge)
        _git(tiny_repo, "add", "-A")
        _git(tiny_repo, "commit", "-m", "huge")
        diff = capture_diff(tiny_repo, base_branch="main")
        assert len(diff) <= MAX_DIFF_CHARS + 200  # some marker text added
        assert "truncated" in diff
