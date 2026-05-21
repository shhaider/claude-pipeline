"""Helpers for capturing the worktree's diff against the base branch.

Used by the v0.3 review ladder — every reviewer sees the same diff so
their judgments are based on the actual change set rather than a model
summary that might have drifted from reality.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

# Hard cap on diff size shipped to the LLM. 80 KB is enough for the
# kind of focused PRs this pipeline produces (typically <2k lines of
# changes). If we ever blow past that, head + tail beats full truncation.
MAX_DIFF_CHARS = 80_000


def _untracked_files_diff(cwd: str) -> str:
    """Return a synthetic diff for untracked files: a `--- /dev/null`
    block for each file, with its content inlined.

    The code node creates files in the worktree but does NOT git add
    them — `pr_node` does the staging right before commit. So when the
    reviewer ladder runs (between code and pr), untracked files don't
    show up in `git diff`. The gatekeeper would then FAIL "spec
    completeness" for files that actually exist on disk.

    To prevent that, we capture untracked files via `git status
    --porcelain` and inline them. This makes the diff a faithful
    representation of "everything the pipeline produced", not just
    "everything that's already tracked".
    """
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        log.warning("git status timed out — untracked files not included")
        return ""
    if proc.returncode != 0:
        return ""

    untracked: list[str] = []
    for line in proc.stdout.splitlines():
        # Porcelain format: XY filepath  (X = index, Y = worktree)
        # "??" prefix means untracked.
        if line.startswith("?? "):
            untracked.append(line[3:].strip())

    if not untracked:
        return ""

    # For directories, expand to files
    expanded: list[str] = []
    for entry in untracked:
        p = Path(cwd) / entry
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and "__pycache__" not in f.parts and ".pyc" not in f.suffix:
                    expanded.append(str(f.relative_to(cwd)))
        elif p.is_file():
            expanded.append(entry)

    blocks: list[str] = []
    for rel in expanded:
        full = Path(cwd) / rel
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            log.warning("could not read untracked %s: %s", rel, e)
            continue
        # Format as a unified diff block. The +/- prefix on each line
        # mimics the shape reviewers expect from `git diff`.
        prefixed = "\n".join(f"+{l}" for l in content.splitlines())
        n_lines = len(content.splitlines())
        block = (
            f"diff --git a/{rel} b/{rel}\n"
            f"new file mode 100644\n"
            f"--- /dev/null\n"
            f"+++ b/{rel}\n"
            f"@@ -0,0 +1,{n_lines} @@\n"
            f"{prefixed}\n"
        )
        blocks.append(block)
    return "\n".join(blocks)


def capture_diff(worktree_path: str | Path, base_branch: str = "main") -> str:
    """Return `git diff <base>` (plus untracked-file synthetic diffs)
    as a single string, capped at MAX_DIFF_CHARS.

    Untracked files in the worktree are inlined as synthetic `/dev/null`
    diff blocks. This matters because the reviewer ladder runs BEFORE
    pr_node has done `git add`, so newly-created files (like
    `tests/__init__.py`) would otherwise be invisible to the reviewers
    and the release_gatekeeper would FAIL "spec completeness" for files
    that exist on disk.

    If the worktree was branched off a remote, `<base>` may not exist
    locally. We try `<base>` first, then `origin/<base>`, then fall back
    to the full diff against HEAD's first parent.

    Returns an empty string on error (and logs it) so reviewers can still
    proceed with the summary even if diff capture breaks.
    """
    cwd = str(worktree_path)
    tracked = ""
    for ref in (base_branch, f"origin/{base_branch}"):
        try:
            proc = subprocess.run(
                ["git", "diff", ref, "--no-color"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            log.warning("git diff vs %s timed out", ref)
            continue
        if proc.returncode == 0:
            tracked = proc.stdout
            log.info("diff captured against %s (%d chars tracked)", ref, len(tracked))
            break
        log.debug("git diff vs %s failed (exit %d)", ref, proc.returncode)
    else:
        # Last-resort: diff HEAD against its first parent
        try:
            proc = subprocess.run(
                ["git", "diff", "HEAD~1", "--no-color"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if proc.returncode == 0:
                tracked = proc.stdout
                log.info("diff captured against HEAD~1 (%d chars)", len(tracked))
        except subprocess.TimeoutExpired:
            pass

    untracked = _untracked_files_diff(cwd)
    if untracked:
        log.info("diff includes %d chars of untracked-file content", len(untracked))

    combined = tracked + ("\n" + untracked if untracked else "")
    if not combined:
        log.warning("could not capture diff for worktree=%s base=%s", cwd, base_branch)
        return ""

    if len(combined) > MAX_DIFF_CHARS:
        head = combined[: MAX_DIFF_CHARS // 2]
        tail = combined[-MAX_DIFF_CHARS // 2 :]
        combined = f"{head}\n\n[... diff truncated — {len(combined)} chars total ...]\n\n{tail}"
    return combined
