# Sprint 3 Handoff — SimpleAgent ↔ emdash HTTP Bridge

## Branch
`shhaider/emdash-bridge`

## Base commit (HEAD at handoff)
`756a5706ce0ca2a0be4c163a264f1ba109c13235`

## Sprint scope
SimpleAgent side only. emdash was already modified in Sprint 2.

## Changed files

### New files (untracked at handoff — to be committed)
- `governed_fsm_conduit/bridge/__init__.py`
- `governed_fsm_conduit/bridge/hook_server.py`
- `tests/test_bridge.py`
- `agents/integrations/simpleagent-bridge.md`
- `sprints/sprint3_emdash_bridge/` (all sprint artifacts)

### Modified files
- `front_door.py` (+1 import, +3 lines in main())

## Test counts
- Bridge tests: 8 passed, 1 skipped (exit 0)
- Full suite: 217 passed, 1 skipped
- See `test_output.txt` for raw output

## Delivery classification
**INFRASTRUCTURE_READY_NOT_WIRED** — The SimpleAgent side of the bridge is fully implemented
and tested. The emdash side (provisioning blocked based on this response) was confirmed working
in Sprint 2's integration test with mocked responses. End-to-end enforcement proof (emdash
actually blocking a task when this bridge denies) requires running emdash + SimpleAgent together
and is out of Sprint 3 scope.

## Known gaps accepted at handoff

### createTask bypass (accepted gap)
`createTask.ts` in emdash calls `taskManager.provisionTask` directly without going through the
`before-provision` hook. This bypass is documented in `agents/integrations/simpleagent-bridge.md`
under "Known limitations". It is a known gap accepted for Sprint 3 scope. Fix in a future emdash PR.

### tool_closed test skipped
No state in MVP_STATE_POLICIES uses `enforcement_tier="tool_closed"`. The test is a structural
placeholder; enable once a tool_closed state is added to policy.py.

## Next allowed phase
Release gate (Step 10) may proceed. AUTOFIX blockers B3/B4/B5 are resolved.
B1 (INFRASTRUCTURE_READY reclassification) and B2 (createTask acceptance) are resolved by this
document's "Delivery classification" and "Known gaps accepted" sections above.
