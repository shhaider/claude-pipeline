"""Subprocess wrapper around `claude --print`.

Single responsibility: invoke Claude Code CLI with a prompt + working
directory, return stdout. Captures stderr separately. Enforces a wall-
clock timeout. Refuses to swallow non-zero exit codes — pipeline nodes
decide what to do with failures.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Raised when `claude --print` exits non-zero or times out."""


@dataclass
class ClaudeResult:
    stdout: str
    stderr: str
    duration_s: float


def run_claude(
    prompt: str,
    *,
    cwd: Path | str | None = None,
    timeout_s: int = 600,
    extra_args: list[str] | None = None,
    add_dirs: list[Path | str] | None = None,
    output_format: str = "text",
    permission_mode: str = "bypassPermissions",
    model: str | None = None,
) -> ClaudeResult:
    """Run `claude --print <prompt>` and return the result.

    Args:
        prompt: The prompt body. Passed via stdin to avoid argv length limits.
        cwd: Working directory for the child. Claude Code reads/writes from
            here.
        timeout_s: Hard wall-clock timeout. Process is killed if exceeded.
        extra_args: Additional CLI flags appended verbatim.
        add_dirs: Paths to make readable via `--add-dir`. The worktree is
            usually the cwd; use add_dirs for read-only references like
            the parent repo's docs.
        output_format: 'text' for plain stdout, 'stream-json' for SSE-shaped
            JSONL events.
        permission_mode: One of 'default', 'acceptEdits', 'plan',
            'bypassPermissions'. The pipeline trusts its own prompts so we
            default to bypassPermissions.
        model: Override model name; None means CLI default.

    Returns:
        ClaudeResult with stdout / stderr / duration.

    Raises:
        ClaudeError on non-zero exit or timeout.
    """
    import time

    args = ["claude", "--print", "--permission-mode", permission_mode]
    if output_format != "text":
        args += ["--output-format", output_format]
    if model:
        args += ["--model", model]
    for d in add_dirs or []:
        args += ["--add-dir", str(d)]
    if extra_args:
        args += list(extra_args)

    cwd_path = Path(cwd) if cwd else Path.cwd()
    log.info("claude.run cwd=%s timeout=%ds prompt_len=%d", cwd_path, timeout_s, len(prompt))

    env = os.environ.copy()
    # If the operator has a global ANTHROPIC_BASE_URL pointed somewhere
    # weird (e.g. an old proxy that no longer exists), unset it so the
    # subprocess talks directly to api.anthropic.com via the configured
    # OAuth token. This is a safety net — most invocations won't need it.
    env.pop("ANTHROPIC_BASE_URL", None)

    start = time.monotonic()
    try:
        proc = subprocess.run(
            args,
            input=prompt,
            cwd=str(cwd_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise ClaudeError(
            f"claude timed out after {timeout_s}s (cwd={cwd_path})"
        ) from e

    duration = time.monotonic() - start
    if proc.returncode != 0:
        raise ClaudeError(
            f"claude exited {proc.returncode} after {duration:.1f}s — "
            f"stderr: {proc.stderr[:500]}"
        )

    return ClaudeResult(stdout=proc.stdout, stderr=proc.stderr, duration_s=duration)


def assert_claude_available() -> None:
    """Quick sanity check that `claude` is on PATH and runnable."""
    try:
        proc = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise ClaudeError(
            "claude CLI not found or unresponsive. Ensure `claude` is on PATH "
            "and CLAUDE_CONFIG_DIR points to an authenticated config dir."
        ) from e
    log.info("claude available: %s", proc.stdout.strip())
