# Gate 5.2 Baseline

- Canonical gate path: `/Users/syedhaider/Downloads/gate`
- Accepted Gate 5.1 snapshot: `~/Downloads/gate_5_1_canonical_accepted_2026-05-01.zip`
- Accepted Gate 5.1 zip SHA256: `adb0cd81ce51bbc06e81abeac3bcf18bd8f3c08b55b316fc9963c2fcf505246f`
- Backup path: `/Users/syedhaider/Downloads/gate_backup_pre_5_2_20260501T113854Z`
- Baseline captured at: `2026-05-01T11:38:54Z`

## Inventory Summary

- File inventory command: `find . -maxdepth 4 -type f | sort`
- Files discovered within depth 4: `229`
- Fixture directories under `tests/fixtures`: `8`
- Canonical gate package is a filesystem directory, not a git worktree.

## Current Recorded Version

- Entry point title: `Gate — Entry Point (Gate 5.1)` in `00_START.md`
- Standing rule doc: `GATE_5_1_USAGE_RULE.md`
- Checker banner/help: `Gate 5.1 package checker`

## Requested Baseline Commands

- `pwd` from gate root: `/Users/syedhaider/Downloads/gate`
- `python3 --version`: `Python 3.14.3`
- `python3 tools/check_gate_package.py --help`: succeeded, checker exists
- `python3 tests/test_check_gate_package.py`: succeeded, tests file exists

## Baseline Self-Test Result

- Exit code: `0`
- Summary: `7 passed, 0 failed`
- Covered baseline cases:
  - `blank_exit_code`
  - `post_pass_enoent`
  - `missing_raw_output`
  - `manifest_stale_self_size`
  - `missing_gate_source`
  - `missing_required_proof_file`
  - `happy_path`

## Known Gaps To Address In Gate 5.2

1. Stale-report / output-contract contradiction is only manual/prose, not executable.
2. Wrong gate-profile detection is not mechanically enforced.
3. `EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW` exists in prose but is not implemented.
4. `reports/gate-5-1-upgrade/GATE_5_1_DIFF.patch` is corrupt and unusable as rollback evidence.
5. Existing Gate 5.1 executable checks must not regress while hardening the package.
