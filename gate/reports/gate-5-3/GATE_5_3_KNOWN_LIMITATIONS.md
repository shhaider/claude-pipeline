# Gate 5.3 — Known Limitations

## New limitations introduced by Gate 5.3

1. **Independence is policy-enforced, not mechanically verifiable.**
   The checker reads the "Independence achieved: <true|false>" line as plain text. It cannot prove a fresh subagent actually ran the auditor. An operator who labels their own session as "fresh-subagent" can pass the check.
   Mitigation: rely on operator vigilance and the standing usage rule.

2. **Schema validation is regex-based.**
   `_FINAL_AUDITOR_VERDICT_RE` and `_FINAL_AUDITOR_RERUN_RE` use multi-line regex with markdown-bullet tolerance. A structurally valid but semantically empty report (e.g., `REASON:\n- ` with no actual prose) could pass.
   Mitigation: upstream reviewers (R1–R5) — not the schema check — are responsible for substantive content review.

3. **Lane D and other prior packages will fail under 5.3.**
   The Lane D production package built before Gate 5.3 fails the new auditor check. This is not a regression: Lane D had no FINAL_PACKET_AUDITOR_REPORT.md because the file did not exist as a concept. Lane D needs a follow-up to add the auditor report. All other Lane D checks continue to pass under 5.3 (61 passing under 5.3, with only the 2 new auditor-related failures — confirmed by cross-check).

4. **HUMAN_DECISION_REQUIRED handoff cross-check is token-based.**
   `_FINAL_AUDITOR_HANDOFF_BLOCKED_TOKENS` searches for `BLOCKED`, `HUMAN_DECISION`, `REQUIRES_HUMAN`, or `NEEDS_HUMAN`. A handoff that uses a different vocabulary may be flagged inconsistent even when the operator intent matches the verdict.
   Mitigation: standardize handoff vocabulary in templates.

5. **`RERUN_FROM:BEGINNING` cross-check is token-based.**
   `_FINAL_AUDITOR_HANDOFF_READY_TOKENS` searches for `READY`, `MERGED`, `VERIFIED`, `PASS_HANDOFF_COMPLETE`, `ACCEPTED`. False positives possible if handoff prose uses these tokens in non-status contexts.
   Mitigation: structured handoff format (out of scope for 5.3).

## Inherited Gate 5.3 backlog from 5.2-R1 acceptance

These were acknowledged in `GATE_5_2_USAGE_RULE.md` and remain open:

1. **Display-only path-trim bug** in `dirty_paths_from_git_status` (chops one extra char from dirty paths in failure messages). Cosmetic only — classification still correct.
2. **No fixtures for `EXIT_CODE_CONFLICTING` or `EXIT_CODE_NON_NUMERIC`.** Code paths exist but are unexercised by the self-test suite.
3. **`SUMMARY_DOC_PATTERNS` glob is broad** (`*SUMMARY*.md`) — a doc that legitimately quotes `EXIT_CODE:0` in a code example could trigger `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` falsely.
4. **Domain-addendum file existence is not enforced** for `GATE_FULL_PLUS_DOMAIN_ADDENDUM` — the YAML template `DOMAIN_ADDENDUM_{name}.md` is silently skipped.
5. **NA-reason heuristic** is keyword + length-based, not semantic.
6. **Prose-scan exhaustiveness** for output-contract negation — the negation set is not exhaustive (e.g., "did not detect" passes; "didn't detect" with apostrophe fails).
7. **Fence-aware EXIT_CODE scanning** — `EXIT_CODE:0` inside fenced code blocks in summary docs is not distinguished from real status claims.

## Documented but not fixed in 5.3

These are by-design simplicity choices for the auditor:

- The auditor prompt is intentionally short. We are not adding bullet points, escape hatches, or pre-checks. If a class of issue is recurring, fix the upstream reviewer (R1–R5) — not the auditor.
- The auditor cannot be replaced by a more elaborate prompt-only review. The independence requirement (fresh subagent / Tier 3 model) is part of the contract.
- Non-export GATE_LITE NA path is allowed by design. If the package is for an internal docs-only consumer, the marginal value of the auditor is low and the NA-with-substantive-reason path stays open.
