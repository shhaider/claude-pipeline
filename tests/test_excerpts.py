"""Tests for the deterministic excerpt-gathering preprocessing.

Pure-Python; no LLM calls, no network. Runs against a tmp_path with a
fixture filesystem we build inside each test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_pipeline.excerpts import (
    extract_tokens,
    gather_excerpts_for_files,
    gather_relevant_excerpts,
)


class TestExtractTokens:
    def test_picks_snake_case(self):
        text = "Add the build_pipeline function to graph_state.py"
        tokens = extract_tokens(text)
        assert "build_pipeline" in tokens
        assert "graph_state" in tokens

    def test_picks_camel_case(self):
        text = "We need to wire gatherRelevantExcerpts into the planner"
        tokens = extract_tokens(text)
        assert "gatherRelevantExcerpts" in tokens

    def test_picks_pascal_case(self):
        text = "The ContractWriter and PackPlanner roles must agree"
        tokens = extract_tokens(text)
        assert "ContractWriter" in tokens
        assert "PackPlanner" in tokens

    def test_skips_short_tokens(self):
        text = "fix bug in api_x" # api_x is <5 chars after underscore? len=5 ok; "bug" is 3
        tokens = extract_tokens(text)
        assert "bug" not in tokens

    def test_caps_at_max_tokens(self):
        # 12 distinct snake_case tokens — should cap at 8
        text = " ".join(f"foo_bar_{i}" for i in range(12))
        tokens = extract_tokens(text)
        assert len(tokens) <= 8

    def test_dedupes(self):
        text = "build_pipeline build_pipeline build_pipeline"
        tokens = extract_tokens(text)
        assert tokens.count("build_pipeline") == 1

    def test_empty_input(self):
        assert extract_tokens("") == []
        assert extract_tokens("   ") == []

    def test_plain_english_filtered(self):
        # No mixed case, no underscores → should produce no tokens
        text = "please add the feature to the project quickly"
        tokens = extract_tokens(text)
        assert tokens == []


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    """Build a tiny mock repo with files we can grep."""
    (tmp_path / "src" / "lib").mkdir(parents=True)
    (tmp_path / "src" / "lib" / "core.py").write_text(
        "def build_pipeline(args):\n"
        "    '''docstring'''\n"
        "    return Pipeline(args)\n"
        "\n"
        "class Pipeline:\n"
        "    pass\n"
    )
    (tmp_path / "src" / "lib" / "utils.js").write_text(
        "const gatherRelevantExcerpts = (req) => {\n"
        "  return req.split('\\n');\n"
        "}\n"
        "module.exports = { gatherRelevantExcerpts };\n"
    )
    # Test file — should be skipped
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_core.py").write_text(
        "def test_build_pipeline():\n    assert True\n"
    )
    # Noise dirs
    (tmp_path / "node_modules" / "junk").mkdir(parents=True)
    (tmp_path / "node_modules" / "junk" / "lib.js").write_text(
        "function build_pipeline() {}\n"
    )
    return tmp_path


class TestGatherRelevantExcerpts:
    def test_finds_python_def(self, repo_root: Path):
        result = gather_relevant_excerpts(
            "Refactor build_pipeline so it accepts a config dict",
            repo_root,
        )
        assert "build_pipeline" in result
        assert "core.py" in result
        assert "def build_pipeline" in result

    def test_finds_js_const(self, repo_root: Path):
        result = gather_relevant_excerpts(
            "Move gatherRelevantExcerpts into a separate module",
            repo_root,
        )
        assert "gatherRelevantExcerpts" in result
        assert "utils.js" in result

    def test_skips_test_files(self, repo_root: Path):
        # The token matches both core.py and test_core.py — non-test wins.
        result = gather_relevant_excerpts("update build_pipeline", repo_root)
        assert "core.py" in result
        assert "test_core" not in result

    def test_skips_node_modules(self, repo_root: Path):
        result = gather_relevant_excerpts("update build_pipeline", repo_root)
        assert "node_modules" not in result

    def test_no_tokens_returns_empty(self, repo_root: Path):
        result = gather_relevant_excerpts("fix the bug", repo_root)
        assert result == ""

    def test_nonexistent_root_returns_empty(self, tmp_path: Path):
        result = gather_relevant_excerpts(
            "build_pipeline", tmp_path / "doesnotexist"
        )
        assert result == ""

    def test_worktree_under_skip_dir_parent_still_works(self, tmp_path: Path):
        """Regression: when the worktree path itself is *under* a
        directory whose name matches _SKIP_DIRS (e.g. runs/ in the
        real pipeline layout), the skip-dir filter must NOT match the
        parent path. Only parts relative to the worktree root should
        be skip-filtered.
        """
        # Simulate runs/{id}/worktree/ layout
        worktree = tmp_path / "runs" / "abc123" / "worktree"
        (worktree / "src").mkdir(parents=True)
        (worktree / "src" / "module.py").write_text(
            "def build_pipeline(args):\n    return args\n"
        )
        result = gather_relevant_excerpts("update build_pipeline", worktree)
        assert "module.py" in result
        assert "def build_pipeline" in result


class TestGatherExcerptsForFiles:
    def test_returns_head_of_named_files(self, repo_root: Path):
        result = gather_excerpts_for_files(
            ["src/lib/core.py", "src/lib/utils.js"],
            repo_root,
        )
        assert "core.py" in result
        assert "utils.js" in result
        assert "def build_pipeline" in result

    def test_silently_skips_missing_files(self, repo_root: Path):
        result = gather_excerpts_for_files(
            ["src/lib/core.py", "src/lib/does_not_exist.py"],
            repo_root,
        )
        assert "core.py" in result
        assert "does_not_exist" not in result

    def test_path_traversal_blocked(self, repo_root: Path):
        # Attempting "../etc/passwd" should be blocked by the resolve check.
        result = gather_excerpts_for_files(
            ["../../../etc/passwd"], repo_root
        )
        assert "passwd" not in result
        assert result == ""
