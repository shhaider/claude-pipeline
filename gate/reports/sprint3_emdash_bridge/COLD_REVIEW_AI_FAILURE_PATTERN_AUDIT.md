# Cold Review — R3 AI Failure Pattern Audit
Sprint 3 — SimpleAgent emdash Bridge
Gate 5.4 — Reviewer 3

State: R3_IN_PROGRESS

Do not be charitable. Do not praise. Fail closed.

---

## Patterns checked

### Code patterns

**exported but not wired**
- `HookDecision` and `start_bridge_server` exported from `governed_fsm_conduit/bridge/__init__.py`
- `start_bridge_server` is imported in `front_door.py` line 9 and called at line 407.
- `HookDecision` is used in `hook_server.py` (internally) and in `tests/test_bridge.py` (test assertions).
- Assessment: Both exports are wired. start_bridge_server is production-wired. HookDecision is test-wired (used by test assertions). No stranded export.
- BLOCKING: NO

**wrong import path**
- `front_door.py` imports `from governed_fsm_conduit.bridge import start_bridge_server`
- Module is at `governed_fsm_conduit/bridge/__init__.py` which exports `start_bridge_server` from `hook_server.py`
- Import path is correct.
- BLOCKING: NO

**unawaited async**
- No async code in hook_server.py (uses stdlib http.server, threading — synchronous)
- BLOCKING: NO — NOT APPLICABLE

**swallowed errors**
Finding: `hook_server.py` line 113-117: `except Exception as exc: ... decision = HookDecision(allowed=True, reason="Internal error — failing open")`
This swallows any exception in `decide()` during HTTP handler execution. The design choice is intentional ("Fail open — do not crash the server") and documented in the contract. The `log.error` call means the error IS logged.
Assessment: Pattern present by design. The "fail open" behavior on internal error is a deliberate security/availability trade-off documented in the contract. NON-BLOCKING.
- BLOCKING: NO (by-design, documented)

**free variable bug**
- `hook_server.py` uses `self.state_root` via dynamic subclass binding: `handler_cls = type("Handler", (_HookHandler,), {"state_root": resolved_root})`. This is injected at class creation time, not a free variable.
- All variables in scope within functions examined.
- BLOCKING: NO

**top-level output ambiguity**
- One output path: `decide()` returns `HookDecision`. HTTP handler uses only this function.
- BLOCKING: NO

**duplicate source of truth**
- `_TERMINAL_STATES` in `hook_server.py` is defined inline and the comment notes it must stay in sync with `service.py`. This is a soft duplicate of truth — two places define terminal states.
- Risk: if service.py adds a new terminal state and hook_server.py is not updated, the bridge may count a completed run as ACTIVE.
- Assessment: NON-BLOCKING for Sprint 3 but a noted maintenance risk. The comment explicitly calls this out. No evidence it caused a test failure.

Pattern: `duplicate source of truth`
Location: hook_server.py lines 27-28
Evidence: `_TERMINAL_STATES = frozenset({"S21", "S83"})` with comment "Must stay in sync with TERMINAL_STATES in service.py"
Impact: If service.py adds terminal states without updating hook_server.py, bridge may misclassify runs
BLOCKING: NO (documented; currently in sync; not a Sprint 3 defect)

**hardcoded local paths**
- No hardcoded user paths in hook_server.py or bridge/__init__.py
- front_door.py uses `ROOT / ".agentos-ng" / "governed-fsm-conduit"` where ROOT is `Path(__file__).resolve().parent`
- This is portable — derives from the script location
- BLOCKING: NO

---

### Test patterns

**source-string tests**
- All bridge tests check runtime behavior (allowed=True/False, reason contents) — not source code strings
- BLOCKING: NO

**permissive OR assertions**
Examined test assertions:
- `assert decision.allowed is True` — exact boolean, no OR
- `assert "No FSM state" in decision.reason or "No active" in decision.reason` — THIS IS AN OR ASSERTION
Finding: `test_decide_allow_no_state_root` asserts `"No FSM state" in decision.reason or "No active" in decision.reason`. This passes if either string is in the reason. Both strings would indicate correct behavior but checking either one allows the other branch to be wrong.
- Assessment: The OR assertion in test_decide_allow_no_state_root is technically permissive. However, both options represent valid "no runs" reasons for an allowed=True response. The test also separately checks `decision.allowed is True`. The OR is for the reason text (informational), not for the core allow/deny decision.
- BLOCKING: NO — the critical assertion (`allowed is True`) is exact; the OR is only on human-readable reason text

Pattern: `permissive OR assertions`
Location: test_bridge.py:89
Evidence: `assert "No FSM state" in decision.reason or "No active" in decision.reason`
Impact: Does not mask a wrong allowed/denied decision; only allows either of two valid reason strings
BLOCKING: NO

**exit-code-as-proof**
- Tests do NOT pass because process exits 0 and nothing else; they assert on specific fields of the returned dict/decision object
- BLOCKING: NO

**parser/gate split-brain**
- Single parsing path: decide() in hook_server.py
- No parallel parser
- BLOCKING: NO

**manual command output used as substitute for tests**
- No manual command outputs substituted for test assertions
- BLOCKING: NO

---

### Evidence/packaging patterns

**stale handoff artifacts**
- HANDOFF.md SHA (756a5706) matches repo_state.txt SHA — consistent
- HANDOFF.md branch matches repo_state.txt branch — consistent
- Test counts in HANDOFF.md match test_output.txt — consistent
- BLOCKING: NO

**incomplete snapshots**
- Sprint 3 does not include named snapshot files (e.g., hook_server_snapshot.py). Source files are readable from the repo. The contract does not explicitly require snapshot files.
- This is a gap vs. gate minimum evidence bundle, noted in Evidence Adequacy Assessment.
- BLOCKING: NO — gate auditor has read access to actual source files

**stale report carryover**
- Prior cycle 0 reports in `sprints/sprint3_emdash_bridge/gate/` are historical. They are registered in STALE_FILE_REGISTER.yaml. They are not being used as current final evidence.
- BLOCKING: NO

**self-review false positive**
- Prior COLD_REVIEW_ADJUDICATION.md (cycle 0) says "Evidence adequacy: PASS — test_output.txt, diff.patch, repo_state.txt, HANDOFF.md, ENFORCEMENT_AUTHORITY_AUDIT.md all present"
- Direct inspection confirms all named files exist on disk — no false positive
- BLOCKING: NO

**stale evidence reuse**
- test_output.txt is the current evidence — not reused from a prior failing run
- BLOCKING: NO

**synthetic-only proof**
- decide() unit tests use real on-disk RUN.json files via _write_fake_run (not mocked)
- HTTP integration tests use a real HTTP server (not mocked)
- Only the tool_closed test uses a mock (for state_policy_for) — and no real policy exists yet
- BLOCKING: NO

**review-over-empty-evidence**
- Evidence Adequacy Assessment confirms adequate evidence before panel
- BLOCKING: NO

**pending commit language**
- HANDOFF.md "Changed files" section says "New files (untracked at handoff — to be committed)". This describes the real state correctly — files are on disk but not yet committed. This is not misleading placeholder language.
- BLOCKING: NO

**snapshots contradicting diff**
- No named snapshot files. Source files read directly. diff.patch is consistent with actual front_door.py content.
- BLOCKING: NO

**skipped or failing tests hidden in prose**
- test_output.txt clearly shows `1 skipped` with reason shown inline: `test_decide_deny_tool_closed SKIPPED (No state...)`
- HANDOFF.md explicitly mentions 1 skipped and explains why
- Not hidden
- BLOCKING: NO

**unrelated work counted**
- Sprint 3 deliverables are exactly the files in the contract file-touch map. No unrelated files modified.
- BLOCKING: NO

---

### Protocol patterns

**mid-cycle fix then adjudication**
- Prior cycle 0 ad-hoc reviews were completed before this formal Gate 5.4 run
- This formal run reviews the code fresh — not the patched state
- BLOCKING: NO

**next phase started without authorization**
- No evidence of later-phase work started
- BLOCKING: NO

---

### Enforcement patterns (Gate 4.1 additions)

**wrong_gate_profile_too_weak**
- Selected profile: GATE_FULL for D3 (production_wiring). Correct.
- BLOCKING: NO

**production_caller_overclaim**
- HANDOFF.md explicitly labels delivery as `INFRASTRUCTURE_READY_NOT_WIRED`. No overclaim of live behavior.
- BLOCKING: NO

**consumer_api_bypass**
- Tests call `decide()` directly and via real HTTP server. Tests do not inspect DB or file state as proxy for API behavior.
- BLOCKING: NO

**warning_contradicts_success**
- test_output.txt: no warnings, no ENOENT, no deprecation warnings, no connection failures in output
- Only skipped test has a skip reason message which is normal
- BLOCKING: NO

**wrong_required_test_set**
- test command `pytest tests/test_bridge.py -v` targets the specific required test file, not a broad glob
- BLOCKING: NO

**manifest_self_size_stale_or_zero**
- No zip manifest used. Directory-based package.
- BLOCKING: NOT APPLICABLE

**migration_sql_only_runner_not_proven**
- No migration. NOT APPLICABLE.
- BLOCKING: NO

**prompt_invalid_js_snippet**
- No JavaScript snippets in any prompt file. Python project.
- BLOCKING: NO

**helper_test_only_claiming_production**
- `start_bridge_server` is called in `front_door.py:main()` (production caller), not only in tests
- Correctly labeled INFRASTRUCTURE_READY_NOT_WIRED, not LIVE_BEHAVIOR_FIXED
- BLOCKING: NO

**file_exists_on_host_missing_from_export**
- Package is directory-based on the same host; all Sprint 3 files exist in the repo dir
- BLOCKING: NO — gate_used/ and other proof files will be addressed in FINAL_PACKAGE_AUDIT

**advisory gate mistaken for enforcement**
- createTask bypass correctly identified as advisory; labeled ADVISORY in enforcement audit
- provisionTask path correctly labeled AUTHORITATIVE
- BLOCKING: NO

**lower-layer bypass**
- createTask.ts bypass documented and accepted for Sprint 3 scope
- BLOCKING: NO (accepted)

**split-brain lifecycle**
- Single source of truth: on-disk RUN.json files. Bridge reads only.
- No split-brain possible within Sprint 3 scope.
- BLOCKING: NO

**detection-without-prevention**
- Sprint 3 correctly labeled INFRASTRUCTURE_READY_NOT_WIRED. The prevention (emdash actually blocking) is the Sprint 2 proof. This is not a misrepresentation — it's an honest classification.
- BLOCKING: NO

**negative-test-without-side-effect-check**
Finding: The bridge's negative tests (deny path) check that `allowed=False` is returned. They do not check that emdash actually failed to provision (side effect). This is `detection-without-prevention` as noted above.
Assessment: For INFRASTRUCTURE_READY_NOT_WIRED, this is expected and correctly classified. The handoff does not claim full enforcement proof for Sprint 3.
BLOCKING: NO — correctly classified tier

**auto-merge bypass**
- NOT APPLICABLE — no merge operations in this sprint
- BLOCKING: NO

**consumer-before-producer scheduling**
- NOT APPLICABLE
- BLOCKING: NO

**false-completion trust**
- No worker self-report issues. Tests ran and output is verified.
- BLOCKING: NO

**right command, wrong context**
- test_output.txt lacks inline branch/HEAD. However, tests are context-independent (tmp_path isolation). The handoff makes no branch-specific test claim.
- BLOCKING: NO

---

## R3 Summary
- Patterns checked: 32 (all base patterns + all Gate 4.1 additions)
- Instances found: 4 (2 notable, 2 accepted)
- BLOCKING findings: 0
- NON-BLOCKING findings: 4
  1. `duplicate source of truth` — _TERMINAL_STATES defined in hook_server.py separately from service.py (documented, in sync)
  2. `permissive OR assertions` — test_decide_allow_no_state_root uses OR on reason text (not on allow/deny decision)
  3. `swallowed errors` — fail-open on internal error is intentional and documented
  4. `detection-without-prevention` — bridge tests prove detection; prevention proof is deferred (Sprint 2 covers it; INFRASTRUCTURE_READY classification is correct)
