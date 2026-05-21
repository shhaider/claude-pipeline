"""Tests for the ABC harness metric extractors.

Tests use small synthetic worktrees built per-fixture and log fixtures
defined inline. We exercise each extractor in isolation, then the
composed ``score_variant_run``.

No subprocess shell-outs to ``claude`` or ``gh`` here — that's not what
this module tests. The harness driver (abc_harness.py) is the boundary
that calls those.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from claude_pipeline.abc_scoring import (
    count_exported_funcs,
    detect_failure_categories,
    diff_stats,
    extract_gate_verdict,
    extract_pr_url,
    extract_test_counts,
    score_variant_run,
)


# --------------------------------------------------------------------------- #
# extract_pr_url
# --------------------------------------------------------------------------- #


def test_extract_pr_url_basic() -> None:
    text = "opened PR: https://github.com/owner/repo/pull/42"
    assert extract_pr_url(text) == ("https://github.com/owner/repo/pull/42", 42)


def test_extract_pr_url_picks_last_when_multiple() -> None:
    """If multiple PR URLs appear, pick the last (the one just opened)."""
    text = (
        "ref: https://github.com/owner/repo/pull/10 — closes #1\n"
        "now opening: https://github.com/owner/repo/pull/99"
    )
    assert extract_pr_url(text) == ("https://github.com/owner/repo/pull/99", 99)


def test_extract_pr_url_none_when_missing() -> None:
    assert extract_pr_url("just some text, no PR url here") == (None, None)


def test_extract_pr_url_works_with_http_or_https() -> None:
    text = "http://github.com/owner/repo/pull/7"
    assert extract_pr_url(text) == ("http://github.com/owner/repo/pull/7", 7)


# --------------------------------------------------------------------------- #
# extract_gate_verdict
# --------------------------------------------------------------------------- #


def test_extract_gate_verdict_pass() -> None:
    assert extract_gate_verdict("reached 12_PASS_HANDOFF, done") == "PASS"


def test_extract_gate_verdict_blocked_wins_over_pass() -> None:
    """If both PASS and BLOCKED appear, BLOCKED must win."""
    text = "early note: 12_PASS_HANDOFF candidate\nfinal: 13_BLOCKED_HANDOFF"
    assert extract_gate_verdict(text) == "BLOCKED"


def test_extract_gate_verdict_fail_wins_over_pass() -> None:
    text = "PASS_HANDOFF_COMPLETE was approached\n10_GATE_VERDICT: FAIL"
    assert extract_gate_verdict(text) == "FAIL"


def test_extract_gate_verdict_unknown() -> None:
    assert extract_gate_verdict("no gate text at all") == "UNKNOWN"


# --------------------------------------------------------------------------- #
# extract_test_counts
# --------------------------------------------------------------------------- #


def test_extract_test_counts_pytest_all_pass() -> None:
    assert extract_test_counts("60 passed in 2.35s") == (60, 60)


def test_extract_test_counts_pytest_with_failures() -> None:
    assert extract_test_counts("3 failed, 57 passed in 4.1s") == (57, 60)


def test_extract_test_counts_jest() -> None:
    text = "Tests: 1 failed, 23 passed, 24 total\nSnapshots: 0 total"
    assert extract_test_counts(text) == (23, 24)


def test_extract_test_counts_unknown_format() -> None:
    assert extract_test_counts("no test output at all") == (None, None)


# --------------------------------------------------------------------------- #
# detect_failure_categories
# --------------------------------------------------------------------------- #


def test_detect_failure_unparseable_llm_output() -> None:
    text = "json.JSONDecodeError: Expecting value: line 1 column 1"
    cats = detect_failure_categories(text)
    assert "unparseable-llm-output" in cats


def test_detect_failure_missing_error_handling() -> None:
    text = "AttributeError: 'NoneType' object has no attribute 'get'"
    cats = detect_failure_categories(text)
    assert "missing-error-handling" in cats


def test_detect_failure_gate_blocked() -> None:
    text = "Gate runner halted: 13_BLOCKED_HANDOFF"
    cats = detect_failure_categories(text)
    assert "gate-blocked" in cats


def test_detect_failure_tests_failed() -> None:
    text = "3 failed, 57 passed in 4.1s"
    cats = detect_failure_categories(text)
    assert "tests-failed" in cats


def test_detect_failure_timeout() -> None:
    text = "claude timed out after 1800s"
    cats = detect_failure_categories(text)
    assert "claude-timeout" in cats


def test_detect_failure_categories_dedup() -> None:
    """Multiple matches of the same category appear only once."""
    text = "json.JSONDecodeError once\njson.JSONDecodeError again"
    cats = detect_failure_categories(text)
    assert cats.count("unparseable-llm-output") == 1


def test_detect_failure_categories_none_for_clean_log() -> None:
    assert detect_failure_categories("All good. Tests passed. PR opened.") == []


def test_detect_failure_categories_preserves_declaration_order() -> None:
    """When multiple categories match, they appear in FAILURE_PATTERNS order."""
    text = (
        "json.JSONDecodeError: bad output\n"
        "AttributeError: 'NoneType' has no attribute 'get'\n"
        "claude timed out after 600s"
    )
    cats = detect_failure_categories(text)
    # unparseable-llm-output declared before missing-error-handling declared
    # before claude-timeout
    assert cats.index("unparseable-llm-output") < cats.index("missing-error-handling")
    assert cats.index("missing-error-handling") < cats.index("claude-timeout")


# --------------------------------------------------------------------------- #
# count_exported_funcs
# --------------------------------------------------------------------------- #


def test_count_exported_funcs_simple(tmp_path: Path) -> None:
    """Count top-level `def ` lines in a single .py file."""
    f = tmp_path / "mod.py"
    f.write_text(
        "def a():\n    pass\n\n"
        "def b():\n    pass\n\n"
        "class C:\n    def c_method(self):\n        pass\n"
    )
    # method indented under class — should NOT count
    assert count_exported_funcs(tmp_path, ["mod.py"]) == 2


def test_count_exported_funcs_skips_non_py(tmp_path: Path) -> None:
    f = tmp_path / "thing.md"
    f.write_text("def looks_like_python(): pass\n")
    assert count_exported_funcs(tmp_path, ["thing.md"]) == 0


def test_count_exported_funcs_missing_file_is_zero(tmp_path: Path) -> None:
    """A deleted file in the diff should not crash; counts as 0."""
    assert count_exported_funcs(tmp_path, ["never_existed.py"]) == 0


def test_count_exported_funcs_empty_changed_paths(tmp_path: Path) -> None:
    assert count_exported_funcs(tmp_path, []) == 0


def test_count_exported_funcs_multifile(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def x():\n    pass\n")
    (tmp_path / "b.py").write_text("def y():\n    pass\ndef z():\n    pass\n")
    assert count_exported_funcs(tmp_path, ["a.py", "b.py"]) == 3


# --------------------------------------------------------------------------- #
# diff_stats (against a real tiny git repo)
# --------------------------------------------------------------------------- #


def _init_repo(path: Path) -> None:
    """Initialize a minimal git repo at ``path`` for diff_stats tests."""
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    # Configure identity locally so commits work even with no global config.
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)


def test_diff_stats_against_main(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "a.py").write_text("def hello():\n    pass\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    # Rename branch to main so diff_stats finds it.
    subprocess.run(["git", "branch", "-m", "main"], cwd=repo, check=True)
    # Branch off and make a change
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    (repo / "a.py").write_text(
        "def hello():\n    pass\n\ndef goodbye():\n    pass\n"
    )
    (repo / "b.py").write_text("def thing():\n    pass\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "feature"], cwd=repo, check=True)

    ds = diff_stats(repo, base_ref="main")
    assert ds.files == 2
    assert "a.py" in ds.changed_paths
    assert "b.py" in ds.changed_paths
    assert ds.additions > 0


def test_diff_stats_missing_repo_returns_zeros(tmp_path: Path) -> None:
    """diff_stats on a non-repo dir returns zeros, doesn't crash."""
    ds = diff_stats(tmp_path / "not-a-repo")
    assert ds.additions == 0 and ds.deletions == 0 and ds.files == 0


# --------------------------------------------------------------------------- #
# score_variant_run (composed)
# --------------------------------------------------------------------------- #


def test_score_variant_run_missing_log_returns_unknowns(tmp_path: Path) -> None:
    """If log_path doesn't exist, scorer returns gate_verdict=UNKNOWN and
    no PR url, and counts diff stats as zero (no .git)."""
    result = score_variant_run(tmp_path / "no-worktree", tmp_path / "no-log.txt")
    assert result["pr_url"] is None
    assert result["gate_verdict"] == "UNKNOWN"
    assert result["diff_files"] == 0
    assert result["exported_func_count"] == 0


def test_score_variant_run_with_log_only(tmp_path: Path) -> None:
    """A populated log with no worktree still extracts gate verdict + PR url."""
    log_path = tmp_path / "run.log"
    log_path.write_text(
        "starting variant B\n"
        "60 passed in 2.4s\n"
        "12_PASS_HANDOFF reached\n"
        "PR: https://github.com/owner/repo/pull/77\n"
    )
    result = score_variant_run(tmp_path / "no-wt", log_path)
    assert result["gate_verdict"] == "PASS"
    assert result["pr_number"] == 77
    assert result["test_pass_count"] == 60
    assert result["test_total_count"] == 60
    assert result["failure_categories"] is None


def test_score_variant_run_records_failures(tmp_path: Path) -> None:
    log_path = tmp_path / "run.log"
    log_path.write_text(
        "claude timed out after 1800s\n"
        "json.JSONDecodeError: Expecting value\n"
    )
    result = score_variant_run(tmp_path / "no-wt", log_path)
    assert result["failure_categories"] is not None
    cats = result["failure_categories"].split(",")
    assert "unparseable-llm-output" in cats
    assert "claude-timeout" in cats
