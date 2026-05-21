# Gate effectiveness log

**Task area:** `system_gap_analyst`

## What the gate caught (cycle-1 → cycle-2)

1. **Substantive bug: `--max-tokens` / `--temperature` unsupported by `claude --print`.** The judge's fix #6 in cycle-1 verdict flagged this. The coder verified via `claude --help` and removed both flags. **High-value catch — would have caused every live run of the new nodes to exit non-zero.**

2. **Missing gate package.** Cycle-1 submission had no process artifacts. Cycle-2 produced initial ledgers and R1–R5 reports. While the ledgers themselves are bureaucratic, the discipline of writing R1–R5 forced re-examination of: (a) which acceptance criteria were actually met, (b) which were N/A and why, (c) what risks remained. That re-examination did not surface new bugs but did surface the lens-name drift risk now logged in R4 / PROMPT_CONTRACT_REVIEW.

## What the gate caught (cycle-2 → cycle-3)

3. **File-name mismatch with `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`.** Cycle-2 used R1_*..R5_* names; the profile spec requires COLD_REVIEW_* names. Renamed.
4. **Missing structured fenced YAML in FINAL_PACKET_AUDITOR_REPORT.md.** Cycle-2 had prose only; the checker requires a `final_packet_auditor:` fenced YAML block with verdict/reason/blockers/required_fix/rerun_from/independence keys. Cycle-3 rewrites it.
5. **Independence requirement.** Cycle-2 self-authored the auditor report; the checker requires the auditor to be a fresh subagent / fresh session for GATE_STANDARD+. Cycle-3 spawns a fresh subagent to perform the audit.
6. **17 missing required-always proof files for GATE_FULL.** Authored in cycle 3.
7. **Missing `gate_used/` or `gate_hash.txt`.** Cycle-3 produces `gate_hash.txt`.
8. **Missing `package_file_sizes.txt`, `package_file_hashes.txt`, `git_status_final.txt`.** Cycle-3 produces.

## What the gate did NOT catch

- The R1–R4 cold-review reports in cycle-2 (before rename) all returned PASS, but the package was structurally non-compliant. The cold reviews did not check file-naming against `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`. Suggested gate-effectiveness fix: have R5_ADJUDICATION include a checker-tool invocation step before reaching its synthesis verdict.

## Effectiveness summary

The gate is most effective when:
- The checker tool (`tools/check_gate_package.py`) runs at every cycle. Coders that skip this step spend cycles producing prose that the checker would reject in seconds.
- The checker output is treated as the spec, not the human prose in `00_START.md`.

The gate is least effective when:
- A coder writes prose reports without first running the checker. (Cycle-1 and cycle-2 both did this.)
- The cold-review panel does not include an automated check step.

## Verdict

**Gate caught 1 substantive bug + 6 process defects across 3 cycles. Recommended improvement: cold-review panel should include a checker run as an R-step before synthesis.**
