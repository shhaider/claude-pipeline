# Metabuilder port spec

This is the canonical reference for porting metabuilder's actual node logic
into this pipeline. Extracted read-only from `/home/claw/clawcodex/` on the
VPS on 2026-05-21.

The principle: **port faithfully, don't reimagine.** Where metabuilder has
N LLM calls in a node, this pipeline must have N LLM calls. Where
metabuilder has deterministic glue, port the deterministic glue. Where
metabuilder has prompt files (`*.md`), import them verbatim.

## Node-to-file map

| local node | metabuilder file(s) | one-line description |
|---|---|---|
| **intake** | `skills/metabuilder/intake/autonomous_software_resolver.js` | 7-decision autonomous resolver, Opus, JSON output with fallback heuristics |
| **research** | `prompts/04_research_lead.md` + `scripts/metabuilder/plan_self_upgrade.js:704` (`buildResearchPacket`) + `gatherRelevantExcerpts` | Codebase-grounded research with implementation-level findings |
| **plan** | THREE LLM calls in sequence: (a) `27_contract_writer.md` + `buildContractPacket`, (b) `10_pack_planner.md` + `buildPlannerPacket`. Plus adversarial pre-lanes: `35_system_gap_analyst.md` + `36_cto_orchestrator.md`. Plus `buildRevisionPacket` (revision loop) and `checkPlanCompleteness` (4-Correction). | What must exist + how it's staged, with adversarial gap-finding lanes |
| **code** | `11_implementation_builder.md` + `buildPromptExpansionPacket` (parallel per-stage). Plus `skills/metabuilder/core/softspot/coding_harness.js` for execution. | Two passes: prompt expansion (Opus, 8192 tok, parallel) then actual coder |
| **verify** | NOT a single LLM call. Ladder: `12_pack_reviewer.md` → `34_software_reasoning_reviewer.md` → 4 mandatory reviewers (`founder_judge`, `reliability_engineer`, `state_architecture_reviewer`, `security_blast_radius_judge`) → `08_executive_governance_reviewer.md` + governance_repair_loop → `19_release_gatekeeper.md`. | 5-role review ladder, governance repair loop (max 2 rounds), final gatekeeper |

## LLM parameters (canonical)

All planning roles in metabuilder route through `routeByTier(roleId, opts)`,
which reads `default_tier` from `skills/metabuilder/core/prompting/tier_registry.js`:

| tier | model | fallback | max_tokens | temperature |
|---|---|---|---|---|
| 1 | `claude-haiku-4-5-20251001` | (self) | 2048 | 0.2 |
| 2 | `claude-sonnet-4-6` | haiku-4-5 | 4096 | 0.3 |
| 3 | `claude-opus-4-6` | sonnet-4-6 | 8192 | 0.2 |
| 4 | `claude-opus-4-6` | sonnet-4-6 | 8192 | 0.2 (escalation-only) |

Role → tier:
- Tier 3 (Opus): `research_lead`, `contract_writer`, `pack_planner`, `cto_orchestrator`, `system_gap_analyst`, `software_reasoning_reviewer`, `executive_governance_reviewer`
- Tier 2 (Sonnet): `implementation_builder`, `pack_reviewer`, `release_gatekeeper`

Per-role overrides:
- `pack_planner` first call: 8192 tok
- `pack_planner` revision: 8192 tok + conditional escalate
- `implementation_builder` for prompt expansion: 8192 tok + force-escalate to Tier 3 / Opus (Sonnet was hallucinating paths at 8192 tok per a comment in plan_self_upgrade.js)

## Verbatim prompts

### intake

`skills/metabuilder/intake/autonomous_software_resolver.js` lines 65-83, built inline in JS:

```
You are a software development intake specialist. The user wants you to make ALL decisions for their task.

CONTEXT: ${JSON.stringify(partialPayload)}
HISTORY: ${histStr}

Resolve these 7 decisions. For each: value, one-sentence reasoning, confidence 0-1.
1. task_type — bug_fix / new_feature / refactor / test_addition / documentation / exploration
2. complexity_tier — 1 (trivial), 2 (moderate), 3 (complex)
3. scope_plan — single task or subphases? One sentence
4. risk_flags — array from: auth, db_schema, api_contract, llm_routing, concurrency, security
5. right_thing_answer — is this the right thing to build? One sentence
6. acceptance_criteria — array of 3 testable criteria
7. wiring_plan — which existing modules this touches

Respond with VALID JSON only:
{"decisions": [{"field":"task_type","value":"...","reasoning":"...","confidence":0.85}, ...]}
```

LLM params: `model=claude-opus-4-7`, `temperature=0.3`, `max_tokens=1000`, timeout 30s. Calls `http://127.0.0.1:4020/v1/chat/completions` directly (bypasses routeByTier).
Output schema: `{ decisions: [{field, value, reasoning, confidence}] }` — 7 entries.
Post-processing: strip ```json fences; merge into `resolvedPayload`; flag confidence < 0.7.
Wrap: on exception → `buildFallbackDecisions(partialPayload)` returns deterministic `HEURISTIC_DEFAULTS`.

### research

System prompt: `04_research_lead.md` (166 lines, file content used verbatim as system).

User message via `buildResearchPacket` (lines 704-754):

```
${lessonBlock}

## Planning Research Task

You are acting as research_lead for a MetaBuilder planning request.

**Initiative ID:** ${initiative.initiative_id}
**Planning request:** ${initiative.goals[0]}

**Your task:**
Research the current MetaBuilder codebase state relevant to this planning request.
Identify: what already exists, what is missing, what the key risks are.

**Important — implementation-level research:**
You must identify specific implementation details that an implementer would need:
- Exact function signatures (name, arguments, return shape)
- Default values that would change during extraction or refactoring (e.g., hardcoded max_tokens)
- Injectable seam patterns or test hooks that must be preserved
- Test runner conventions (e.g., which test framework, any shims or adapters)
- Policy table values (e.g., mandatory source classes for specific task_class values)
These details prevent silent regressions that high-level findings miss.

**Relevant source file excerpts (from the codebase):**
${excerpts}

**Scope constraints:**
- Focus only on what is directly relevant to the planning request above
- Do not research unrelated capabilities
- Limit your output to the most important 5-8 findings
- At least 2 findings must be implementation-level details (signatures, defaults, patterns)

**Output format:**
Return a JSON object:
{
  "evidence_summary": "2-3 sentence summary of findings",
  "key_findings": ["finding 1", "finding 2", ...],
  "implementation_details": ["detail 1: exact function signature or default value", ...],
  "gaps_identified": ["gap 1", "gap 2"],
  "confidence": "high|medium|low",
  "sources_consulted": ["file:line — what was found"]
}
```

Deterministic side-channel: `gatherRelevantExcerpts(planningRequest)` regex-extracts identifier tokens (snake_case, camelCase, PascalCase, ≥5 chars, capped at 8), greps `skills/` + `scripts/` for `function token|token: function|const token =|module.exports.*token`, picks up to 4 non-test files, embeds excerpts directly into the user message. This grounding step prevents file-path hallucination.

LLM params: Tier 3 — Opus, max_tokens=8192, T=0.2.
Output schema: per buildResearchPacket above + role prompt's reframing fields (`stated_goal, abstract_goal, generic_form`).
Post-processing: `extractJSON()` → `assertResearchGatePasses` (Source Selection Policy enforces minimum sources by task_class). Sets P05A milestone `research_done`. Checkpoint key: `research_lead`.

### plan

**Three LLM calls + adversarial pre-lanes.**

**3a. system_gap_analyst** (live mode only — line 2900): system prompt `35_system_gap_analyst.md` (Tier 3 / Opus). User message via `buildGapAnalysisPacket` applies 8 adversarial lenses: infrastructure assumed-but-not-mentioned, silent failure, cross-cutting concerns, next-stage prerequisites, YAGNI cut, fake completion, architecture smell, developer contract completeness.

**3b. cto_orchestrator** (live mode only — line 2919): system prompt `36_cto_orchestrator.md` (Tier 3 / Opus). User message via `buildCTOPacket`. Runs Phase A (no file reads) + Phase B (mandatory file reads). Blocking gaps merged via `mergeCTOBlockingGaps` into gap-analysis result.

**3c. contract_writer** (always — line 2937): system prompt `27_contract_writer.md` (Tier 3). User message via `buildContractPacket` — injects "GOAL ANCHOR" structured block (PRIMARY GOAL / SECONDARY / ANTI-GOALS / SUCCESS LOOKS LIKE) and gap-additions from adversarial lanes as MANDATORY deliverables.
Output: `{ contract_title, deliverables[{id,name,description,success_criteria[],source_goal}], ambiguity_flags[{goal,issue,assumed}], total_deliverables, verification }`.

**3d. pack_planner** (always — line 2959): system prompt `10_pack_planner.md` (Tier 3, 8192 tok override). User message via `buildPlannerPacket` — injects contract deliverables verbatim as "MANDATORY CONTRACT — every deliverable below MUST appear in at least one stage."
Output: `{ plan_title, stages[{stage_id,name,purpose,role,file_touch_map:{create,modify,do_not_touch},acceptance_criteria[{check,pass_condition}],depends_on,backward_compat_notes}], recommended_first_stage, estimated_risk, risk_rationale, assumption_audit, verification }`.

**Post-processing chain (deterministic):**
1. `normalizeContractPacket` — coerces contract shape variants.
2. `maybeNormalizeDocumentationStages` — for docs-heavy requests, rewrites stages under existing packet roots.
3. `checkPlanCompleteness(contractDeliverables, planStages)` — verifies every deliverable.id appears in some stage's file_touch_map or stage.purpose. If any missing → **4-Correction** cycle: one extra pack_planner call with appended `**CORRECTION REQUIRED:**` block.
4. `checkPlanCompletenessOnDisk` — verifies file paths reflect reality.
5. `normalizeStageOrder` — enforces impl → reviewer → gatekeeper order.
6. `buildHilltopAuthoringPlan` — for subsystems with canonical docs.
7. `buildTaskGraph` + `assignRoles`.
8. `ensureExpertAgent` — auto-creates agent prompt files for missing roles.

**Revision loop:** after `pack_reviewer` returns `NEEDS_REVISION` → up to 2 cycles via `buildRevisionPacket`. **Surgical mode**: stages NOT named in blocking issues output `{stage_id, unchanged: true}`; merged via `mergeRevision`. Per-stage fallback `reviseOneStage` patches one stage per blocking issue.

### code

**Two LLM passes plus deterministic execution.**

**Pass 1 — Per-stage prompt expansion** (line 3265, **parallel-merge / one LLM call per stage**):

System prompt: `11_implementation_builder.md`. Forced to Tier 3 / Opus via `{ maxTokensOverride: 8192, escalate: true }`.

User message via `buildPromptExpansionPacket(stage, initiative, researchResult, codebaseAnchor, normalizedContract)`:
- Injects `codebaseAnchor` + relevant file excerpts via `gatherExcerptsForFiles(touchedFiles)`.
- Injects all stage metadata + `do_not_touch` + acceptance criteria + contract deliverables verbatim.
- Conditional discipline blocks based on file_touch_map (TIMING/MEMORY/SECURITY/API; specific guards for sensitive files).
- Demands 11 numbered sections IN ORDER: Truth boundary / Do-not-claim-completion-unless / Goal / Read-these-files-first / In-scope files / Out-of-scope files / What would count as fake completion (with 2-3 specific scenarios) / Required changes / Acceptance criteria (commands only) / Scope boundaries / Stop condition.
- File path verification rule, existing-anchor preference rule, seam verification rule, test convention.

Output: markdown prompt document (NOT JSON). Post-processed via `_augmentPromptWithGuards(prompt, file_touch_map, {repoRoot})` (silent-failure discipline injector with catalog AI-ERR-011..036). Stored as `{stage_id, stage_name, prompt_text}` in `expandedPrompts[]`. Checkpoint key per stage: `expansion_${stage_id}`. P05A milestone `expansion_done`.

**Pass 2 — coding_harness execution** (only with `--execute`):

`skills/metabuilder/core/softspot/coding_harness.js` (7929 LOC). Per stage: dispatches to a worktree, runs the expanded prompt, executes `test_command` (jest default), re-prompts on failure with test output. Uses Tier 2 / Sonnet by default for the coder. Inner phases: planner/coder/tester/reviewer each via `callRole`.

For this pipeline, Pass 2 is replaced by `claude --print` running in the worktree with the expanded prompt as input. No need to recreate coding_harness — Claude Code's native agent loop handles it.

### verify

**Multi-role ladder, not a single call.**

**8a. pack_reviewer** (always, line 3123) — system prompt `12_pack_reviewer.md` (Tier 2). User message via `buildReviewerPacket`. Mandatory **Fresh Eyes Hindsight** check (MINOR/MATERIAL/BLOCKING). Output: `{must_fix[], should_fix[], notes[], passed, hindsight, verification}`. Triggers revision cycle in plan node.

**8b. software_reasoning_reviewer** (mandatory, line 3305) — system prompt `34_software_reasoning_reviewer.md` (Tier 3 / Opus). User message via `buildReasoningReviewPacket(initiative, expandedPrompts)` — **reviews expanded prompts, not raw stages.** Forces JSON-only output. Looks ONLY for 8 categories: hot-path-bypass, fake-complete, interface-error, dependency-inversion, error-suppression, schema-drift, policy-bypass, anchor-drift. Output: `{reasoning_verdict: "PASS|CONCERN|FAIL", overall_assessment, concerns[{category,severity,description,fix}], blocking_concerns[]}`.

**8c. executive_governance_reviewer** (always, line 3315) — system prompt `08_executive_governance_reviewer.md` (Tier 3). User message via `buildGovernancePacket` includes plan + reviewer verdict + reasoning verdict + revision status. Output: `{governance_verdict: "PASS|FAIL|NEEDS_REVISION", overall_assessment, findings[{criterion,result,note}], blocking_issues[]}`.

**8c-repair. governance_repair_loop** (`skills/metabuilder/core/planning/governance_repair_loop.js`, 309 LOC) — `MAX_REPAIR_ROUNDS = 2`. Per round: `extractMustFixItems()` → `identifyAffectedStages()` by stage_id or 4+-char keyword → `buildStagePatchPrompt()` per affected stage → invokes pack_planner per stage to return ONLY patched stage JSON → parses via `_parsePatchedStage()` (direct JSON → ```json fence → first brace-match) → merges → re-invokes executive_governance_reviewer (`executive_governance_reviewer_repairN` checkpoint).

**8d. release_gatekeeper** (`19_release_gatekeeper.md`, Tier 2) — final GATE: PASS / FAIL / BLOCKED. Disk-verifies spec completeness before PASS. Output: `{decision, rationale, unresolved_items, verification}`.

**8e. Test execution** is NOT in verify — it's inside `coding_harness.js` per-stage `test_command`.

## Architectural rule (binds all future work)

**Every step is an LLM judgment by default. Deterministic steps require A/B-test evidence that they outperform an LLM call at the same decision.**

Audit of current claude-pipeline hardcoded decisions that should be LLM-replaced:

| Current code | What it decides | Should be LLM? |
|---|---|---|
| `should_retry` in verify.py | retry vs PR-anyway, max retry count | YES — currently hardcoded `MAX_RETRIES=2`. Replace with LLM that takes verify report + history. |
| `_retry_with_guidance` in graph.py | which stage to retry on verify-fail | YES — currently "always last stage". Replace with LLM that analyzes verify report. |
| `_has_more_stages` in graph.py | "are we done coding?" | PROBABLY YES — could short-circuit if acceptance criteria already met. |
| pr_node commit message | what's a good commit message | YES — currently templated. LLM should write from intake + diff + verify. |
| pr_node PR body | what's a good PR body | YES — currently templated. |
| pr_node base branch | branch off main or dev | YES — read repo conventions. |
| pr_node feature branch name | semantic branch name | YES — currently `claude-pipeline/{run_id}`. |
| `git add -A` in pr_node | what to stage | NO (probably) — mechanical. CANDIDATE FOR A/B if exotic cases. |
| JSON parsing | mechanical extraction | NO — pure string operation. |
| `_new_run_id` random hex | entropy | NO. |

## Upgrade roadmap (each line = one upgrade issue)

Ordered by dependency, smallest first:

1. **Replace intake prompt with verbatim metabuilder version** (current is close; align temperature, max_tokens, fallback heuristics).
2. **Add `gatherRelevantExcerpts` preprocessing before research node.**
3. **Replace research prompt with verbatim metabuilder version** (load `04_research_lead.md` as system prompt + buildResearchPacket).
4. **Split plan into contract + planner two-step** (largest single change in current MVP shape).
5. **Add `checkPlanCompleteness` deterministic check + 4-Correction cycle.**
6. **Add `system_gap_analyst` adversarial pre-lane.**
7. **Add `cto_orchestrator` adversarial pre-lane.**
8. **Add `normalizeStageOrder` + `maybeNormalizeDocumentationStages` deterministic post-processing.**
9. **Replace code node with per-stage prompt expansion + execution** (currently one Claude call; should be expansion-pass-then-execute-pass).
10. **Add `_augmentPromptWithGuards` deterministic prompt postprocessor.**
11. **Split verify into the 5-role ladder** (pack_reviewer → software_reasoning_reviewer → executive_governance_reviewer → release_gatekeeper, plus revision loop and governance_repair_loop).
12. **Add governance_repair_loop with surgical per-stage patching.**
13. **Add 4 mandatory reviewers panel** (founder_judge, reliability_engineer, state_architecture_reviewer, security_blast_radius_judge).
14. **Add tier-based LLM routing** (haiku/sonnet/opus by role + escalation policy).
15. **Replace deterministic decisions with LLM nodes** per architectural rule (should_retry, retry_stage, commit message, PR body, branch name, base branch detection).
16. **Add P05A milestones + file-based checkpoints with role-keyed resume.**
17. **Add `buildCodebaseAnchor` consistent grounding block across nodes.**
18. **Add Hilltop authoring** for subsystems with canonical docs.
19. **Add Goal Anchor + Goal Reframing in research** (stated/abstract/generic goal).
20. **Add Assumption Audit (Step 7.5 in pack_planner).**

## Surprising findings

1. **Verify is not a node — it's a 5-role ladder.** Porting verify faithfully means porting pack_reviewer + software_reasoning_reviewer + 4 mandatory reviewers + executive_governance_reviewer + release_gatekeeper + governance_repair_loop. Test execution lives inside coding_harness, not a verify LLM.

2. **Plan is two LLM calls (contract → planner), not one.** contract_writer defines what, pack_planner defines how. Completeness check between them triggers 4-Correction.

3. **Code has TWO LLM passes, both critical.** Per-stage prompt expansion (Opus, 8192 tok) is the most accuracy-critical step (a comment notes Sonnet hallucinated paths at 8192 tok). The expansion prompt carries the truth-boundary and fake-completion-scenario discipline. Without it, the coder loses the rails.

4. **System prompts are in .md files, user messages are built in JS.** Port both halves: system = role .md file content, user = packet builder output.

5. **`gatherRelevantExcerpts` is deterministic preprocessing.** It regex-extracts identifier tokens, greps the repo, inlines excerpts. Without this, research hallucinates file paths. This is the kind of deterministic step that's clearly mechanical and stays deterministic.

6. **Revision uses "surgical mode."** Unchanged stages output as `{stage_id, unchanged: true}`; merger only touches stages explicitly revised. Prevents drift in unrelated areas.

7. **The 4 mandatory reviewers are invoked from pack_reviewer's prompt, not from plan_self_upgrade.js.** Port decision: spawn them as separate LLM calls (faithful) or trust pack_reviewer's prompt instruction (lighter).

8. **All packet builders share one pattern.** `"\n".join([...])` with conditional spread+filter. Highly portable to Python.

## Reference: verbatim role prompt files to copy

Should be pulled from VPS and stored under `prompts/` in this repo:

- `04_research_lead.md`
- `08_executive_governance_reviewer.md`
- `10_pack_planner.md`
- `11_implementation_builder.md`
- `12_pack_reviewer.md`
- `19_release_gatekeeper.md`
- `27_contract_writer.md`
- `34_software_reasoning_reviewer.md`
- `35_system_gap_analyst.md`
- `36_cto_orchestrator.md`

Plus the 4 mandatory reviewers' prompts (likely in same `prompts/` dir; need to verify on VPS).
