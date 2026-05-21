# Fixture: consumer_api_bypass

## Setup

- Task: "Add `getLatestMemory(userId)` to `memoryRepository.js`"
- Test file: `tests/memory/getLatestMemory.test.js`
- Test asserts:
  ```js
  const row = await db.query('SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', [userId]);
  expect(row.content).toBe('expected content');
  ```
- The test queries the DB directly — it does NOT call `memoryRepository.getLatestMemory(userId)`
- `COLD_REVIEW_ACTIVE_PROOF_AUDIT.md` says: "Consumer API tested: YES"
  (incorrect — the test bypasses the consumer API)
- `CONSUMER_API_PROOF_AUDIT.md` shows:
  - Consumer API: `memoryRepository.getLatestMemory`
  - Tested through consumer path: NO
  - Raw inspection only: YES
  - Verdict: CONSUMER_API_PROVEN (incorrect — should be RAW_ONLY)

## Expected checker behavior

`check_gate_package.py` must return **FAIL** with:

```
[FAIL] Consumer API bypass: tests use raw DB inspection but not consumer API
       Consumer API: memoryRepository.getLatestMemory
       CONSUMER_API_PROOF_AUDIT.md verdict: CONSUMER_API_PROVEN (incorrect)
       Test file shows: db.query('SELECT * FROM memories...') — not getLatestMemory()
       Invariant violated: consumer_api_tested_through_consumer_path
[FAIL] CONSUMER_API_PROOF_AUDIT.md contains incorrect verdict:
       Actual test assertion: raw SQL query
       Consumer API: memoryRepository.getLatestMemory()
       Correct verdict: RAW_ONLY (not CONSUMER_API_PROVEN)
```

## Expected invariant

`consumer_api_tested_through_consumer_path`

## Why this matters

The raw DB query proves the DB row exists. It does not prove that `getLatestMemory()`
handles the ORDER BY correctly, applies any row-level transforms, or raises the correct
error when no memory exists. A future change to the repository method could break all
callers without this test failing.
