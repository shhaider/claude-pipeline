# Fixture Spec: weak_profile

**Scenario:** GATE_PROFILE_SELECTION.md selects GATE_LITE for a merge verification task.
Merge verification is a D3 task (per GATE_PROFILE_SELECTOR.md escalation triggers) and
requires GATE_FULL as the minimum profile.

**Expected checker result:** FAIL — profile too weak for task type. Gate escalation trigger
"Task involves branch merge verification" requires at least GATE_FULL.

**Why this matters:** Weak profile selection is how agents escape the stricter checks.
The checker validates profile selection independently.
