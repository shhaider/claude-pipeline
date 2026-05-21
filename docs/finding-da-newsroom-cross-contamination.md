# Finding — "Da newsroom" cross-contamination investigation

**Date:** 2026-05-21
**Investigator:** v0.4-prep agent
**Question:** Is "Da newsroom" / "Db/Eb" / "Da mode" in the software-dev skill a
real software-pipeline concept, or cross-contamination from the writing pipeline
(scribblios newsroom)?

---

## The literal hits

### 1. `~/.claude/skills/software-dev/SKILL.md` — 4 mentions

Lines 501-503 (Step 0 complexity calibration table):

```
| **Bounded** | 1–3 files, known scope, ≤1 existing API touched | Abbreviated pipeline — skip Da newsroom, use Db/Eb for planning |
| **Complex** | New subsystem, ≥3 new modules, ≥2 existing APIs touched, integration specs | Full pipeline — use Da newsroom for planning |
| **Phased** | Multi-stage roadmap work, defines contracts for future stages | Full pipeline + roadmap crosscheck mandatory — Da mode always |
```

Line 567 (example output):

```
- `COMPLEXITY: complex | META: no | Budget: full pipeline, Da mode`
```

### 2. VPS — `/home/claw/clawcodex/docs/agent_coordination/skills/software-dev-skill.txt`

Two hits (lines 505, 506) — identical to lines 501-502 above. This file is a
mirror/sync of the local SKILL.md, present in the main checkout and three
`.worktrees/` copies. Same content; not an independent source.

---

## Where "Da newsroom" / "Db" / "Eb" / "Da mode" is NOT mentioned

Searched on VPS (clawcodex repo) and locally:

| Location | Hits for `Da newsroom`, `Db newsroom`, `Da mode`, `Da_newsroom` |
|---|---|
| `clawcodex/scripts/metabuilder/` | 0 |
| `clawcodex/skills/metabuilder/` | 0 |
| `clawcodex/skills/newsroom/` (all 35 stages, SKILL.md, COWORK_HANDOFF) | 0 |
| `clawcodex/docs/metabuilder/` (canonical metabuilder docs) | 0 |
| `clawcodex/docs/scribblios/` | 0 |
| Any other skill under `~/.claude/skills/` | 0 |

The only `Eb` hit anywhere in `skills/newsroom/` is one unrelated note in
`COWORK_HANDOFF.md` line 115: *"Eb timed out at 30.5 minutes on a ~2500 word
article's synthesis step"* — clearly an internal codename for some writing
sub-agent or stage that the operator was tracking informally. It is not the
same "Eb" the software-dev skill table references, and it is not defined
anywhere in the newsroom pipeline itself.

The newsroom pipeline's actual stages are named in plain English in
`skills/newsroom/SKILL.md` (intake_created, trend_candidates_built,
constitution_filtered, …, post_publish_analytics_snapshot). There is no
"Da" or "Db" or "Eb" stage code in the real newsroom workflow.

---

## What the table is trying to say

The table's intent is reasonable: route different complexity tiers to
different planning depths. "Skip Da newsroom, use Db/Eb for planning" is
clearly trying to gesture at *some* tiered planning system. But the terms
`Da`, `Db`, `Eb`, `Da newsroom`, `Da mode` are never defined in the skill
itself, never referenced in any code, and never explained in any companion
doc. The reader is left to guess.

The most plausible reconstruction is that "Da/Db/Eb" was an internal
codename from a prior iteration of MetaBuilder's planning lanes (perhaps
`Decision a` / `Decision b` / `Evidence b` or similar) that never made it
into the live codebase, OR a shorthand from the writing-pipeline brainstorm
that bled into the software-dev skill during a copy/paste from a shared
template.

Either way, the table currently asks the reader to follow instructions
("use Db/Eb for planning") that have no implementation behind them.

---

## Verdict

**CONTAMINATED — likely cross-contamination from the writing pipeline OR
stale orphan terminology from a prior planning-lane scheme that was
never wired.**

Three concrete reasons:

1. **Zero hits in real code.** Neither metabuilder scripts/skills nor
   newsroom scripts/skills know what `Da`, `Db`, `Eb`, "Da newsroom", or
   "Da mode" are. If these were live concepts, the runner code would
   reference them.

2. **The term "newsroom" only exists in the writing pipeline.** The
   software-dev skill should not reference "newsroom" at all under the
   single-source-of-truth principle. Mentioning it suggests the table
   was templated from (or alongside) a writing-pipeline planning doc and
   the placeholder was never cleaned up.

3. **The terms are self-referential.** The SKILL.md uses them as if they
   are defined elsewhere, but there is no "elsewhere." This is a tell-tale
   sign of orphan terminology — a concept that was promised but never
   delivered, then quoted as if it had been.

---

## Recommendation

**File an issue against scribblios (or wherever the canonical software-dev
skill lives) to clarify or remove the `Da newsroom` / `Db/Eb` / `Da mode`
terminology in `~/.claude/skills/software-dev/SKILL.md` lines 501-503 and
567.** Either:

- (a) **Replace** with concrete planning-depth labels that match what the
  skill actually does (e.g., "skip CTO sanity check + skip
  system_gap_analyst lane" instead of "skip Da newsroom"). This is the
  better option — say what the rule actually does.
- (b) **Define** Da/Db/Eb explicitly somewhere — add a "planning lanes"
  reference section near Step 3.5 that maps the codes to behavior. This
  is acceptable if there is a real intent behind the names.
- (c) **Remove** the column entirely if there is no concrete pipeline
  branch behind the labels.

This is low-stakes for v0.4 (the labels are not load-bearing on any
runner code), but it's a documentation hygiene fix worth doing — the
table is currently giving operators instructions they cannot follow.

For v0.4-prep purposes, we should treat the complexity tiers as
**trivial / bounded / complex / phased only** and ignore the
unimplemented Da/Db/Eb routing column when wiring tier-routing logic.
