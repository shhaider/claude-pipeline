# GATE_EFFECTIVENESS_LOG — NOT_APPLICABLE

This log is NOT_APPLICABLE for the system-gap-analyst gate run.

**Reason.** Per `REQUIRED_PROOF_FILES_BY_PROFILE.yaml`, the gate effectiveness log is required only under `GATE_FULL`; for the selected `GATE_STANDARD` profile it appears in `not_applicable_proof_required`, meaning a substantive NOT_APPLICABLE marker is the expected output. The effectiveness log accumulates cross-run signals (catch-rate of blockers, false-positive rate of audits, time-to-pass per profile) and is only useful when the gate run is part of a longer-running quality-feedback program against the same gate version. This is the first gate run on this task area on this branch, with a single cycle that produced zero blocking findings — there is no historical effectiveness signal to log. The NOT_APPLICABLE marker honestly records why no log body was emitted.
