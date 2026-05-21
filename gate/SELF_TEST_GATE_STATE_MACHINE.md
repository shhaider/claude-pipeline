# Self-Test — Gate State Machine

This file answers 14 specific questions about whether the gate would catch known failure modes. Read this to verify the design is sound before using the gate in production.

---

## Question 1

**Would the gate catch: a package zip that does not contain a file the MANIFEST.md claims to contain?**

**Answer: YES.**

Step `15_FINAL_PACKAGE_AUDIT.md` Step 3 (Manifest audit) physically lists the zip contents via `zipinfo -1` and cross-checks every file in PACKAGE_MANIFEST.md against the listing. A file present in the manifest but absent from the zip produces a **BLOCKER**. The gate cannot transition to `FINAL_PACKAGE_AUDIT_PASS` with any blocker present. Therefore `12_PASS_HANDOFF.md` cannot be reached. The gate stays in `FINAL_PACKAGE_AUDIT_FAIL` until the file is included in the zip.

---

## Question 2

**Would the gate catch: MANIFEST.md entries that reference local machine paths (e.g., `/Users/agent/...`) instead of portable relative paths?**

**Answer: YES.**

Step `15_FINAL_PACKAGE_AUDIT.md` Step 3 checks each manifest path for local-machine prefixes (`/Users/`, `/home/`, `/tmp/`, `C:\`). Any path matching these prefixes produces `verification_result: LOCAL_PATH_ONLY` — a **BLOCKER**. The fix required is to replace the path with a relative path (e.g., `<task_area>/filename`).

---

## Question 3

**Would the gate catch: HANDOFF.md saying PENDING while CYCLE_TRACKER.md and R5 say PASS?**

**Answer: YES.**

At `15_FINAL_PACKAGE_AUDIT.md` Step 7 (Handoff status pre-check): HANDOFF.md `Final readiness status: PENDING` is detected — **BLOCKER** immediately. Gate cannot proceed.

Additionally, at `16_CANONICAL_HANDOFF_AUDIT.md` Step 4 (Unregistered stale file scan): HANDOFF.md status PENDING contradicts `final_gate_verdict: PASS_FOR_HANDOFF` in CURRENT_STATE.yaml — **BLOCKER** from a second independent check. Both steps catch the same inconsistency.

---

## Question 4

**Would the gate catch: BLOCKED_HANDOFF.md remaining in the package without a HISTORICAL banner after the gate passed?**

**Answer: YES.**

At `16_CANONICAL_HANDOFF_AUDIT.md` Step 3 (Stale file register audit): BLOCKED_HANDOFF.md should be registered in STALE_FILE_REGISTER.yaml when the gate passes after a prior blocked state. If `banner_added: false`, this is a **BLOCKER**.

At `16_CANONICAL_HANDOFF_AUDIT.md` Step 5 (Exactly-one-active-handoff check): if BLOCKED_HANDOFF.md has no HISTORICAL banner, it counts as an active handoff. Combined with HANDOFF.md (the real active handoff), there are two active handoffs — **BLOCKER**.

Additionally, `SCRIPT_SPEC_check_gate_package.md` defines a `verify_stale_file_register` function that catches this programmatically.

---

## Question 5

**Would the gate catch: an agent fixing a blocker mid-cycle and then asking R5 to adjudicate the fixed state (the "mid-cycle fix then adjudication" failure pattern)?**

**Answer: YES.**

`07_R3_AI_PATTERNS.md` lists "mid-cycle fix then adjudication" as one of the 8 AI enforcement failure patterns that R3 checks for. R3 would mark this as a BLOCKING finding if it detects the pattern. R5 would synthesize R3's finding.

Additionally, the state machine structurally prevents this: the states `R1_IN_PROGRESS` through `R5_COMPLETE` are sequential. There is no transition that routes from an R-state back to a fix state and then forward to a different R-state within the same cycle. The only fix state is `FIX_CYCLE_IN_PROGRESS`, which is entered from `GATE_FAIL_AUTOFIX_REQUIRED` — after R5 has already issued the cycle verdict. Mid-cycle fixes that circumvent this sequence are not valid state transitions.

---

## Question 6

**Would the gate catch: a PASS_FOR_HANDOFF issued when the Enforcement Authority Audit recorded a FAIL?**

**Answer: YES.**

`10_GATE_VERDICT.md` has an explicit override rule: if `ENFORCEMENT_AUTHORITY_AUDIT.md` records any FAIL, the gate verdict becomes at minimum `FAIL_AUTOFIX_REQUIRED`, regardless of R5's verdict. A `GATE_PASS_FOR_HANDOFF` state is forbidden unless `enforcement_audit_result` in the current cycle is `PASS` or `NOT_APPLICABLE`.

`TRANSITION_RULES.md` makes this explicit: `GATE_PASS_FOR_HANDOFF` has the additional constraint "enforcement_audit_result must be PASS or NOT_APPLICABLE in this cycle."

`STATE_SCHEMA.md` validation rule 8 enforces this at the YAML write level.

---

## Question 7

**Would the gate catch: cycle 6 being started after cycle 5 failed?**

**Answer: YES.**

`TRANSITION_RULES.md` states: `FIX_CYCLE_COMPLETE → EVIDENCE_ADEQUACY_IN_PROGRESS` requires `cycle_count < 5`. If `cycle_count == 5`, the allowed transition is `MAX_CYCLES_REACHED` → `BLOCKED_HANDOFF_COMPLETE`, not another `EVIDENCE_ADEQUACY_IN_PROGRESS`.

`STATE_SCHEMA.md` validation rule 3 states `cycle_count` must be between 1 and 5. A write of `cycle_count: 6` would be a schema violation.

`11_FIX_CYCLE.md` Step 1 explicitly checks the cycle counter and routes to `13_BLOCKED_HANDOFF.md` if cycle 5 was just completed.

---

## Question 8

**Would the gate catch: R5 being skipped and the gate verdict being drawn directly from R4?**

**Answer: YES.**

The state machine requires `R4_COMPLETE → R5_IN_PROGRESS → R5_COMPLETE → GATE_VERDICT_ISSUED`. There is no valid transition from `R4_COMPLETE` directly to `GATE_VERDICT_ISSUED`.

`TRANSITION_RULES.md` lists `R5_COMPLETE` as the only allowed predecessor of `GATE_VERDICT_ISSUED`. Skipping R5 would require writing a state that TRANSITION_RULES.md marks as forbidden — a state machine violation, which routes to `13_BLOCKED_HANDOFF.md`.

---

## Question 9

**Would the gate catch: the PASS_HANDOFF_COMPLETE terminal state being reached without FINAL_PACKAGE_AUDIT and CANONICAL_HANDOFF_AUDIT having run?**

**Answer: YES.**

`TRANSITION_RULES.md`: `PASS_HANDOFF_COMPLETE` is only allowed from `EXECUTION_CONTEXT_AUDIT_PASS` or `EXECUTION_CONTEXT_AUDIT_NOT_APPLICABLE`. Those states are only reachable from `CANONICAL_HANDOFF_AUDIT_PASS`. `CANONICAL_HANDOFF_AUDIT_PASS` is only reachable from `CANONICAL_HANDOFF_AUDIT_IN_PROGRESS`, which requires `FINAL_PACKAGE_AUDIT_PASS`. There is no shortcut.

`STATE_SCHEMA.md` validation rule 7: if `current_state: PASS_HANDOFF_COMPLETE`, then `final_package_audit_result: PASS`, `canonical_handoff_audit_result: PASS`, and `execution_context_audit_result: PASS or NOT_APPLICABLE` must all be present in CURRENT_STATE.yaml. If any is missing or not PASS/NOT_APPLICABLE, the state write is invalid.

---

## Question 10

**Would the gate catch: a HARD_FACT claim in HANDOFF.md that is not backed by any artifact in CLAIMS_LEDGER.yaml?**

**Answer: PARTIAL — by design, depends on ledger discipline.**

The gate does not automatically scan HANDOFF.md for claims and cross-check them against the ledger. The CLAIMS_LEDGER must be populated by the agent as it writes claims — one entry per claim-to-evidence binding. If an agent writes a HARD_FACT claim in HANDOFF.md but does not add it to CLAIMS_LEDGER.yaml, the ledger audit (Step 15 Step 4) will not catch the gap because the claim is simply absent from the ledger.

The partial mitigation: R4 (`08_R4_HANDOFF.md`) includes a handoff completeness check that looks for claims without backing evidence. R4 would surface this as a BLOCKING or NON-BLOCKING finding, which R5 would synthesize.

The full mitigation requires ledger discipline: every time a HARD_FACT claim is written in any document, a corresponding entry must be added to CLAIMS_LEDGER.yaml immediately. `00_START.md` instructs agents to initialize the ledger at gate entry and populate it throughout.

A future enhancement: `SCRIPT_SPEC_check_gate_package.md`'s `check_local_paths` function could be extended to scan all documents for claim-like patterns and warn on any that are absent from the ledger.

---

---

## Question 11

**Would the gate catch: a post-merge test log that claims tests ran on main, but lacks branch/HEAD proof?**

**Answer: YES.**

At `06_R2_ACTIVE_PROOF.md`: the R2 hard rule now states "a test log without branch/HEAD proof is NOT active proof of 'tested on main'." R2 would mark the claim PARTIAL and flag `BLOCKING: YES`. R5 would synthesize R2's blocking finding.

At `17_EXECUTION_CONTEXT_AUDIT.md` Step: The claim "tests ran on main" triggers the audit. The required context check looks for `git branch --show-current: main` and `git rev-parse HEAD` in the raw output. If absent: **BLOCKER — context not proven**. Gate stays in `EXECUTION_CONTEXT_AUDIT_FAIL`.

Both checks are independent — R2 catches it at review time; Step 17 catches it at handoff audit time even if R2 missed it.

---

## Question 12

**Would the gate catch: a test log showing tests passed, but `git branch --show-current` shows `agentos-ng-integration` while the claim says "post-merge tests ran on main"?**

**Answer: YES — this is the exact AgentOS-NG failure this step was designed for.**

At `17_EXECUTION_CONTEXT_AUDIT.md` context proof table:
- `claim`: "post-merge tests ran on main"
- `branch`: `agentos-ng-integration` (from raw output)
- `expected_context`: `main`
- `observed_context`: `agentos-ng-integration`
- `pass/fail`: FAIL

`observed_context ≠ expected_context` → **BLOCKER**. The test log is genuine — the tests passed — but the context claim is false. The gate stays in `EXECUTION_CONTEXT_AUDIT_FAIL` until the tests are rerun on `main` and new raw output with correct branch proof is produced.

In CLAIMS_LEDGER.yaml the claim entry would have `context_matches: false`, making it a failed EXECUTION_CONTEXT claim.

---

## Question 13

**Would the gate catch: a PACKAGE_FILE_LISTING.txt that contains `/Users/agent/...` paths, claimed as proof that the package contains specific files?**

**Answer: YES — from two independent checks.**

At `15_FINAL_PACKAGE_AUDIT.md` Step 3: any artifact claimed as a package listing is checked for local-machine prefix patterns. `/Users/agent/...` → `LOCAL_PATH_ONLY` → **BLOCKER**.

At `15_FINAL_PACKAGE_AUDIT.md` Step 3 extended check: artifacts claimed to be generated from an uploaded/exported package must show `zipinfo -1 <actual_export>.zip` or `tar -tzf` output. A listing from local `find` or `ls` commands fails this check — **BLOCKER**.

The required fix: regenerate the listing by running `zipinfo -1 <package>.zip > PACKAGE_FILE_LISTING.txt` against the actual exported file.

---

## Question 14

**Would the gate catch: a "final git status was clean" claim contradicted by untracked files in the actual `git status --short` output?**

**Answer: YES.**

At `17_EXECUTION_CONTEXT_AUDIT.md`: "final git status clean" is an execution-context claim. The audit requires the raw output to contain `git status --short` with either an empty result or an explanation for each untracked/modified file (gitignore proof for intentionally ignored files).

If the raw output shows untracked files and no explanation is provided: **BLOCKER — clean-state claim unverified**. 

If no raw `git status --short` output is provided at all: the claim is unsupported → **BLOCKER**.

---

## Overall assessment

| Failure mode | Caught | Mechanism |
|---|---|---|
| File missing from zip | YES | Step 15 manifest audit + claims ledger audit |
| Local-machine-only paths | YES | Step 15 path prefix check + Step 17 package listing check |
| Contradictory handoff status | YES | Step 15 handoff pre-check + Step 16 unregistered stale scan |
| Unlabeled BLOCKED_HANDOFF.md | YES | Step 16 stale register audit + exactly-one-handoff check |
| Mid-cycle fix then adjudication | YES | R3 pattern check + state machine structure |
| Enforcement FAIL → PASS issued | YES | Gate verdict override rule + transition constraint |
| Cycle 6 started after cycle 5 | YES | State machine cycle_count constraint |
| R5 skipped | YES | State machine sequence enforcement |
| Package audit bypassed | YES | Transition rules + state schema |
| Unbacked HARD_FACT claims | PARTIAL | R4 check + ledger discipline required |
| Test log without branch/HEAD proof | YES | R2 hard rule + Step 17 context proof table |
| Right command, wrong branch | YES | Step 17 context_matches check (R3 pattern: "right command, wrong context") |
| Package listing from local paths | YES | Step 15 local-path check + Step 17 package listing check |
| Clean-state claim without git status output | YES | Step 17 required context checks |

---

## Gate 4.1 — Self-test questions (Questions 15–24)

### Question 15

**Would the gate catch: GATE_LITE selected for a hot-file task?**

**Answer: YES.**

`18_GATE_PROFILE_SELECTION.md` Step 1 identifies hot files in the task's file-touch map by checking against `GATE_PROFILE_SELECTOR.md`. Any hot file contact triggers an escalation to D2-hot, which requires GATE_FULL. If GATE_LITE is selected instead, `profile_override_required: true` must be set. `check_gate_package.py` `verify_gate_profile()` detects this as a violation of `gate_profile_not_weaker_than_risk_tier`.

Fixture: `tests/gate_state_machine/fixtures/wrong_gate_profile_too_weak/`

---

### Question 16

**Would the gate catch: a handoff claiming LIVE_BEHAVIOR_FIXED with no production caller?**

**Answer: YES.**

`20_PRODUCTION_CALLER_ACTIVE_PATH_AUDIT.md` requires a grep-provable import chain from a production entry point to the changed module. Without it, the verdict must be `INFRASTRUCTURE_READY_NOT_WIRED` or `TEST_HELPER_ONLY`. `STATE_SCHEMA.md` validation rule 13 requires `final_outcome_label` to be set, and `check_gate_package.py` `verify_required_proof_files()` checks that `PRODUCTION_CALLER_AUDIT.md` is present and its verdict is consistent with `final_outcome_label`.

Fixture: `tests/gate_state_machine/fixtures/production_caller_overclaim/`

---

### Question 17

**Would the gate catch: tests that only use raw DB inspection when the consumer API is also available?**

**Answer: YES.**

`21_CONSUMER_API_PROOF_AUDIT.md` explicitly checks whether each test asserts through the consumer API path. If all tests use only raw DB or file inspection, the verdict is `RAW_ONLY` — insufficient for any task where downstream code will use the API. R3 pattern `consumer_api_bypass` also catches this. Both are independent.

Fixture: `tests/gate_state_machine/fixtures/consumer_api_bypass/`

---

### Question 18

**Would the gate catch: EXIT_CODE 0 but warnings in raw output that directly contradict the claimed success?**

**Answer: YES.**

`22_WARNING_OUTPUT_AUDIT.md` scans all raw outputs with the grep pattern specified. A warning classified as `CONTRADICTS_SUCCESS_CLAIM` is blocking regardless of test exit code. R3 pattern `warning_contradicts_success` also catches this. The hard rule is explicit: "a warning that contradicts claimed behavior is blocking even when tests pass."

Fixture: `tests/gate_state_machine/fixtures/warning_contradicts_success/`

---

### Question 19

**Would the gate catch: a broad test pattern that excluded a required test file?**

**Answer: YES.**

`23_REQUIRED_TEST_SET_EXACTNESS.md` Check 4 explicitly detects when a broad pattern may exclude required test files. If any required test file name does not match the pattern, it is flagged `REQUIRED_TEST_EXCLUDED_BY_PATTERN`. The fixture demonstrates a subtler case where the file matched the pattern but all tests inside were skipped — caught by checking whether the file produced any test results in the raw output.

Fixture: `tests/gate_state_machine/fixtures/wrong_required_test_set/`

---

### Question 20

**Would the gate catch: a manifest that lists itself at 0 bytes or a stale size?**

**Answer: YES.**

`15_FINAL_PACKAGE_AUDIT.md` Gate 4.1 additions (Step A/B/C) include a manifest self-size check. `MANIFEST_FINALIZATION_AUDIT_TEMPLATE.md` specifically checks the manifest's own entry against `stat` output. `check_gate_package.py` `verify_manifest_file_sizes()` flags `MANIFEST_SELF_SIZE_STALE` when they disagree.

Fixture: `tests/gate_state_machine/fixtures/manifest_self_size_stale/`

---

### Question 21

**Would the gate catch: a SQL migration applied manually but never proven via the real runner?**

**Answer: YES.**

`24_MIGRATION_RUNNER_PROOF.md` requires three checks: SQL validity, runner discovery, and runner application. If runner discovery and application are NOT RUN, the verdict must be `SQL_ONLY_PROVEN_RUNNER_NOT_PROVEN`, not `MIGRATION_RUNNER_PROVEN`. The gate blocks at this state until runner proof is provided or the task is blocked.

Fixture: `tests/gate_state_machine/fixtures/migration_sql_only_runner_not_proven/`

---

### Question 22

**Would the gate catch: an implementation prompt with an unquoted JS identifier as a value?**

**Answer: YES.**

`25_IMPLEMENTER_PROMPT_LINT.md` Check 2 explicitly looks for unquoted JS identifiers. The example `model: claude-sonnet-4-6` (unquoted) is a canonical example of this pattern. `check_gate_package.py` `verify_required_proof_files()` verifies that `IMPLEMENTER_PROMPT_LINT.md` is present and its verdict is PASS (not a false PASS with underlying violations).

Fixture: `tests/gate_state_machine/fixtures/prompt_invalid_js_snippet/`

---

### Question 23

**Would the gate catch: a new helper used only by tests but labeled as production wired?**

**Answer: YES.**

`26_STRANDED_HELPER_UNUSED_EXPORT_AUDIT.md` explicitly checks production callers vs. test callers. If only test callers exist, the verdict must be `TEST_HELPER_ONLY`, not `PRODUCTION_WIRED`. The `final_outcome_label` check in `check_gate_package.py` cross-references the stranded helper audit verdict against the handoff label.

Fixture: `tests/gate_state_machine/fixtures/helper_test_only_claiming_production/`

---

### Question 24

**Would the gate catch: a file that exists on the VPS execution host but is absent from the exported zip?**

**Answer: YES.**

`29_EXPORT_CHANNEL_AUDIT.md` explicitly distinguishes "exists on host" from "included in export." The hard rule states: "Exists on VPS is not sufficient if the reviewer receives a zip." The proof must be a `zipinfo -1` line, not a host path listing. `check_gate_package.py` `verify_package_listing_from_export()` detects when the export channel audit used a host path instead of zipinfo output.

Fixture: `tests/gate_state_machine/fixtures/file_exists_on_host_missing_from_export/`

---

## Gate 4.1 — Updated overall assessment

| Failure mode | Caught | Mechanism |
|---|---|---|
| Gate profile too weak for hot file | YES | Step 18 profile selection + script `verify_gate_profile` |
| Production caller overclaim (LIVE_BEHAVIOR_FIXED without caller) | YES | Step 20 production caller audit + overclaim taxonomy check |
| Consumer API bypass (raw inspection only) | YES | Step 21 consumer API audit + R3 pattern |
| Warning contradicts success (EXIT_CODE 0 but fallback active) | YES | Step 22 warning output audit + R3 pattern |
| Wrong required test set (broad pattern, skipped tests) | YES | Step 23 required test set exactness |
| Manifest self-size stale or zero | YES | Step 15 Gate 4.1 additions + script `verify_manifest_file_sizes` |
| Migration SQL applied but runner not proven | YES | Step 24 migration runner proof |
| Implementer prompt invalid JS snippet | YES | Step 25 implementer prompt lint |
| Helper test-only labeled as production wired | YES | Step 26 stranded helper audit + overclaim taxonomy |
| File exists on host but missing from export | YES | Step 29 export channel audit + script `verify_package_listing_from_export` |
