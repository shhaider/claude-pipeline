"""Deterministic codebase excerpt gathering.

Ports metabuilder's `gatherRelevantExcerpts(planningRequest)` from
`scripts/metabuilder/plan_self_upgrade.js:~704`.

Purpose: ground LLM research by inlining actual source text from the
worktree so the model doesn't hallucinate file paths. This is the kind
of mechanical preprocessing the architectural rules explicitly call
out as staying deterministic.

Algorithm (generic — works for any repo, not just metabuilder):
  1. Extract identifier tokens from the planning request:
       - snake_case, camelCase, PascalCase
       - >= 5 characters
       - cap at 8 tokens (longest / most-specific first)
  2. Walk the repo from worktree root, skipping common noise dirs
     (node_modules, .git, __pycache__, dist, build, .venv, runs).
  3. For each token, grep code files for definition-like patterns:
       - python:     `def token`, `class token`, `token = ` (top-level)
       - js/ts:      `function token`, `const token =`,
                     `token: function`, `module.exports.*token`
       - generic:    fall back to plain substring match
  4. Pick up to 4 non-test files. Read the matching context window
     (~40 lines centered on first match) per file.
  5. Return a single string suitable for inlining into a Claude prompt.

If no tokens are found or no files match, returns an empty string —
callers should treat that as "no excerpts available, proceed without
grounding" rather than as an error.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# Files we never include — too noisy, generated, or binary.
_SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".turbo",
    "runs",
    "checkpoints",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "coverage",
    ".tox",
}
_CODE_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".mjs",
    ".cjs",
    ".go",
    ".rs",
    ".rb",
    ".java",
    ".kt",
    ".swift",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".sh",
    ".bash",
}

# Identifier token regex (Unicode-agnostic; ASCII-only is fine here).
# Matches snake_case (foo_bar), camelCase (fooBar), PascalCase (FooBar).
# Requires at least one underscore OR mixed case to filter out english.
_TOKEN_RE = re.compile(
    r"\b(?:[a-z]+_[a-z_0-9]+|[A-Z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*|[a-z]+[A-Z][a-zA-Z0-9]*|[A-Z][a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*)\b"
)

MAX_TOKENS = 8
MAX_FILES = 4
CONTEXT_LINES_AROUND_MATCH = 20  # ~40 lines total per excerpt


def extract_tokens(text: str) -> list[str]:
    """Pull >=5-char identifier tokens (snake/camel/Pascal) from arbitrary
    text. Deduplicates, caps at MAX_TOKENS, longest-first (longer tokens
    are more specific and so more useful for grepping)."""
    if not text:
        return []
    raw = _TOKEN_RE.findall(text)
    seen: set[str] = set()
    out: list[str] = []
    for t in raw:
        if len(t) < 5:
            continue
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    # Longest first — specific tokens beat generic ones.
    out.sort(key=lambda s: (-len(s), s))
    return out[:MAX_TOKENS]


def _is_test_path(p: Path, root: Path | None = None) -> bool:
    """Heuristic: anything under tests/, *_test.py, *.test.ts, etc.

    If `root` is given, only inspect path parts RELATIVE to root, so a
    worktree path under e.g. /tmp/some-test-dir/worktree/src/... isn't
    mistakenly flagged.
    """
    name = p.name.lower()
    if root is not None:
        try:
            rel = p.resolve().relative_to(root.resolve())
            parts = rel.parts
        except ValueError:
            parts = p.parts
    else:
        parts = p.parts
    parts_lower = {part.lower() for part in parts}
    if "tests" in parts_lower or "test" in parts_lower or "__tests__" in parts_lower:
        return True
    if name.startswith("test_") or name.endswith("_test.py"):
        return True
    if ".test." in name or ".spec." in name:
        return True
    return False


def _iter_code_files(root: Path) -> list[Path]:
    """Yield code files under root, skipping noise dirs.

    Skip-dir matching uses the path RELATIVE to root, so the worktree
    path containing literally e.g. "runs/" or "node_modules/" as a
    parent of `root` doesn't false-positive everything.
    """
    out: list[Path] = []
    root_resolved = root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _CODE_EXTS:
            continue
        try:
            rel = path.resolve().relative_to(root_resolved)
        except ValueError:
            continue
        # Skip anything under a noise dir (relative parts only)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        # Skip files we'd never read
        try:
            if path.stat().st_size > 500_000:  # 500KB — too big
                continue
        except OSError:
            continue
        out.append(path)
    return out


def _grep_token(content: str, token: str) -> int | None:
    """Return line number (0-indexed) of best match for `token`, or None.

    Prefers definition-like contexts (function/class/const decl). Falls
    back to first occurrence.
    """
    lines = content.splitlines()
    # Definition patterns (in priority order)
    patterns = [
        rf"\bdef\s+{re.escape(token)}\b",  # python def
        rf"\bclass\s+{re.escape(token)}\b",  # python/js class
        rf"\bfunction\s+{re.escape(token)}\b",  # js function
        rf"\bconst\s+{re.escape(token)}\s*=",  # js const
        rf"\blet\s+{re.escape(token)}\s*=",  # js let
        rf"\bvar\s+{re.escape(token)}\s*=",  # js var
        rf"^\s*{re.escape(token)}\s*=",  # python top-level assignment
        rf"\b{re.escape(token)}\s*:\s*function\b",  # js method shorthand
        rf"\bmodule\.exports\b.*\b{re.escape(token)}\b",  # js export
        rf"\bexport\s+(?:default\s+)?\b{re.escape(token)}\b",  # js export
    ]
    for pat in patterns:
        cre = re.compile(pat)
        for i, line in enumerate(lines):
            if cre.search(line):
                return i
    # Fall back to first plain substring
    cre = re.compile(rf"\b{re.escape(token)}\b")
    for i, line in enumerate(lines):
        if cre.search(line):
            return i
    return None


def gather_relevant_excerpts(
    planning_request: str,
    worktree_root: Path | str,
    *,
    max_files: int = MAX_FILES,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Build a string of relevant code excerpts to inline in an LLM prompt.

    Args:
        planning_request: the user-facing description of the work
            (issue body, task description, etc.)
        worktree_root: path to the repo checkout to grep
        max_files: cap on number of file excerpts to include
        max_tokens: cap on identifier tokens to grep for

    Returns:
        A string with markdown-fenced excerpts, or "" if nothing found.
    """
    root = Path(worktree_root)
    if not root.is_dir():
        log.warning("gather_excerpts: worktree_root not a dir: %s", root)
        return ""

    tokens = extract_tokens(planning_request)[:max_tokens]
    if not tokens:
        log.info("gather_excerpts: no identifier tokens in planning_request")
        return ""

    log.info("gather_excerpts: tokens=%s", tokens)

    code_files = _iter_code_files(root)
    if not code_files:
        log.info("gather_excerpts: no code files under %s", root)
        return ""

    # For each token, find the first non-test file that matches.
    # Each file appears at most once (multiple tokens can land in the
    # same file — we pick the first token that surfaces it).
    picked: list[tuple[Path, str, int]] = []  # (path, token, line_no)
    picked_paths: set[Path] = set()

    for token in tokens:
        if len(picked) >= max_files:
            break
        for path in code_files:
            if path in picked_paths:
                continue
            if _is_test_path(path, root):
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            line_no = _grep_token(content, token)
            if line_no is not None:
                picked.append((path, token, line_no))
                picked_paths.add(path)
                break

    if not picked:
        log.info("gather_excerpts: no file/token matches")
        return ""

    # Render the excerpts as a single markdown string.
    out_chunks: list[str] = []
    for path, token, line_no in picked:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = content.splitlines()
        start = max(0, line_no - CONTEXT_LINES_AROUND_MATCH)
        end = min(len(lines), line_no + CONTEXT_LINES_AROUND_MATCH + 1)
        window = lines[start:end]
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        # 1-indexed line numbers for human readability
        header = f"### {rel}  (match: `{token}` at line {line_no + 1})"
        numbered = [
            f"{start + i + 1:>5}: {line}" for i, line in enumerate(window)
        ]
        body = "\n".join(numbered)
        out_chunks.append(f"{header}\n```\n{body}\n```")

    return "\n\n".join(out_chunks)


def gather_excerpts_for_files(
    file_paths: list[str],
    worktree_root: Path | str,
    *,
    context_lines: int = 80,
) -> str:
    """Variant for prompt-expansion: given an explicit file list (the
    stage's file_touch_map), inline a head excerpt of each existing file.

    Used by `nodes/prompt_expand.py` so the implementation_builder sees
    the actual file headers it's about to modify.
    """
    root = Path(worktree_root)
    if not root.is_dir():
        return ""

    out_chunks: list[str] = []
    for f in file_paths:
        # Strip leading slash and try to resolve against worktree
        candidate = (root / f.lstrip("/")).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            # Outside worktree, skip
            continue
        if not candidate.is_file():
            # New file the stage will create; skip
            continue
        try:
            content = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = content.splitlines()
        window = lines[:context_lines]
        try:
            rel = candidate.relative_to(root.resolve())
        except ValueError:
            rel = candidate
        numbered = [f"{i + 1:>5}: {line}" for i, line in enumerate(window)]
        body = "\n".join(numbered)
        out_chunks.append(f"### {rel}  (head, {len(window)} lines)\n```\n{body}\n```")

    return "\n\n".join(out_chunks)
