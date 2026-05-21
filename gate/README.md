# Gate folder (v0.4 prep — ported verbatim)

## Origin

This folder was ported verbatim from `~/.claude/skills/software-dev/gate/` on **2026-05-21**
as preparation for claude-pipeline v0.4. No file contents were modified during the port;
filenames are preserved (the leading numeric prefix is semantically load-bearing — it
encodes the state-machine order of the gate runner).

## How v0.4+ uses this folder

claude-pipeline v0.4 introduces tier-routing plus a **unified gate-folder audit system**.
This folder is that audit system's source of truth. Instead of inlining audit logic in
each pipeline node, the v0.4 (and later) verify ladder walks this directory as a state
machine — each gate file declares the checks to run, what counts as PASS/FAIL, and which
gate to transition to next. The runner is `src/claude_pipeline/gate_runner.py`.

Until v0.4 ships, the gate folder lives here as a **read-only reference port**. The
pipeline still runs v0.3 verify logic. Do not modify these files during v0.4 prep —
upstream changes will be re-ported when v0.4 is built.

## File categories

Every top-level `*.md` and `*.yaml` falls into one of three categories. Full per-file
categorization is in `CATEGORIZATION.csv`.

- **deterministic** — the gate's verdict is computable from pure-mechanical checks
  (file existence, regex, AST walk, `git status --porcelain`, JSON schema match,
  subprocess exit code). No model judgment needed. Implementation = a Python function.

- **llm-judged** — the gate's verdict requires a model call (reviewer prompt, evidence
  adequacy review, AI-pattern detection, narrative quality assessment). Implementation
  = `claude --print` with a role prompt; the gate file body is the prompt.

- **hybrid** — both. Deterministic check gates the LLM call (e.g., "file must exist
  before we ask the model whether its content is adequate") OR the LLM call's verdict
  is checked against a deterministic floor (e.g., "model says PASS but `git status`
  is dirty → override to FAIL"). Implementation = Python wrapper that runs the
  deterministic part first, then dispatches to the LLM if/when needed.

Templates (`*_TEMPLATE.md`, `*_TEMPLATE.yaml`) are not gates themselves — they are
artifact scaffolds that the gates read or produce. They are categorized as `template`
in the CSV.

## Entry and terminal states

- **Entry point:** `00_START.md` — Gate 5.4 state-machine entry; reads/writes
  `CURRENT_STATE.yaml` in the run's `reports/<task_area>/` directory.
- **Terminal: success** — `PASS_HANDOFF_COMPLETE` (file: `12_PASS_HANDOFF.md`)
- **Terminal: blocked** — `BLOCKED_HANDOFF` (file: `13_BLOCKED_HANDOFF.md`)

Any state other than these two is non-terminal and the runner must continue advancing.
Transition rules live in each gate file's body (and in `TRANSITION_RULES.md` for the
cross-cutting rules), not in the runner code.

## Quick map of the state machine (Gate 5.4)

```
00_START
  -> 18_GATE_PROFILE_SELECTION
  -> 01_EVIDENCE_ADEQUACY  (-> 02 if upgrade needed -> back to 01)
  -> 03_EVIDENCE_CONSISTENCY
  -> 14_ENFORCEMENT_AUTHORITY_AUDIT  (when applicable)
  -> 04_PANEL_ENTRY -> 05_R1 -> 06_R2 -> 07_R3 -> 08_R4 -> 09_R5
  -> 10_GATE_VERDICT
       PASS    -> 15 -> 16 -> 17 -> 37 -> 12_PASS_HANDOFF (terminal)
       AUTOFIX -> 11_FIX_CYCLE -> back to 01
       BLOCKED -> 13_BLOCKED_HANDOFF (terminal)
```

Plus the supplementary audit gates (19-36) that the verdict step may delegate to
based on the selected gate profile (`GATE_PROFILES.md`).

## File counts at port time

- Top-level files: 86 (62 `.md`, 4 `.yaml`, plus the README being written now)
- Subdirectories: `tools/`, `tests/`, `scripts/`, `domain_addenda/`, `examples/`,
  `logs/`, `reports/` — preserved as-is (test fixtures included for replay).

## See also

- `STATE_MACHINE.md` — full canonical transition spec
- `STATE_SCHEMA.md` — `CURRENT_STATE.yaml` shape
- `GATE_PROFILES.md` and `GATE_PROFILE_SELECTOR.md` — which gates are required for
  which task profiles (lite / full / merge / etc.)
- `CATEGORIZATION.csv` — per-file category + suggested implementation (v0.4 prep)
