# Runtime State Resume Addendum

This addendum applies when a gate run touches durable runtime state, workflow checkpointing, milestone tracking, or resume/skip semantics for a long-running orchestration.

Checks required by this addendum:
- the package distinguishes status-only/advisory reads from controlled-skip semantics in the source comment block, the handoff, and the operational limitation report;
- the package names the SOLE skip authority and proves it is unchanged (or, if changed, that change is the deliberate scope of the task and is bounded);
- artifact provenance / staleness / fingerprint concerns that are NOT solved by the change are explicitly deferred with a target sprint or milestone (e.g. M70);
- the output-contract surface (new opts, new output fields, new log families) is enumerated in the change and exercised by tests through the production entry point;
- forbidden-file edits (state-machine internals, migration files, repository module) are confirmed clean;
- regression tests covering the existing skip authority (e.g. file-checkpoint-based opts.resume) still pass.
