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


def capture_diff(worktree_path: str | Path, base_branch: str = "main") -> str:
    """Return `git diff <base>` as a single string, capped at MAX_DIFF_CHARS.

    If the worktree was branched off a remote, `<base>` may not exist
    locally. We try `<base>` first, then `origin/<base>`, then fall back
    to the full diff against HEAD's first parent.

    Returns an empty string on error (and logs it) so reviewers can still
    proceed with the summary even if diff capture breaks.
    """
    cwd = str(worktree_path)
    candidates = [base_branch, f"origin/{base_branch}"]
    for ref in candidates:
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
            out = proc.stdout
            if len(out) > MAX_DIFF_CHARS:
                head = out[: MAX_DIFF_CHARS // 2]
                tail = out[-MAX_DIFF_CHARS // 2 :]
                out = f"{head}\n\n[... diff truncated — {len(proc.stdout)} chars total ...]\n\n{tail}"
            log.info("diff captured against %s (%d chars)", ref, len(out))
            return out
        # Fall through to next candidate
        log.debug("git diff vs %s failed (exit %d)", ref, proc.returncode)

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
            log.info("diff captured against HEAD~1 (%d chars)", len(proc.stdout))
            return proc.stdout[:MAX_DIFF_CHARS]
    except subprocess.TimeoutExpired:
        pass

    log.warning("could not capture diff for worktree=%s base=%s", cwd, base_branch)
    return ""
