# Fixture Spec: manifest_stale_self_size

**Scenario:** PACKAGE_MANIFEST.md lists itself as 0 bytes. This simulates the stale
self-size failure pattern where the manifest was written before its own content was
finalized (resulting in a recorded size of 0 at the time of the self-referential entry).

**Expected checker result:** FAIL — MANIFEST_SELF_SIZE_STALE

**Why this matters:** A manifest that lists itself as 0 bytes proves it was generated
before its content was complete. Any size claims in such a manifest are suspect.
