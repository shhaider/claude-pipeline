# Gate 5.1 Baseline Audit

**Created:** 2026-05-01
**Purpose:** P00 — Pre-upgrade audit of Gate 5 to identify gaps that enabled the M77-P05A failure.

---

## Q1 — Which files currently mention EXIT_CODE validation?

| File | Mentions EXIT_CODE? | How strong? |
|---|---|---|
| `03_EVIDENCE_CONSISTENCY.md` | YES — Check 5 RAW_TEST_OUTPUT_TABLE has `EXIT_CODE` column | Structural mention but no exact regex requirement |
| `23_REQUIRED_TEST_SET_EXACTNESS.md` | YES — Check 3 says "Verify EXIT_CODE for each test command" | Mentions `EXIT_CODE_MISSING` flag but does NOT define blank/non-numeric/conflicting cases |
| `REQUIRED_TEST_SET_EXACTNESS_TEMPLATE.md` | YES — table has `EXIT_CODE` column | Column present but no validation regex defined |
| `SCRIPT_SPEC_check_gate_package.md` | YES — `verify_raw_output_exit_codes()` function spec | Spec only; script does not exist as executable code |
| `06_R2_ACTIVE_PROOF.md` | Implicitly (exit codes part of proof) | Not explicit |

**Gap:** No file defines the exact regex `^EXIT_CODE:0\s*$`. No file names flags for `EXIT_CODE_BLANK`, `EXIT_CODE_NON_NUMERIC`, `EXIT_CODE_CONFLICTING`, or `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW`. The M77-P05A blank `EXIT_CODE:` line would NOT have been caught by mechanical check.

---

## Q2 — Which files currently mention warning/output scans?

| File | What it says |
|---|---|
| `22_WARNING_OUTPUT_AUDIT.md` | Full step definition; grep pattern defined; classification table |
| `WARNING_OUTPUT_AUDIT_TEMPLATE.md` | Template for producing the audit artifact |
| `15_FINAL_PACKAGE_AUDIT.md` | Gate 4.1 appended section references warning audit findings |
| `03_EVIDENCE_CONSISTENCY.md` | Check 5 table has `post-pass error?` column — but this is a prose check, not a defined detection rule |
| `SCRIPT_SPEC_check_gate_package.md` | `verify_raw_output_exit_codes` but does NOT scan for post-PASS errors |

**Gap:** The warning scan grep pattern in `22_WARNING_OUTPUT_AUDIT.md` includes `ENOENT` in the pattern, but there is no explicit rule that an ENOENT occurring **after** a PASS summary line is BLOCKING. The audit classifies by warning type, not by position. A reviewer could classify a post-PASS ENOENT as `REQUIRES_FOLLOWUP` (non-blocking) and not be structurally wrong under current rules.

---

## Q3 — Which files currently mention post-PASS uncaught errors?

| File | Mention? |
|---|---|
| `03_EVIDENCE_CONSISTENCY.md` | YES — Check 5 has `post-pass error?` column in RAW_TEST_OUTPUT_TABLE |
| `22_WARNING_OUTPUT_AUDIT.md` | Mentions ENOENT in scan pattern but does NOT define "post-PASS position" as a separate rule |
| `WARNING_OUTPUT_AUDIT_TEMPLATE.md` | No mention |
| `SCRIPT_SPEC_check_gate_package.md` | No explicit post-PASS detection function |

**Gap:** There is NO defined flag `POST_PASS_UNCAUGHT_ERROR`. There is no mechanical rule saying "if Error: or ENOENT appears AFTER a PASS line, this is BLOCKING." The column in Check 5 is a manual reviewer check — if a reviewer does not examine the position of the error, they can classify it non-blocking.

---

## Q4 — Which files currently require Required Test Set Exactness?

| File | What it says |
|---|---|
| `23_REQUIRED_TEST_SET_EXACTNESS.md` | Step definition — mandatory for GATE_STANDARD and GATE_FULL |
| `GATE_PROFILES.md` | Lists `REQUIRED_TEST_SET_EXACTNESS_*` as YES for GATE_STANDARD and GATE_FULL |
| `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` | GATE_FULL: `required_always` includes `REQUIRED_TEST_SET_EXACTNESS.md`; GATE_STANDARD: only in `required_conditional` (condition: `raw_output_present == true`) |
| `STATE_MACHINE.md` | State `REQUIRED_TEST_SET_EXACTNESS_*` defined for GATE_STANDARD/GATE_FULL |

**Gap (confirmed):** GATE_PROFILES.md says `REQUIRED_TEST_SET_EXACTNESS_*` is YES for GATE_STANDARD. REQUIRED_PROOF_FILES_BY_PROFILE.yaml lists it as `required_conditional` for GATE_STANDARD. This is an inconsistency — the YAML is weaker than the prose.

---

## Q5 — Which files currently require proof files by profile?

| File | What it says |
|---|---|
| `REQUIRED_PROOF_FILES_BY_PROFILE.yaml` | Machine-readable YAML with per-profile required_always, required_conditional, not_applicable |
| `PROOF_FILE_REQUIREMENTS.md` | Prose rules for proof files |
| `GATE_PROFILES.md` | Profile-specific required states list |
| `PACKAGE_MANIFEST_TEMPLATE.md` | Template includes profile proof files section |

**Gap:** No automated check verifies the YAML against the prose. GATE_STANDARD in YAML is missing `REQUIRED_TEST_SET_EXACTNESS.md` from `required_always`. This creates a path where a GATE_STANDARD run skips REQUIRED_TEST_SET_EXACTNESS without a NOT_APPLICABLE file.

---

## Q6 — Is there an executable package checker, or only SCRIPT_SPEC_check_gate_package.md?

**Answer: ONLY SCRIPT_SPEC_check_gate_package.md. No executable script exists.**

The file at `tools/check_gate_package.py` does not exist. The spec in `SCRIPT_SPEC_check_gate_package.md` is detailed (defines functions, updated main()) but remains a specification document. This means:

- There is no way to mechanically run a check against a package
- All checks rely on the agent/reviewer reading and following the prose
- A reviewer who skips checking post-PASS ENOENT has no automated backstop

---

## Q7 — Are Gate 4.1 extra audit states integrated into transition rules, or only listed as optional?

| State | Transition rule status |
|---|---|
| `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND` | Routes to `FIX_CYCLE_IN_PROGRESS` — YES, integrated |
| `REQUIRED_TEST_SET_EXACTNESS_FAIL` | Routes to `FIX_CYCLE_IN_PROGRESS` — YES, integrated |
| `PRODUCTION_CALLER_AUDIT_FAIL` | Routes to `FIX_CYCLE_IN_PROGRESS` — YES, integrated |
| All other extra audit FAIL states | Individual routing defined in TRANSITION_RULES.md |

**Gap:** Transition rules define the routing for individual fail states. However, there is NO explicit "pre-PASS barrier" that blocks `GATE_PASS_FOR_HANDOFF` if ANY required extra audit is in FAIL state. The current rule only requires:
- R5_COMPLETE before GATE_VERDICT_ISSUED
- enforcement_audit_result = PASS or NOT_APPLICABLE for GATE_PASS_FOR_HANDOFF

It does NOT explicitly require `WARNING_OUTPUT_AUDIT_PASS` or `REQUIRED_TEST_SET_EXACTNESS_PASS` to be present before PASS can be issued. An agent that runs the audits, gets BLOCKING findings, and then issues PASS anyway has no explicit transition barrier stopping it.

---

## Q8 — Can a package reach terminal PASS while a required extra audit state is FAIL or missing?

**Answer: TECHNICALLY YES — this is the critical gap.**

The terminal PASS states (e.g., `GATE_FULL_PASS_HANDOFF_COMPLETE`) require:
- All required FULL states "must be recorded"
- `final_package_audit_result: PASS`, `canonical_handoff_audit_result: PASS`

But "must be recorded" does not prevent a state from being recorded as FAIL while PASS is still issued. The constraint in `TRANSITION_RULES.md` for `GATE_FULL_PASS_HANDOFF_COMPLETE` says "all required FULL states must be recorded" — not "all required FULL states must be recorded as PASS."

An agent could technically:
1. Run `WARNING_OUTPUT_AUDIT` → `WARNING_OUTPUT_AUDIT_BLOCKING_FOUND`
2. Record the FAIL state
3. Proceed to issue PASS anyway (the FAIL state is "recorded")

The gate relies on reviewers following routing rules honestly. There is no automated barrier that reads CURRENT_STATE.yaml and confirms all required states are in PASS/OK/NOT_APPLICABLE before allowing the terminal state.

---

## Q9 — Are proof files required to be included in the export package, or only produced locally?

**Answer: Required to be included, but enforcement is weak.**

`PROOF_FILE_REQUIREMENTS.md` states: "Place a copy or a reference under: `reports/<task_area>/gate_used/`"

`12_PASS_HANDOFF.md` lists what must be included in the package but does NOT list:
- All required Gate 4.1 proof files (WARNING_OUTPUT_AUDIT.md, REQUIRED_TEST_SET_EXACTNESS.md, etc.)
- Raw test outputs
- `package_file_hashes.txt`
- `GATE_PACKAGE_VALIDATION_REPORT.md` (this does not exist yet)

`15_FINAL_PACKAGE_AUDIT.md` only verifies files listed in PACKAGE_MANIFEST.md. If an agent omits a required proof file from PACKAGE_MANIFEST.md, it will pass Step 15 without detecting the gap.

**Gap:** There is no exhaustive "required files list" that Step 15 checks independently of what the agent put in the manifest. The manifest is agent-populated, so an agent can omit required files and pass the audit.

---

## M77-P05A Failure Classification

**Classification: MIXED**

Evidence:

1. **GATE_MISSING_EXECUTABLE_ENFORCEMENT** — The primary structural gap: no executable `check_gate_package.py` exists. A script running against the package would have caught blank `EXIT_CODE:` mechanically. No checker = relies entirely on human/agent reading discipline.

2. **GATE_MISSING_CHECK** — No `POST_PASS_UNCAUGHT_ERROR` flag exists. The ENOENT error appearing after the Jest PASS line could have been classified as `REQUIRES_FOLLOWUP` (non-blocking) and still technically comply with the gate. The gate does not define position-based blocking for errors.

3. **GATE_RULE_AMBIGUITY** — `EXIT_CODE_BLANK` is not defined as a flag. The existing `EXIT_CODE_MISSING` flag applies when there is no EXIT_CODE line. A line reading `EXIT_CODE:` (blank value) is ambiguous — it has an EXIT_CODE line, but the value is blank. Current rules do not explicitly cover this case.

4. **GATE_NOT_FOLLOWED_STRICTLY** — If Gate Full had been run and Warning Output Audit had been run against the raw output, an ENOENT in the output should have been flagged. The post-PASS ENOENT contradicts "tests ran cleanly" claims. A strict reviewer would have caught this under existing rules.

**Verdict: MIXED** — Part compliance failure (the gate's existing rules, strictly followed, would have caught the ENOENT warning), part missing enforcement (blank EXIT_CODE and post-PASS position detection are genuine gaps), part missing executable (no script to catch it mechanically).

The primary prevention gap is the absence of an executable checker. A passing CI/CD check would have blocked the package.
