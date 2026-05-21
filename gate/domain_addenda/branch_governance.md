# Branch Governance Addendum

This addendum applies when a gate run mutates a shared canonical branch (force-push, archive creation, branch reclassification, branch authority change).

Checks required by this addendum:
- the prior tip of the canonical branch must be preserved as a named archive ref before any force-push;
- only --force-with-lease may be used; plain --force is prohibited;
- preservation must be verified (e.g., git rev-parse origin/<archive>) before the force-push;
- new canonical-branch SHA must be cited identically across the package (PACKAGE_MANIFEST, CLAIMS_LEDGER, EVIDENCE_LEDGER, FINAL_PACKET_AUDITOR_REPORT);
- branch reclassification (e.g., "dev becomes experimental") must be documented in maintained docs (AGENTS.md, README.md, doc-truth) on the new canonical branch;
- a notice file must inform any agent operating on a reclassified branch.
