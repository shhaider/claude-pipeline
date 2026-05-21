"""Subprocess wrapper around `claude --print --output-format json`.

Uses Claude Code's structured JSON output instead of free-form text.
Each invocation returns a stable envelope:

    {
      "type": "result",
      "subtype": "success",
      "is_error": false,
      "result": "<the actual model output>",
      "duration_ms": ...,
      "total_cost_usd": ...,
      "usage": {...},
      ...
    }

This removes the brittleness of regex-extracting JSON from free-form
stdout. Nodes still parse their own JSON OUT of result.text when they
asked Claude for JSON output — but that's one well-defined string,
not the whole subprocess transport.

If a node needs progress events during a long-running operation, use
`run_claude_stream` instead.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

log = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Raised when `claude --print` exits non-zero, times out, or emits
    a malformed envelope."""


@dataclass
class ClaudeResult:
    """Structured result from one `claude --print` invocation."""

    text: str
    """The final model output (the `result` field of the envelope)."""

    session_id: str
    """Claude Code's session UUID for this invocation. Useful for
    cross-referencing with Conductor or for resuming via `--resume`."""

    duration_s: float
    """Wall-clock seconds from process spawn to exit."""

    cost_usd: float
    """Claude Code's self-reported cost. Free if running under a Max
    subscription via OAuth; pay-per-token if running with an API key."""

    num_turns: int
    """Number of agent-loop turns Claude took to complete the task."""

    usage: dict = field(default_factory=dict)
    """Raw token usage dict from the envelope."""

    is_error: bool = False
    """True if Claude reported a soft error (the subprocess still
    exited 0 but the envelope says is_error=true)."""

    stop_reason: str = ""
    """Why the agent loop stopped: end_turn, max_tokens, error, etc."""


def _build_args(
    *,
    output_format: str,
    permission_mode: str,
    model: str | None,
    add_dirs: list[Path | str] | None,
    extra_args: list[str] | None,
) -> list[str]:
    args = [
        "claude",
        "--print",
        "--permission-mode",
        permission_mode,
        "--output-format",
        output_format,
    ]
    if model:
        args += ["--model", model]
    for d in add_dirs or []:
        args += ["--add-dir", str(d)]
    if extra_args:
        args += list(extra_args)
    return args


def _env_for_subprocess() -> dict:
    """Drop ANTHROPIC_BASE_URL if set (some operator setups point it at
    proxies that are no longer running). The CLI will use the OAuth
    flow against the real api.anthropic.com."""
    env = os.environ.copy()
    env.pop("ANTHROPIC_BASE_URL", None)
    return env


def run_claude(
    prompt: str,
    *,
    cwd: Path | str | None = None,
    timeout_s: int = 600,
    extra_args: list[str] | None = None,
    add_dirs: list[Path | str] | None = None,
    permission_mode: str = "bypassPermissions",
    model: str | None = None,
    resume_session_id: str | None = None,
) -> ClaudeResult:
    """Run `claude --print` with structured JSON output, return parsed result.

    Args:
        prompt: The prompt body. Passed via stdin to avoid argv length limits.
        cwd: Working directory for the child. Claude Code reads/writes here.
        timeout_s: Hard wall-clock timeout. Process killed if exceeded.
        extra_args: Additional CLI flags appended verbatim.
        add_dirs: Paths to make readable via `--add-dir`.
        permission_mode: 'default' | 'acceptEdits' | 'plan' | 'bypassPermissions'.
            The pipeline trusts its own prompts so we default to bypass.
        model: Override model name. None = CLI default.
        resume_session_id: If set, the CLI is invoked with `--resume <id>`,
            continuing a prior session. The new prompt is appended to that
            session's history so the model retains all prior tool use,
            file reads, and assistant turns. The session_id of the result
            in this case is the SAME id (sessions are stable across resumes).

    Raises:
        ClaudeError on timeout, non-zero exit, or malformed envelope.
    """
    # Build resume flag into extra_args
    resume_extra: list[str] = []
    if resume_session_id:
        resume_extra = ["--resume", str(resume_session_id)]
    merged_extra = resume_extra + (list(extra_args) if extra_args else [])

    args = _build_args(
        output_format="json",
        permission_mode=permission_mode,
        model=model,
        add_dirs=add_dirs,
        extra_args=merged_extra,
    )
    cwd_path = Path(cwd) if cwd else Path.cwd()
    log.info(
        "claude.run cwd=%s timeout=%ds prompt_len=%d resume=%s",
        cwd_path,
        timeout_s,
        len(prompt),
        resume_session_id or "(fresh)",
    )

    start = time.monotonic()
    try:
        proc = subprocess.run(
            args,
            input=prompt,
            cwd=str(cwd_path),
            env=_env_for_subprocess(),
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
            f"stderr: {proc.stderr[:500]!r}"
        )

    # Parse the JSON envelope. With --output-format=json, stdout is a
    # single JSON object on one line (no leading/trailing junk).
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise ClaudeError(
            f"claude returned non-JSON stdout (exit 0): {e}; "
            f"first 300 chars: {proc.stdout[:300]!r}"
        ) from e

    if env.get("type") != "result":
        raise ClaudeError(
            f"claude envelope has unexpected type={env.get('type')!r}"
        )

    return ClaudeResult(
        text=str(env.get("result", "")),
        session_id=str(env.get("session_id", "")),
        duration_s=duration,
        cost_usd=float(env.get("total_cost_usd") or 0.0),
        num_turns=int(env.get("num_turns") or 0),
        usage=env.get("usage") or {},
        is_error=bool(env.get("is_error", False)),
        stop_reason=str(env.get("stop_reason") or ""),
    )


def run_claude_stream(
    prompt: str,
    *,
    cwd: Path | str | None = None,
    timeout_s: int = 1800,
    extra_args: list[str] | None = None,
    add_dirs: list[Path | str] | None = None,
    permission_mode: str = "bypassPermissions",
    model: str | None = None,
) -> Iterator[dict]:
    """Stream JSONL events from `claude --print --output-format stream-json`.

    Yields one parsed event dict per line. Event types include:
      - {"type": "system", "subtype": "init", ...}
      - {"type": "assistant", "message": {...}}
      - {"type": "result", ...}                  ← terminal event
      - {"type": "rate_limit_event", ...}

    Use this when you need observable progress on a long-running node
    (e.g. the implementer printing tool-use events as Claude does work).
    Standard nodes that just want the final answer should use
    `run_claude` instead — it's simpler.
    """
    args = _build_args(
        output_format="stream-json",
        permission_mode=permission_mode,
        model=model,
        add_dirs=add_dirs,
        extra_args=["--verbose"] + (list(extra_args) if extra_args else []),
    )
    cwd_path = Path(cwd) if cwd else Path.cwd()
    log.info("claude.stream cwd=%s timeout=%ds prompt_len=%d", cwd_path, timeout_s, len(prompt))

    start = time.monotonic()
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd_path),
        env=_env_for_subprocess(),
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    # Send the prompt and close stdin so Claude can finish.
    try:
        proc.stdin.write(prompt)
        proc.stdin.close()
    except BrokenPipeError:
        pass

    try:
        for line in proc.stdout:
            if time.monotonic() - start > timeout_s:
                proc.kill()
                raise ClaudeError(f"claude stream timed out after {timeout_s}s")
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                log.warning("claude stream skipped non-JSON line: %s", line[:200])
                continue
    finally:
        proc.wait(timeout=10)
        if proc.returncode and proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise ClaudeError(
                f"claude stream exited {proc.returncode} — stderr: {stderr[:500]!r}"
            )


def extract_json(text: str) -> dict | list:
    """Best-effort: pull the first balanced JSON value out of arbitrary text.

    For nodes that ask Claude for JSON output and got it inside
    `result.text`. Handles three common shapes:
      - pure JSON: `{"key": "value"}` or `[...]`
      - code-fenced: ```json\n{...}\n```
      - prose preamble before/after the JSON
    """
    import re

    stripped = text.strip()
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", stripped)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Walk to find first balanced { or [ block
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        depth = 0
        start = -1
        for i, ch in enumerate(cleaned):
            if ch == open_ch:
                if depth == 0:
                    start = i
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        return json.loads(cleaned[start : i + 1])
                    except json.JSONDecodeError:
                        # Try the next one
                        start = -1
                        continue

    raise ValueError(f"no balanced JSON value found in: {text[:200]!r}")


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
