# Step 32 — Concurrency Assumptions Audit

**State machine:** Write `current_state: CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS` to CURRENT_STATE.yaml at entry.

**Mandatory when the task involves any of the following:**
- State persistence or checkpointing
- Queue or dispatch systems
- Branch/worktree governance
- Multi-agent coordination
- Checkpoint/resume behavior
- Locks or mutexes
- Cache or in-memory store systems
- Any system where two callers might write the same resource concurrently

**Skip when:** No shared mutable state, no concurrent callers, no queues or locks. Produce `CONCURRENCY_ASSUMPTIONS_AUDIT_NOT_APPLICABLE.md`.

---

## Why this step exists

A system that works correctly when used sequentially may fail silently when two agents use it concurrently. The gate cannot prevent all concurrency bugs, but it can prevent the handoff from overclaiming concurrency safety that was never implemented or tested.

---

## Output file

Copy `CONCURRENCY_ASSUMPTIONS_AUDIT_TEMPLATE.md` to `reports/<task_area>/CONCURRENCY_ASSUMPTIONS_AUDIT.md`.

---

## Checks

### Check 1 — Single-process or multi-process?

Is this system ever used by:
- One process at a time? (sequential safe — no concurrency concern)
- Multiple processes simultaneously? (concurrency concern — must be addressed)
- Multiple async callers within one process? (limited concurrency concern — depends on await discipline)

### Check 2 — Sequential safe?

If the system is designed for sequential use only:
1. Is this stated explicitly in the code or documentation?
2. Is there any code path that could allow concurrent access?
3. Is there a runtime assertion or lock that enforces sequential use?

### Check 3 — Concurrent safe?

If the system claims to support concurrent access:
1. Is there a lock, mutex, or transaction boundary around the critical section?
2. Is the lock tested with concurrent callers?
3. Are there any TOCTOU (time-of-check/time-of-use) vulnerabilities?

### Check 4 — Idempotent?

If the operation might be retried:
1. Is the operation idempotent (safe to run twice with the same result)?
2. If not idempotent: is there a deduplication mechanism?

### Check 5 — Race condition risks

For any write operation on shared state:
1. What happens if two callers write simultaneously?
2. What happens if a reader reads while a writer is writing?
3. Is the failure mode silent (data corruption) or loud (error/exception)?

### Check 6 — What is explicitly not guaranteed?

If the system does not guarantee a concurrency property, this must be stated. Examples:
- "This module is not concurrent-safe. Only one process should call it at a time."
- "This queue does not guarantee delivery-once under concurrent consumption."
- "This cache may return stale values if written concurrently."

---

## Hard rule

If concurrency is not guaranteed, say so explicitly in the handoff. The handoff must not claim behaviors that depend on concurrency properties that were never implemented or tested. Prevent overclaiming — not all concurrency bugs.

---

## Routing

| Outcome | State to write | Next file |
|---|---|---|
| Concurrency assumptions documented and safe | `CONCURRENCY_ASSUMPTIONS_AUDIT_PASS` | Continue |
| Undocumented race conditions or incorrect guarantees | `CONCURRENCY_ASSUMPTIONS_AUDIT_FAIL` | `FIX_CYCLE_IN_PROGRESS` |
