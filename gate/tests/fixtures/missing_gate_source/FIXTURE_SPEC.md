# Fixture Spec: missing_gate_source

**Scenario:** Package claims gate was used but lacks both gate_used/ directory and gate_hash.txt.
A local path `/Users/syedhaider/Downloads/gate` is referenced in CURRENT_STATE.yaml as the
gate source — this is a local-path-only reference, not portable proof.

**Expected checker result:** FAIL — gate_used/ directory and gate_hash.txt both absent.

**Why this matters:** Without gate source proof, the reviewer cannot verify which version
of the gate was used. A local path is machine-specific and not transferable.
