# Fixture: lite_profile_missing_risk_task

**Profile:** GATE_LITE
**Risk tier:** (intentionally absent)
**Task kind:** (intentionally absent)
**Expected verdict:** FAIL with `MISSING_RISK_TIER` and `MISSING_TASK_KIND`

## Why this fixture exists

Gate 5.2-R1 P02: Even GATE_LITE packages must declare `risk_tier` and `task_kind` so the
WRONG_GATE_PROFILE selector can mechanically detect a too-weak profile choice. Prior to
R1, Lite packages could omit these fields and slip through without selector validation.

## Setup

GATE_PROFILE_SELECTION.md declares only `gate_profile: GATE_LITE` with a rationale, but
omits `risk_tier:` and `task_kind:`.

The test invokes the checker without `--risk-tier` or `--task-kind` so the metadata must
come from the file (it doesn't), causing both flags to fire.
