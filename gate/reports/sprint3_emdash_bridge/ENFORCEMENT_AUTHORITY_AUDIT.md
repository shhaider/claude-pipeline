# Enforcement Authority Audit
Sprint 3 — SimpleAgent emdash Bridge
Gate 5.4 — Step 14

State: ENFORCEMENT_AUDIT_IN_PROGRESS

---

## Applicability

- Does this task involve enforcement/gating/blocking/control? YES
- Justification: Sprint 3 builds a bridge server that returns allow/deny decisions to gate emdash task provisioning. The bridge is an agent governance layer with enforcement semantics.

---

## Protected actions

| action | claimed controlling component | true authority | evidence path |
|---|---|---|---|
| emdash task provisioning via provisionTask.ts RPC | SimpleAgent bridge (POST /hooks/before-provision) | emdash's provisionTask.ts — calls the hook and halts if `allowed: false` | Sprint 2 integration test (not in Sprint 3 scope) |
| emdash task creation via createTask.ts direct call | None (bypass exists) | taskManager.provisionTask directly — bridge not consulted | ENFORCEMENT_AUTHORITY_AUDIT.md (prior cycle 0) |

---

## Source-of-truth map

| domain | source of truth | secondary systems | risk of split-brain | mitigation |
|---|---|---|---|---|
| FSM current state | on-disk RUN.json files in state_root | bridge reads these read-only | LOW — bridge only reads, never writes | read-only access eliminates write split-brain |
| emdash task lifecycle | emdash's internal task store | SimpleAgent bridge provides allow/deny signal | LOW — bridge is advisory for createTask path | documented; future emdash PR needed |
| task provisioning decision | SimpleAgent bridge response | emdash honors the response for provisionTask path | MEDIUM — createTask path bypasses | bypass is documented and accepted for Sprint 3 |

---

## Bypass path inventory

| protected action | possible bypass path | tested? | result | evidence path | blocker? |
|---|---|---|---|---|---|
| task provisioning gate | createTask.ts → taskManager.provisionTask direct (skips hook) | NO — live emdash not available in Sprint 3 | BYPASSED — documented in Sprint 2/3 artifacts | ENFORCEMENT_AUTHORITY_AUDIT.md (prior cycle 0) | NO — accepted for Sprint 3 scope |
| task provisioning gate | Human or agent directly calling emdash API bypassing hook config | NOT_TESTED | Theoretically possible | N/A | NO — out of scope |
| task provisioning gate | Misconfigured hooks.json pointing to wrong port | NOT_TESTED | Would fall through to permissive default | N/A | NO — deployment config, not code scope |

---

## Negative side-effect tests

| test | unsafe action attempted | expected prevention | observed final state | pass/fail | raw output path |
|---|---|---|---|---|---|
| Unit: test_decide_deny_planning_state | decide() called with S06 (planning) ACTIVE run | expected: allowed=False | decision.allowed is False, S06 in reason | PASS | test_output.txt |
| Unit: test_decide_deny_tool_closed | decide() called with synthetic tool_closed state | expected: allowed=False | decision.allowed is False, "tool_closed" in reason | PASS | test_output.txt |
| Unit: test_decide_deny_unknown_state | decide() called with unknown S99_UNKNOWN | expected: allowed=False (precaution) | decision.allowed is False | PASS | test_output.txt |
| Integration: test_http_server_deny | HTTP POST with active S06 run on disk | expected: HTTP 200 with allowed=false + reason | server returns {allowed: false, reason: "..."} | PASS | test_output.txt |
| Live e2e: emdash blocks task on deny | NOT RUN — out of Sprint 3 scope | emdash would not create worktree | NOT TESTED | N/A | N/A |

Note: The negative side-effect tests above verify that the bridge CORRECTLY RESPONDS with deny. They do not verify that emdash actually halts provisioning (the "prevention" side). The prevention side was verified in Sprint 2's live integration test, which is referenced in HANDOFF.md but not included in Sprint 3 artifacts.

---

## Before/after authority proof

| action | before state evidence | attempted command/event | after state evidence | conclusion |
|---|---|---|---|---|
| Bridge returns deny on S06 state | RUN.json written to tmp_path with current_state=S06 | decide(tmp_path) called | decision.allowed is False | PROVEN: bridge correctly reads on-disk state and denies |
| Bridge returns allow on empty state_root | No RUN.json files in tmp_path | decide(tmp_path) called | decision.allowed is True | PROVEN: bridge correctly allows when no active runs |
| HTTP POST returns allow | No runs in tmp_path | POST /hooks/before-provision | HTTP 200 {allowed: true} | PROVEN: HTTP layer correctly passes through allow decision |
| emdash doesn't provision task after deny | NOT CAPTURED — requires live emdash | N/A | NOT CAPTURED | OUT OF SCOPE for Sprint 3 |

---

## Advisory vs authoritative classification

| gate/control | advisory or authoritative | reason | required fix if advisory |
|---|---|---|---|
| Bridge for provisionTask.ts path | AUTHORITATIVE (with Sprint 2 proof) | emdash's provisionTask.ts calls the hook and structurally halts if allowed=false; Sprint 2 verified this | N/A — authoritative |
| Bridge for createTask.ts path | ADVISORY | createTask.ts calls taskManager.provisionTask directly without consulting the hook | Future emdash PR: wire createTask through before-provision hook |

---

## Findings

Finding: createTask bypass path not governed
Evidence: ENFORCEMENT_AUTHORITY_AUDIT.md (prior cycle 0) — "createTask.ts → taskManager.provisionTask (src/main/core/tasks/operations/createTask.ts) — MEDIUM — advisory only on this code path — ACCEPTED for Sprint 3"
Impact: Tasks created via createTask.ts bypass governance entirely
BLOCKING: NO — formally accepted for Sprint 3 scope with roadmap entry required
Required correction: Future emdash PR — "fix(hooks): wire createTask through before-provision hook to close governance gap"

Finding: No live e2e prevention proof
Evidence: Sprint 3 scope is SimpleAgent-side only; Sprint 2 verified provisionTask hook chain
Impact: Cannot independently verify emdash blocks on `allowed: false` from this sprint's bridge
BLOCKING: NO — INFRASTRUCTURE_READY_NOT_WIRED classification suspends this requirement; Sprint 2 evidence covers it

---

## Enforcement verdict

PASS (conditional on INFRASTRUCTURE_READY_NOT_WIRED classification)

Rationale: The bridge correctly implements allow/deny logic. The primary provisioning path (provisionTask.ts) is governed, verified by Sprint 2. The createTask bypass is documented, accepted, and tracked for future remediation. Sprint 3's INFRASTRUCTURE_READY_NOT_WIRED classification is appropriate and honest. No blocking enforcement findings for this sprint.

---

## Self-check: would this catch known failures?

1. ORCH auto-merged after blocked verdict? — NOT APPLICABLE (no merge in this sprint)
2. ORCH auto-merged after validation failure? — NOT APPLICABLE
3. Consumer before producer scheduling? — NOT APPLICABLE (single-system bridge)
4. False completion report passing validation? — NOT APPLICABLE
5. Missing verification artifacts? — Would catch (bridge tests + test_output.txt present)
6. Block PASS_FOR_HANDOFF until fixed? — YES, if enforcement verdict were FAIL

All applicable checks satisfied. Enforcement verdict: PASS.
