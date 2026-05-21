# Evidence Integrity Addendum

This addendum applies whenever a gate run produces evidence that survives the conversation (signout zips, persisted reports, SHA-cited claims).

Checks required by this addendum:
- generated reports, raw test outputs, signout zips, and temporary manifests must NOT be committed to any repo;
- all evidence lives in /tmp/<task>/ on the execution host and/or in an exported zip outside any worktree;
- post-commit hook side-effects must be filtered out of commits (verify via git show --stat HEAD immediately after each commit);
- SHAs cited in reports must be re-verifiable by anyone with VPS or origin access (each claim points to a deterministic git rev-parse query);
- the package zip's SHA256 must be computed and recorded in the final report.
