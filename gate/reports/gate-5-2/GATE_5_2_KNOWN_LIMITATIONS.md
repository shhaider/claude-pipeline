# Gate 5.2 Known Limitations

- A pre-5.1 Gate 5 baseline was not available, so only the `Gate 5.1 -> Gate 5.2` diff artifact could be generated mechanically.
- Domain-addendum placeholder expansion (`DOMAIN_ADDENDUM_{name}.md`) was not extended in this packet; Gate 5.2 hardening focused on the requested gaps and regression coverage.
- The checker still writes a validation report after each run, so the missing-report final-mode test removes the report fixture before execution to preserve the negative case.
