# Concurrency Assumptions Audit
Sprint 3 -- SimpleAgent emdash Bridge
Gate 5.4 -- Step 32

State: CONCURRENCY_ASSUMPTIONS_AUDIT_IN_PROGRESS

---

## Applicability

The bridge server runs in a daemon thread and serves HTTP requests. The `decide()` function reads on-disk state files. Concurrency is relevant because:
- The HTTP server runs in a separate thread from the main application
- Multiple HTTP requests could arrive concurrently (though unlikely for localhost dev use)
- The file system (RUN.json files) is shared mutable state (other processes may write to it)

---

## Check 1 -- Single-process or multi-process?

The bridge server runs as a daemon thread within the SimpleAgent process. It is single-process, multi-threaded. The HTTP server (`HTTPServer`) handles requests sequentially by default (one at a time, not using `ThreadingMixIn`).

However, the `GovernedFSMService` (a separate component) may write to `RUN.json` files while the bridge reads them. This is a multi-process read/write scenario.

---

## Check 2 -- Sequential safe?

The HTTP server is sequential (no `ThreadingMixIn`). Each request is handled one at a time. No concurrent request handling within the bridge.

For file reads: `decide()` uses `run_file.read_text(encoding="utf-8")` which reads the entire file atomically at the OS level (single `read()` call for small JSON files). This is safe for concurrent reads.

For file writes by other processes: If `GovernedFSMService` writes a `RUN.json` while `decide()` is reading it, Python's `read_text()` will either read the old content or the new content (not a partial write), because:
- The JSON files are small (< 4KB)
- POSIX guarantees atomic writes for small files when using `write()` (not guaranteed for all write patterns)
- In practice, the write happens via `Path.write_text()` in `StateStore`, which uses `open()` + `write()` + `close()`

Risk: A partially-written `RUN.json` could cause `json.JSONDecodeError`. This is handled by the `except (OSError, json.JSONDecodeError)` clause in `decide()` at hook_server.py:50-51, which logs a warning and skips the unreadable file.

---

## Check 3 -- Concurrent safe?

No explicit locks. No mutexes. The bridge relies on:
1. Sequential HTTP request handling (no ThreadingMixIn)
2. OS-level file read atomicity for small files
3. Error handling for unreadable files (`json.JSONDecodeError` catch)

This is adequate for the current use case (localhost, single consumer, sequential requests).

---

## Check 4 -- Idempotent?

`decide()` is a pure read operation. It can be called any number of times with the same result (given the same on-disk state). It is idempotent.

---

## Check 5 -- Race condition risks

| Scenario | What happens | Failure mode |
|---|---|---|
| Two HTTP requests arrive simultaneously | HTTPServer handles them sequentially | No race -- requests are serialized |
| GovernedFSMService writes RUN.json while decide() reads it | decide() reads partial/old/new content | JSONDecodeError is caught; file is skipped with warning (hook_server.py:50-51) |
| Multiple active runs with interleaved writes | decide() uses max() on last_updated field | Potential stale ordering if timestamps are identical, but this is extremely unlikely |

---

## Check 6 -- What is explicitly not guaranteed

The bridge code and documentation do NOT make concurrency guarantees. The following are NOT guaranteed:
- Thread-safe concurrent request handling (no ThreadingMixIn)
- Atomic consistency between multiple RUN.json reads within a single decide() call
- Linearizable state reads (a write between two reads in the same glob could give inconsistent results)

These non-guarantees are acceptable for the current use case:
- emdash sends one request at a time (provisioning is sequential)
- The glob + read pattern is consistent enough for the advisory gate use case
- The handoff correctly classifies this as INFRASTRUCTURE_READY_NOT_WIRED, not claiming production-grade concurrency

---

## Verdict

Concurrency assumptions are documented and safe for the current use case. No undocumented race conditions. No incorrect guarantees. The sequential HTTPServer and error-handling patterns are adequate for localhost single-consumer operation.

State: **CONCURRENCY_ASSUMPTIONS_AUDIT_PASS**
