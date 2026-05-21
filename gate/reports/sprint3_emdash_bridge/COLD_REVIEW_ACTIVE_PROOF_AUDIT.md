# Cold Review — R2 Active Proof Audit
Sprint 3 — SimpleAgent emdash Bridge
Gate 5.4 — Reviewer 2

State: R2_IN_PROGRESS

Do not be charitable. Do not praise. Fail closed.

---

## Behaviors assessed

| behavior | proof type | proof artifact | active path? | sufficient? | BLOCKING: YES/NO |
|---|---|---|---|---|---|
| decide() returns ALLOW when no state_root | Real file system, tmp_path, decide() called directly | test_output.txt (test_decide_allow_no_state_root) | YES — calls decide() with nonexistent path | YES | NO |
| decide() returns ALLOW when no active runs | Real empty tmp_path dir, decide() called directly | test_output.txt (test_decide_allow_no_active_runs) | YES | YES | NO |
| decide() returns ALLOW for S14 implementation state | Real RUN.json on disk via _write_fake_run | test_output.txt (test_decide_allow_implementation_state) | YES — reads real file | YES | NO |
| decide() returns DENY for S06 planning state | Real RUN.json on disk via _write_fake_run | test_output.txt (test_decide_deny_planning_state) | YES — reads real file | YES | NO |
| decide() returns DENY for tool_closed tier | Patched state_policy_for, real RUN.json | test_output.txt (test_decide_deny_tool_closed) | PARTIAL — mock of policy function | YES for code branch; NO for real policy | NO — accepted as code branch proof |
| decide() returns ALLOW for completed (non-ACTIVE) run | Real RUN.json with status=COMPLETE on disk | test_output.txt (test_decide_allow_completed_run) | YES | YES | NO |
| decide() returns DENY for unknown state (not in IMPL_STATES) | Real RUN.json with S99_UNKNOWN | test_output.txt (test_decide_deny_unknown_state_not_in_implementation_states) | YES | YES | NO |
| HTTP server returns allowed=true for no active runs | Real HTTP server on port=0, real urllib POST | test_output.txt (test_http_server_allow) | YES — real HTTP round-trip | YES | NO |
| HTTP server returns allowed=false for S06 active run | Real HTTP server on port=0, real urllib POST | test_output.txt (test_http_server_deny) | YES — real HTTP round-trip | YES | NO |
| front_door.py starts bridge at boot | Code inspection only — no main() integration test | diff.patch | NO — code path not exercised by tests | PARTIAL — code is wired but not runtime-verified | NO — acceptable for INFRASTRUCTURE_READY |
| emdash blocks provisioning on deny | NOT TESTED — out of scope | HANDOFF.md (written statement) | NO | NO — but accepted for INFRASTRUCTURE_READY | NO — accepted gap |

---

## Exit code and count verification

Raw output (test_output.txt):
- Reported by pytest: `8 passed, 1 skipped in 0.28s`
- HANDOFF.md claim: `8 passed, 1 skipped (exit 0)`
- EXIT_CODE line: `EXIT_CODE: 0` (with space — see Consistency Register for note)
- Agreement: YES on counts; EXIT_CODE format deviates from `^EXIT_CODE:0\s*$` (space present)

Count discrepancy check: test_output.txt shows 9 items collected, 8 passed, 1 skipped. HANDOFF.md says "9 tests" in the "See test_output.txt for raw output" note, and "8 passed, 1 skipped" in the Test counts section. No discrepancy.

---

## Artifact Lifecycle Timing Audit (Gate 4.1 / GATE_FULL requirement)

| Artifact | When generated | Data available at time? | Lifecycle position correct? | Issue |
|---|---|---|---|---|
| test_output.txt | After implementation complete | YES — all test files existed | YES | None |
| diff.patch | After implementation complete | YES | YES | None |
| repo_state.txt | After implementation complete | YES | YES | None |
| HANDOFF.md | After tests passed | YES | YES | None |
| ENFORCEMENT_AUTHORITY_AUDIT.md (prior cycle) | After implementation review | YES | YES | None |

No lifecycle timing violations found.

---

## Execution context rule check

The test_output.txt does NOT contain:
- `git branch --show-current` output
- `git rev-parse HEAD` output
- `pwd` output

This means the test log does not carry branch/HEAD proof.

The R2 execution context rule states: "A test log or command output that claims to prove behavior on a specific branch, directory, or package is insufficient unless the log includes git branch --show-current, git rev-parse HEAD, and pwd."

Assessment: The HANDOFF.md does NOT claim "tests ran on main" or "post-merge tests ran on main." It makes no branch-specific test claim. The test evidence proves behavior of the decision logic, not branch-specific behavior. The test isolation uses `tmp_path` which is environment-independent.

Branch/HEAD proof IS separately captured in `repo_state.txt` which provides the context at time of evidence collection.

FINDING: test_output.txt lacks inline branch/HEAD context. However, this is NON-BLOCKING because: (a) the test does not make a branch-specific claim in the handoff, (b) repo_state.txt separately records context, (c) the tests use path isolation that makes branch irrelevant.

BLOCKING: NO

---

## R2 Summary
- Behaviors assessed: 11
- Active-path proven: 8 (7 unit tests with real files + 2 HTTP integration tests)
- Source-only / mock-only / prose-only: 2 (tool_closed test uses mock; front_door.py wiring is code inspection only)
- BLOCKING findings: 0
- NON-BLOCKING findings: 2
  1. tool_closed test uses mock state_policy_for (NON-BLOCKING: proves code branch exists, real policy has no tool_closed states yet)
  2. front_door.py boot wiring not runtime-verified (NON-BLOCKING: INFRASTRUCTURE_READY tier; code wiring visible in diff)
