# Fixture: not_applicable_with_reason

**Profile:** GATE_STANDARD
**Risk tier:** D2
**Task kind:** normal_impl
**Expected verdict:** PASS

## Why this fixture exists

Gate 5.2-R1 P03: Validates the happy path of NA proofs — every required `_NOT_APPLICABLE.md`
file is present AND contains a substantive reason. Selector minimum profile for D2/normal_impl
is GATE_STANDARD, so this is the correct profile choice for the test.

## Setup

GATE_STANDARD package with all four required `_NOT_APPLICABLE.md` files present, each with a
substantive reason. All other GATE_STANDARD required files are present (sourced from
happy_path_gate_full).
