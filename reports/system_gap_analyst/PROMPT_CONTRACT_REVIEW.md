# 19 — Prompt contract review

**Target:** `prompts/metabuilder/35_system_gap_analyst.md`
**Role:** `system_gap_analyst`
**Task kind:** `prompt_authoring` (mandates this review per gate profile).

## Contract checklist

| Criterion | Status | Notes |
|---|---|---|
| Role identity stated clearly | PASS | "You are the **system gap analyst**: an adversarial reviewer..." — single sentence, unambiguous. |
| Job boundary stated | PASS | "You are not the planner. You are not the implementer." Explicit boundary prevents scope creep. |
| Input expectations described | PASS | Names the packet contents the role will receive: intake decisions, research brief, codebase anchor. |
| Output schema specified | PASS | JSON shape provided with field names, types, and the eight-lens enum constraint. |
| Output strictness asserted | PASS | "Return VALID JSON ONLY — no preamble, no markdown fence, no commentary." |
| Schema enum constraints | PASS | "`lens` MUST be one of the eight named lenses, spelled exactly." |
| Empty-output path explicit | PASS | "Empty arrays are fine. If the framing is genuinely clean, return empty `blocking_gaps` and `advisory_gaps` and say so in `summary`." Avoids "I have nothing to say" silent failure. |
| Severity taxonomy defined | PASS | `blocking` vs `advisory` defined with usage guidance ("Use sparingly; if you flag everything blocking, nothing is."). |
| Anti-patterns called out | PASS | "Be specific. 'Add logging' is bad; 'the new /ingest endpoint has no request-id logging and will be impossible to debug in prod' is good." Concrete good/bad example. |
| Hallucination guard | PASS | "Do NOT speculate beyond what the packet says. If you cannot tell whether a gap exists, do not invent one." |
| Scope guard | PASS | "Do NOT propose alternative implementations or rewrite the plan." Prevents the analyst from overstepping into contract_writer's job. |

## Lens taxonomy review

All 8 lenses present with explicit descriptions:

1. infrastructure-assumed-but-not-mentioned ✓
2. silent-failure ✓
3. cross-cutting-concerns ✓
4. next-stage-prerequisites ✓
5. YAGNI-cut ✓
6. fake-completion ✓
7. architecture-smell ✓
8. developer-contract-completeness ✓

Each lens is named, defined in prose, and gives the model a concrete sense of what evidence triggers it. The lens names match the `LENSES` table in `nodes/system_gap_analyst.py` (verified by `test_gap_packet_lenses_are_the_metabuilder_eight`).

## Drift risk

The same 8 names appear in two places: this prompt file AND in the Python `LENSES` constant. R4.2 flags this as low-severity. Mitigation: the code-side list is asserted in tests; the prompt-side list is asserted here.

**Suggested non-blocking follow-up:** a test that opens the prompt file and asserts each of the 8 names appears. Tracked as future work, not blocking this gate.

## Output schema vs. node parser alignment

The node's `_coerce_finding` reads `lens`, `gap`, `recommendation` — matches the prompt's documented shape exactly. The node's parse of `blocking_gaps`, `advisory_gaps`, `summary` matches the prompt's top-level shape. **No misalignment.**

## What this prompt does NOT do (intentional)

- Does not include exemplars (few-shot). Acceptable: the role is adversarial reasoning over a fresh packet each time, and the schema + anti-pattern call-out give enough grounding without biasing toward specific gap types.
- Does not specify max-output size. Acceptable: the implicit `claude` CLI max governs; over-long outputs are bounded by the agent loop.

## Verdict

**PROMPT CONTRACT REVIEW: PASS.** Prompt is complete, role-bounded, schema-strict, and aligned with the consumer (node parser + contract_writer downstream). One non-blocking drift mitigation suggested.
