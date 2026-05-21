# Prompt Contract Review
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 19

State: PROMPT_CONTRACT_REVIEW_IN_PROGRESS

---

## Applicability

D3 / production_wiring. Mandatory for D2-hot / D3 / D4 work.

Contract reviewed: `/Users/syedhaider/conductor/workspaces/simpleagent/denver/sprints/sprint3_emdash_bridge/contract.md`

---

## Check 1 -- Ambiguous terms

| Term | Context | Interpretation required | Issue? |
|---|---|---|---|
| "wire" | "MODIFY front_door.py -- import + call start_bridge_server in main()" | Clear: add import and function call | NO |
| "production" | "Server starts alongside SimpleAgent's normal boot" | Clear: the main() function of front_door.py | NO |
| "test" | "Tests prove the allow and deny paths with real HTTP (no mocks)" | Clear: pytest with real HTTP, not mocked | NO |

No ambiguous terms found.

---

## Check 2 -- Hidden assumptions

| Assumption | Stated? | Issue? |
|---|---|---|
| Branch `shhaider/emdash-bridge` exists | YES -- "Branch: shhaider/emdash-bridge" in contract | NO |
| `governed_fsm_conduit` package exists | YES -- referenced in "Grounded facts" | NO |
| `state_policy_for` function exists | YES -- referenced in "Grounded facts" | NO |
| `StateStore` lacks `list_runs()` | YES -- "StateStore has NO list_runs() method" | NO |
| Python stdlib http.server available | YES -- "Python stdlib http.server is available" | NO |

No hidden assumptions found. Contract is well-grounded.

---

## Check 3 -- Lifecycle timing ambiguity

The contract does not require artifacts to be captured at specific points. The test output and repo state are captured after implementation is complete. No lifecycle timing ambiguity.

---

## Check 4 -- Forbidden interpretations

The contract explicitly lists:
- "Explicit out of scope" section with 6 items (server.py, metalite_fsm/, supervisor/, gui/, existing tests, requirements.txt)
- "Do NOT start a new FSM run per hook call"
- "Do NOT require a running FSM to respond"
- "Do NOT modify any FSM state on hook call"
- "No auth between emdash and SimpleAgent"
- "No other hook events beyond task.before_provision"

Forbidden interpretations are well-specified.

---

## Check 5 -- Missing proof specifications

The contract specifies: "pytest tests/test_bridge.py must pass" as a success condition.
The contract specifies failure conditions (6 items).
The contract does not explicitly specify EXIT_CODE capture format -- this is a minor gap (the gate convention `EXIT_CODE:0` was not in the contract, leading to the format deviation `EXIT_CODE: 0`).

NON-BLOCKING: The intent is clear; the format deviation is a tooling artifact.

---

## Check 6 -- Unclear allowed/forbidden files

The contract has a clear file-touch map (5 files: 4 CREATE, 1 MODIFY) and an explicit "out of scope" section. No ambiguity.

---

## Check 7 -- Missing model/tier recommendation

The contract does not specify a model or tier for implementation. For D3 tasks, the gate protocol recommends this be specified.

NON-BLOCKING: The task was successfully implemented without model specification.

---

## Check 8 -- Missing repo cleanliness rule

The contract does not specify expected repo state at completion. HANDOFF.md describes files as "untracked at handoff -- to be committed," which is an honest description but not a specification.

NON-BLOCKING: The repo state was accurately captured regardless.

---

## Check 9 -- Missing generated-evidence-outside-repo rule

The contract does not specify where evidence files should live. Sprint artifacts ended up in `sprints/sprint3_emdash_bridge/` (inside repo), gate reports in `/Users/syedhaider/Downloads/gate/reports/` (outside repo).

NON-BLOCKING: Both locations are functional and accessible.

---

## Check 10 -- Invalid code snippets

The contract includes a `decide()` pseudocode snippet. Comparing to actual implementation:
- Contract pseudocode matches the implemented logic in hook_server.py:36-90.
- No invalid variable names, no non-existent imports.
- Minor: contract shows `run["current_state"]` (bare dict access) while implementation uses `run.get("current_state", "UNKNOWN")` (safer). This is an improvement, not a contradiction.

---

## Check 11 -- References to non-existent files or tests

All file paths in the contract exist or were created. No references to non-existent tests or fixtures.

---

## Check 12 -- Overclaims in the prompt itself

The contract says "Server starts alongside SimpleAgent's normal boot" -- this was implemented (front_door.py:main() calls start_bridge_server). No overclaim.

---

## Verdict

All 12 checks pass or have justified non-applicability. The contract is well-specified for the task.

State: **PROMPT_CONTRACT_PASS**
