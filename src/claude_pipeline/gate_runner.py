"""Gate runner — walks the gate/ folder's state machine.

Each gate file declares (in the file body or by filename convention):
- next-state-on-pass
- next-state-on-fail
- checks-required

The runner reads the gate file, executes its checks (deterministic → Python fn,
llm-judged → claude --print, hybrid → both), records the verdict, transitions
to the next state. Loops until PASS_HANDOFF_COMPLETE or BLOCKED_HANDOFF.

This is the v0.4-prep skeleton. The fully wired version comes in the v0.4 build.
Skeleton scope:
- GateRunner can be instantiated against a gate/ directory and worktree
- run() walks numerically-ordered .md gates from 00_START to a terminal state
- Every step is recorded in self.history
- Terminal states (12_PASS_HANDOFF, 13_BLOCKED_HANDOFF) end the loop
- _run_gate() is a stub that returns PASS — fully real verdicts come in v0.4
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Terminal stems — when the runner enters either, it stops.
TERMINAL_STATES: tuple[str, ...] = ("12_PASS_HANDOFF", "13_BLOCKED_HANDOFF")

# Entry stem — first gate the runner enters.
ENTRY_STATE: str = "00_START"


class GateVerdict(Enum):
    """Verdict a single gate emits.

    A gate returns PASS to advance, FAIL to trigger remediation (typically
    routing into 11_FIX_CYCLE), or BLOCKED to short-circuit to
    13_BLOCKED_HANDOFF.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass
class GateResult:
    """Result of executing a single gate file.

    The full v0.4 runner will additionally record per-check breakdowns
    (deterministic vs LLM call) and links to the produced artifact files
    (the *_AUDIT.md / *_REGISTER.md outputs).
    """

    gate_name: str
    verdict: GateVerdict
    findings: list[str] = field(default_factory=list)
    duration_s: float = 0.0


class GateRunner:
    """Walks the gate/ folder as a state machine.

    Parameters
    ----------
    gate_dir : Path
        Directory containing the gate state-machine files (the ported
        ``gate/`` folder at the repo root).
    worktree : Path
        The implementation worktree this run is auditing. Read-only —
        nothing under ``worktree`` is modified by the runner.
    """

    def __init__(self, gate_dir: Path, worktree: Path):
        self.gate_dir = gate_dir
        self.worktree = worktree
        self.log = logging.getLogger("gate_runner")
        self.history: list[GateResult] = []

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(self) -> GateResult:
        """Walk the state machine from 00_START to terminal.

        Returns the final ``GateResult``. ``self.history`` contains the
        chain of every gate visited, in order.
        """
        current = ENTRY_STATE
        # Safety: cap iterations so a misconfigured next_state cannot
        # infinite-loop. 200 is well above the gate count (~37 numbered
        # states even with cycling), so legitimate runs are unaffected.
        max_steps = 200
        steps = 0
        while current not in TERMINAL_STATES:
            if steps >= max_steps:
                self.log.error(
                    "Gate runner exceeded %d steps; halting at %s",
                    max_steps,
                    current,
                )
                result = GateResult(
                    gate_name=current,
                    verdict=GateVerdict.BLOCKED,
                    findings=[f"runner halted: exceeded {max_steps} steps"],
                )
                self.history.append(result)
                return result
            result = self._run_gate(current)
            self.history.append(result)
            current = self._next_state(current, result.verdict)
            steps += 1

        # Record entry into the terminal state itself, with the verdict
        # implied by which terminal we landed on.
        terminal_verdict = (
            GateVerdict.PASS
            if current == "12_PASS_HANDOFF"
            else GateVerdict.BLOCKED
        )
        terminal_result = GateResult(
            gate_name=current,
            verdict=terminal_verdict,
            findings=[],
        )
        self.history.append(terminal_result)
        return terminal_result

    # ------------------------------------------------------------------ #
    # Internals — fully wired in v0.4
    # ------------------------------------------------------------------ #

    def _run_gate(self, gate_name: str) -> GateResult:
        """Execute one gate.

        Stub implementation — fully real version comes in v0.4 build.
        """
        # TODO(v0.4): read gate file, dispatch by category in CATEGORIZATION.csv:
        #   deterministic → call the Python check function for this gate
        #   llm-judged    → claude --print with the gate file body as role prompt
        #   hybrid        → run the Python preflight, then dispatch to LLM
        # Then parse the verdict and populate findings/duration_s.
        return GateResult(
            gate_name=gate_name,
            verdict=GateVerdict.PASS,
            findings=[],
        )

    def _next_state(self, current: str, verdict: GateVerdict) -> str:
        """Lookup next state from gate file metadata.

        Stub for now — advances to the next numbered ``.md`` file
        alphabetically. The real v0.4 implementation will parse
        ``next-state-on-pass`` / ``next-state-on-fail`` declarations from
        the gate file body (and ``TRANSITION_RULES.md`` for cross-cutting
        rules) and honor verdict-aware routing.
        """
        # TODO(v0.4): parse next-state-on-pass / next-state-on-fail from gate file
        # For skeleton, just advance to next numbered gate alphabetically.
        files = sorted(self.gate_dir.glob("*.md"))
        # Build an ordered list of stems that are valid state names — i.e.,
        # gate files whose stem starts with a digit. Reference / template
        # files (STATE_MACHINE.md, *_TEMPLATE.md, GATE_PROFILES.md, etc.)
        # are not state nodes.
        state_files = [f for f in files if f.stem[:2].isdigit()]
        try:
            idx = next(
                i for i, f in enumerate(state_files) if f.stem == current
            )
            return state_files[idx + 1].stem
        except (StopIteration, IndexError):
            # Off the end of the numbered states → declare PASS terminal.
            # In v0.4 this branch becomes unreachable: every gate file will
            # declare an explicit terminal route.
            return "12_PASS_HANDOFF"
