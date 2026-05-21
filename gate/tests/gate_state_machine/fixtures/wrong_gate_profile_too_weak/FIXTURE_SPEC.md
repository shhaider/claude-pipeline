# Fixture: wrong_gate_profile_too_weak

## Setup

- `GATE_PROFILE_SELECTION.md` contains `gate_profile: GATE_LITE`
- `CURRENT_STATE.yaml` records `gate_profile: GATE_LITE` and `risk_tier: D2-hot`
- The task's file-touch map includes `runtime_lane_registry.js` — a listed hot file
- `GATE_PROFILE_SELECTOR.md` clearly states: hot file contact → minimum GATE_FULL
- `GATE_PROFILE_SELECTION.md` shows `profile_override_required: false` (error — should be true)
- The package was passed at `GATE_LITE_PASS_HANDOFF_COMPLETE`

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Gate profile too weak for risk tier:
       Selected profile: GATE_LITE
       Risk tier: D2-hot
       Hot file in touch map: runtime_lane_registry.js
       Required minimum profile: GATE_FULL
       Invariant violated: gate_profile_not_weaker_than_risk_tier
[FAIL] profile_override_required not set despite profile weaker than risk tier
       GATE_PROFILE_SELECTION.md: profile_override_required: false
       Expected: profile_override_required: true (with human acknowledgment)
```

## Expected invariant

`gate_profile_not_weaker_than_risk_tier`

## Why this matters

A hot file task run through GATE_LITE skips: prompt contract review, production caller
audit, consumer API proof audit, warning output audit, CTO operator insight review,
and 12 other checks. The package will appear to pass while being fundamentally under-
scrutinized. This invariant ensures the profile cannot be silently weakened for tasks
that require full gate depth.
