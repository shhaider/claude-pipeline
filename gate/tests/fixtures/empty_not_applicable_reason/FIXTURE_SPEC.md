# Fixture: empty_not_applicable_reason

**Profile:** GATE_STANDARD
**Risk tier:** D2
**Task kind:** normal_impl
**Expected verdict:** FAIL with `NOT_APPLICABLE_REASON_MISSING`

## Why this fixture exists

Gate 5.2-R1 P03: A NOT_APPLICABLE proof file that exists but contains no substantive
reason (e.g. only a heading) is no longer accepted. The body must contain a real
explanatory reason — either an NA keyword (because, audit-only task, no tests run, ...)
or >80 characters of non-template prose.

## Setup

GATE_STANDARD package with all four required `_NOT_APPLICABLE.md` files present, but
the GATE_EFFECTIVENESS_LOG_NOT_APPLICABLE.md file contains only a heading.
