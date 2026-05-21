# Next Prompt Decision
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 34

State: NEXT_PROMPT_DECISION_IN_PROGRESS

---

## Q1 -- Continue / correction / split / defer / stop?

**CONTINUE**

Sprint 3 completed the SimpleAgent side of the emdash bridge as specified. The next phase (Sprint 4 or equivalent) should address the known gaps:
1. Wire createTask.ts through the before-provision hook (emdash-side PR)
2. Full e2e integration test (SimpleAgent + emdash together)
3. Potentially add real tool_closed states to policy

The next prompt (if one exists for Sprint 4) remains valid as planned.

---

## Q2 -- Recommended model/tier/effort for next step

- Model: claude-sonnet (or auto -- the emdash-side PR is straightforward TypeScript wiring)
- Effort tier: D2 (single-file change in emdash, plus a test)
- Gate profile: GATE_STANDARD (D2, no production wiring claim on SimpleAgent side -- the PR is in emdash)
- Estimated complexity: LOW-MEDIUM

The createTask.ts bypass fix is a focused wiring change in emdash. It does not require GATE_FULL unless it touches emdash's production entrypoint.

---

## Q3 -- Exact next allowed action

Merge the Sprint 3 branch (`shhaider/emdash-bridge`) into the target branch. Then: create a PR in emdash that wires `createTask.ts` through the before-provision hook to close the governance bypass gap.

---

## Q4 -- Forbidden next actions

- Do not modify `hook_server.py` or `bridge/__init__.py` -- Sprint 3's SimpleAgent side is complete.
- Do not claim LIVE_BEHAVIOR_FIXED until the emdash createTask bypass is closed.
- Do not start a "Sprint 4" on the SimpleAgent side until Sprint 3 is merged and the emdash-side PR is at least planned.

---

## Verdict

State: **NEXT_PROMPT_DECISION_COMPLETE**
