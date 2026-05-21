# Gate 5.4 — Standing Usage Rule

**Status:** Active as of 2026-05-01
**Supersedes:** Gate 5.3 only for the additions listed here. Gate 5.2-R1 and Gate 5.3 rules still apply unless this file hardens them further.

## What is new in Gate 5.4

1. Final Packet Auditor reports must use a structured YAML/JSON fenced block. Legacy regex-only prose reports are rejected.
2. Final-auditor independence is mechanically checked against declared provenance metadata. This is not trusted runtime proof unless the environment supplies trusted session IDs.
3. `GATE_FULL_PLUS_DOMAIN_ADDENDUM` now requires non-empty `domain_addenda`, valid addendum names, source definitions under `domain_addenda/`, and exact package proof files.
4. EXIT_CODE parsing is fence-aware. Fenced `EXIT_CODE:0` does not count as raw proof.
5. NOT_APPLICABLE reasons reject placeholder, invisible, and generic-only text.
6. Warning audits accept a structured verdict block and have stronger fallback prose scanning.

## Final-auditor limitations

- Independence is verified only against declared metadata.
- The checker can detect missing/conflicting provenance and unsupported contexts.
- The checker cannot prove that a fresh subagent/session actually ran unless the runtime provides trusted IDs.
