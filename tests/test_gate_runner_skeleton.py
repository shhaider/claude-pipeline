"""Skeleton tests for GateRunner (v0.4 prep).

These tests confirm the skeleton runner walks the state machine to a
terminal state. They are intentionally pure-Python — no Claude CLI
spawning, no LLM calls. Once v0.4 ships, deeper tests will be added that
fixture out the LLM transport.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from claude_pipeline.gate_runner import (
    ENTRY_STATE,
    TERMINAL_STATES,
    GateResult,
    GateRunner,
    GateVerdict,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_DIR = REPO_ROOT / "gate"


def test_gate_runner_can_be_instantiated(tmp_path: Path) -> None:
    """GateRunner constructs cleanly against the ported gate/ folder."""
    runner = GateRunner(gate_dir=GATE_DIR, worktree=tmp_path)
    assert runner.gate_dir == GATE_DIR
    assert runner.worktree == tmp_path
    assert runner.history == []


def test_run_walks_from_start_to_terminal(tmp_path: Path) -> None:
    """run() advances from 00_START to one of the terminal states.

    The skeleton's _run_gate always returns PASS and _next_state advances
    to the next numbered file, so the runner should terminate at a
    terminal state without exhausting the step cap.
    """
    runner = GateRunner(gate_dir=GATE_DIR, worktree=tmp_path)
    final = runner.run()

    assert final.gate_name in TERMINAL_STATES
    # The final recorded result in history must match what run() returned.
    assert runner.history[-1].gate_name == final.gate_name


def test_history_records_entry_state_first(tmp_path: Path) -> None:
    """The first entry in history is the gate entry point."""
    runner = GateRunner(gate_dir=GATE_DIR, worktree=tmp_path)
    runner.run()
    assert runner.history[0].gate_name == ENTRY_STATE


def test_history_records_every_gate_visited(tmp_path: Path) -> None:
    """Every gate visited (including the terminal) is in history exactly once
    per visit, and the chain has no duplicates in the skeleton's
    monotonic advance."""
    runner = GateRunner(gate_dir=GATE_DIR, worktree=tmp_path)
    runner.run()
    names = [r.gate_name for r in runner.history]
    # Skeleton advances forward only — no revisits.
    assert len(names) == len(set(names)), f"duplicate visits: {names}"
    # And the entry state and a terminal state are both present.
    assert ENTRY_STATE in names
    assert any(n in TERMINAL_STATES for n in names)


def test_terminal_verdict_is_pass_for_pass_handoff(tmp_path: Path) -> None:
    """Landing in 12_PASS_HANDOFF records a PASS verdict on the terminal
    GateResult; landing in 13_BLOCKED_HANDOFF records BLOCKED."""
    runner = GateRunner(gate_dir=GATE_DIR, worktree=tmp_path)
    final = runner.run()
    if final.gate_name == "12_PASS_HANDOFF":
        assert final.verdict == GateVerdict.PASS
    else:
        assert final.gate_name == "13_BLOCKED_HANDOFF"
        assert final.verdict == GateVerdict.BLOCKED


def test_gate_result_dataclass_defaults() -> None:
    """GateResult constructs with just a name and verdict; findings default
    to an empty list and duration_s defaults to 0.0."""
    r = GateResult(gate_name="00_START", verdict=GateVerdict.PASS)
    assert r.findings == []
    assert r.duration_s == pytest.approx(0.0)
