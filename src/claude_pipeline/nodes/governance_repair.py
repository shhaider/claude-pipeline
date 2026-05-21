"""governance_repair loop — pure-Python port of metabuilder's
`skills/metabuilder/core/planning/governance_repair_loop.js` (309 LOC).

Algorithm (MAX_REPAIR_ROUNDS = 2):
  for round in 1..MAX:
    1. Extract must_fix_items from the governance_review verdict.
    2. Identify affected stages — by stage_id mention OR 4+-char keyword
       in the must_fix description (case-insensitive substring match
       against the stage's name / purpose / file_touch_map paths).
    3. For each affected stage, invoke pack_planner with a "Patch ONLY
       this stage" prompt. Parse the returned JSON for the patched stage.
    4. Merge patched stages back into the plan.
    5. Re-run the code_node on each patched stage — RESUMING the code
       session so the implementer sees its own earlier work and can
       refactor cross-stage.
    6. Re-invoke governance_reviewer with repair_round=N.
    7. If governance_verdict == "PASS" -> done. Else continue.

The pure-Python pieces (item identification, keyword matching, merging,
patch JSON parsing) are unit-tested. The LLM-driven pieces are
validated by the integration run.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from claude_pipeline.claude import ClaudeError, extract_json, run_claude
from claude_pipeline.nodes.code import code_node
from claude_pipeline.nodes.governance_reviewer import governance_reviewer_node
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)

MAX_REPAIR_ROUNDS = 2

_PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts" / "metabuilder"
_PLANNER_PROMPT_PATH = _PROMPTS_DIR / "10_pack_planner.md"


def _load_planner_prompt() -> str:
    try:
        return _PLANNER_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as e:
        raise RuntimeError(
            f"missing pack_planner role prompt at {_PLANNER_PROMPT_PATH}: {e}"
        ) from e


# Pure-Python helpers --------------------------------------------------


def extract_must_fix_items(governance_review: dict[str, Any]) -> list[str]:
    """Pull the list of must-fix descriptions out of a governance verdict.

    Looks at: top-level `blocking_issues`, plus any `findings` whose
    `result` is FAIL or PARTIAL.
    """
    items: list[str] = []
    for x in governance_review.get("blocking_issues", []) or []:
        if isinstance(x, str) and x.strip():
            items.append(x.strip())
    for f in governance_review.get("findings", []) or []:
        if not isinstance(f, dict):
            continue
        if str(f.get("result", "")).upper() in {"FAIL", "PARTIAL"}:
            crit = str(f.get("criterion", "")).strip()
            note = str(f.get("note", "")).strip()
            text = f"{crit}: {note}" if crit and note else (crit or note)
            if text and text not in items:
                items.append(text)
    return items


_KEYWORD_RE = re.compile(r"[a-zA-Z0-9_]{4,}")
# Common English words to avoid matching every stage to every concern
_STOPWORDS = {
    "this", "that", "with", "from", "into", "have", "been", "must", "should",
    "would", "could", "make", "need", "test", "tests", "code", "file", "files",
    "function", "module", "class", "stage", "stages", "plan", "name", "value",
    "values", "check", "issue", "true", "false", "none", "type", "types", "json",
    "data", "list", "lists", "dict", "string", "object", "boolean", "added",
    "fixed", "must_fix", "should_fix", "result", "passed", "fails", "fail",
    "pass", "case", "cases", "above", "below", "before", "after", "when",
    "what", "which", "where", "while", "does", "doesn", "didn", "isn", "into",
    "such", "than", "then", "their", "them", "they", "your", "yours", "ours",
    "also", "only", "even", "still", "very", "more", "less", "much", "many",
    "some", "each", "every", "other", "another", "without",
}


def _stage_blob(stage: dict[str, Any]) -> str:
    """Searchable text blob for a stage, lowercased."""
    pieces: list[str] = []
    for k in ("stage_id", "name", "purpose", "description", "backward_compat_notes"):
        v = stage.get(k)
        if isinstance(v, str):
            pieces.append(v)
    ftm = stage.get("file_touch_map", {})
    if isinstance(ftm, dict):
        for key in ("create", "modify", "do_not_touch"):
            for p in ftm.get(key, []) or []:
                pieces.append(str(p))
    elif isinstance(ftm, list):
        pieces.extend(str(p) for p in ftm)
    crit = stage.get("acceptance_criteria", []) or []
    for c in crit:
        if isinstance(c, dict):
            for k in ("check", "pass_condition"):
                if isinstance(c.get(k), str):
                    pieces.append(c[k])
        elif isinstance(c, str):
            pieces.append(c)
    return "\n".join(pieces).lower()


def identify_affected_stages(
    must_fix_items: list[str], stages: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """For each must_fix item, return the stage_ids it touches.

    Rule (port of metabuilder identifyAffectedStages):
      - explicit stage_id mention (S1, S2, ...) — match exact
      - 4+-char keyword extraction — match case-insensitive substring
        against the stage blob (name / purpose / file_touch_map paths)
      - skip stopwords (this/that/code/test/etc.)
      - if NO stage matches, assign to all stages (broad fix)

    Returns: {must_fix_item: [stage_id, ...]}
    """
    stage_blobs: list[tuple[str, str]] = []
    for s in stages:
        sid = str(s.get("stage_id") or s.get("name") or "S?")
        stage_blobs.append((sid, _stage_blob(s)))

    mapping: dict[str, list[str]] = {}
    for item in must_fix_items:
        hits: list[str] = []
        lower = item.lower()

        # Direct stage_id mention takes priority
        for sid, _ in stage_blobs:
            sid_l = sid.lower()
            # Word-boundary match for stage ids like S1, S2
            if re.search(rf"\b{re.escape(sid_l)}\b", lower):
                if sid not in hits:
                    hits.append(sid)

        if not hits:
            # Keyword matching
            tokens = {
                t.lower()
                for t in _KEYWORD_RE.findall(item)
                if t.lower() not in _STOPWORDS and len(t) >= 4
            }
            for sid, blob in stage_blobs:
                if any(tok in blob for tok in tokens):
                    if sid not in hits:
                        hits.append(sid)

        if not hits:
            # Broad fix — every stage
            hits = [sid for sid, _ in stage_blobs]

        mapping[item] = hits
    return mapping


def _parse_patched_stage(text: str) -> dict[str, Any] | None:
    """Pull a single stage JSON object out of LLM output.

    Tries: direct parse, code-fenced parse, first balanced brace.
    Returns None on failure.
    """
    try:
        raw = extract_json(text)
    except (ValueError, json.JSONDecodeError):
        return None
    if isinstance(raw, dict):
        # Direct stage object
        if "stage_id" in raw or "name" in raw:
            return raw
        # Sometimes the planner returns {"stages": [{...}]} or {"stage": {...}}
        if "stage" in raw and isinstance(raw["stage"], dict):
            return raw["stage"]
        if "stages" in raw and isinstance(raw["stages"], list) and raw["stages"]:
            cand = raw["stages"][0]
            if isinstance(cand, dict):
                return cand
        return raw  # last resort — return what we have
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        return raw[0]
    return None


def merge_patched_stages(
    plan: list[dict[str, Any]], patches: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Merge patched stage dicts back into the plan by stage_id.

    `patches` is {stage_id: patched_stage_obj}. Unmatched patches are
    dropped (the planner may have invented a stage we don't track).
    """
    out: list[dict[str, Any]] = []
    for s in plan:
        sid = str(s.get("stage_id") or "")
        if sid and sid in patches:
            patch = patches[sid]
            merged = dict(s)
            for k, v in patch.items():
                if k == "stage_id":
                    continue  # don't let the patch rename a stage
                if v is None:
                    continue
                merged[k] = v
            out.append(merged)
        else:
            out.append(s)
    return out


def build_stage_patch_prompt(stage: dict[str, Any], must_fix_items: list[str]) -> str:
    """Render the planner packet that asks for a single-stage patch."""
    sid = stage.get("stage_id") or stage.get("name", "?")
    ftm = stage.get("file_touch_map", {})
    if isinstance(ftm, dict):
        ftm_render = json.dumps(ftm, indent=2)
    else:
        ftm_render = json.dumps({"modify": list(ftm or [])}, indent=2)
    crit = stage.get("acceptance_criteria", []) or []
    crit_render = json.dumps(crit, indent=2)
    mf_bullets = "\n".join(f"- {m}" for m in must_fix_items) or "- (none)"
    return "\n".join(
        [
            "## pack_planner — stage patch task",
            "",
            "You are acting as pack_planner in **patch mode**. Your job is to revise ONE",
            "stage to address the must_fix items below. Do NOT add new stages, do NOT",
            "rewrite other stages, do NOT change the stage_id.",
            "",
            f"## Stage to patch: {sid}",
            "",
            "**Current stage JSON:**",
            "",
            "```json",
            json.dumps(
                {
                    "stage_id": sid,
                    "name": stage.get("name", ""),
                    "purpose": stage.get("purpose") or stage.get("description", ""),
                    "role": stage.get("role", "implementation_builder"),
                    "file_touch_map": ftm if isinstance(ftm, dict) else {"modify": list(ftm or [])},
                    "acceptance_criteria": crit,
                    "depends_on": stage.get("depends_on", []),
                    "backward_compat_notes": stage.get("backward_compat_notes", ""),
                },
                indent=2,
            ),
            "```",
            "",
            "## Must-fix items from governance_reviewer",
            "",
            mf_bullets,
            "",
            "## Required output",
            "",
            "Return a SINGLE JSON object: the patched stage, in the same shape as the",
            "current stage JSON above. Keep `stage_id` exactly the same. Update fields as",
            "needed to address the must_fix items. Output JSON only, no preamble.",
            "",
            "```json",
            "{",
            f'  "stage_id": "{sid}",',
            '  "name": "...",',
            '  "purpose": "...",',
            '  "role": "implementation_builder",',
            '  "file_touch_map": { "create": [], "modify": [], "do_not_touch": [] },',
            '  "acceptance_criteria": [ ... ],',
            '  "depends_on": [],',
            '  "backward_compat_notes": "..."',
            "}",
            "```",
        ]
    )


# Main driver ---------------------------------------------------------


def _patch_one_stage(
    stage: dict[str, Any],
    must_fix_items: list[str],
    state: PipelineState,
    role_prompt: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """LLM call: patch one stage. Returns (patched_stage, error)."""
    user_msg = build_stage_patch_prompt(stage, must_fix_items)
    try:
        result = run_claude(
            user_msg,
            cwd=state.get("worktree_path"),
            timeout_s=600,
            model="opus",
            extra_args=["--append-system-prompt", role_prompt],
        )
    except ClaudeError as e:
        return None, f"patch claude call failed: {e}"
    patched = _parse_patched_stage(result.text)
    if not patched:
        return None, f"patch parse failed; head: {result.text[:300]}"
    # Always normalize the stage_id back to original
    patched["stage_id"] = stage.get("stage_id") or patched.get("stage_id", "")
    return patched, None


def governance_repair_node(state: PipelineState) -> dict:
    """Run up to MAX_REPAIR_ROUNDS rounds of: patch affected stages,
    re-run those stages (RESUMING the code session), then re-invoke
    governance_reviewer.

    Re-entry: this node is called from the graph only when the prior
    governance_review verdict is NEEDS_REVISION or FAIL. We loop
    internally rather than yielding back to the graph between rounds —
    keeps the state machine small.
    """
    governance = state.get("governance_review", {}) or {}
    verdict = str(governance.get("governance_verdict", "")).upper()
    if verdict == "PASS":
        log.info("governance_repair: nothing to do (verdict already PASS)")
        return {"error": None}

    plan = list(state.get("plan", []) or [])
    if not plan:
        return {"error": "governance_repair: empty plan"}

    try:
        role_prompt = _load_planner_prompt()
    except RuntimeError as e:
        return {"error": str(e)}

    repair_log: list[dict[str, Any]] = list(state.get("governance_repair_log", []) or [])
    rounds_done = int(state.get("governance_repair_rounds", 0) or 0)
    working_state: PipelineState = dict(state)  # type: ignore[assignment]

    for round_idx in range(rounds_done + 1, MAX_REPAIR_ROUNDS + 1):
        gov = working_state.get("governance_review", {}) or {}
        v = str(gov.get("governance_verdict", "")).upper()
        if v == "PASS":
            break

        must_fix_items = extract_must_fix_items(gov)
        if not must_fix_items:
            log.info("governance_repair round %d: no must_fix items — exiting", round_idx)
            break

        log.info(
            "governance_repair round %d: %d must_fix items to address",
            round_idx,
            len(must_fix_items),
        )
        affected = identify_affected_stages(must_fix_items, plan)
        # Build a stage_id -> aggregated must_fix list
        stage_to_items: dict[str, list[str]] = {}
        for item, sids in affected.items():
            for sid in sids:
                stage_to_items.setdefault(sid, []).append(item)

        # Patch each affected stage
        patches: dict[str, dict[str, Any]] = {}
        patch_errors: list[str] = []
        for sid, items in stage_to_items.items():
            stage_obj = next(
                (s for s in plan if str(s.get("stage_id") or "") == sid), None
            )
            if stage_obj is None:
                continue
            log.info(
                "governance_repair: patching stage %s (%d items)", sid, len(items)
            )
            patched, err = _patch_one_stage(stage_obj, items, working_state, role_prompt)
            if err or not patched:
                patch_errors.append(f"{sid}: {err}")
                continue
            patches[sid] = patched

        if not patches:
            log.warning(
                "governance_repair round %d: no patches succeeded (%d errors) — stopping",
                round_idx,
                len(patch_errors),
            )
            repair_log.append(
                {
                    "round": round_idx,
                    "must_fix_count": len(must_fix_items),
                    "patches_attempted": len(stage_to_items),
                    "patches_succeeded": 0,
                    "errors": patch_errors,
                    "outcome": "patch_failed",
                }
            )
            break

        plan = merge_patched_stages(plan, patches)
        working_state["plan"] = plan

        # Re-run the affected stages through code_node, resuming session
        for sid in patches.keys():
            stage_idx = next(
                (i for i, s in enumerate(plan) if str(s.get("stage_id") or "") == sid),
                None,
            )
            if stage_idx is None:
                continue
            working_state["current_stage_idx"] = stage_idx
            log.info(
                "governance_repair: re-running stage %s (idx=%d, resume=yes)",
                sid,
                stage_idx,
            )
            patch_state_update = code_node(working_state)
            if patch_state_update.get("error"):
                patch_errors.append(f"recoding {sid}: {patch_state_update['error']}")
                continue
            # Merge code_node's updates back in
            for k, v_ in patch_state_update.items():
                if v_ is not None:
                    working_state[k] = v_  # type: ignore[literal-required]

        # Refresh diff after re-coding
        working_state["code_diff"] = ""  # force recapture in next reviewer

        # Re-run governance_reviewer
        gov_update = governance_reviewer_node(working_state, repair_round=round_idx)
        if gov_update.get("error"):
            log.warning(
                "governance_repair round %d: governance re-review errored: %s",
                round_idx,
                gov_update["error"],
            )
            repair_log.append(
                {
                    "round": round_idx,
                    "must_fix_count": len(must_fix_items),
                    "patches_succeeded": len(patches),
                    "errors": patch_errors + [gov_update["error"]],
                    "outcome": "rereview_errored",
                }
            )
            break

        for k, v_ in gov_update.items():
            if v_ is not None:
                working_state[k] = v_  # type: ignore[literal-required]

        new_gov = working_state.get("governance_review", {}) or {}
        new_verdict = str(new_gov.get("governance_verdict", "")).upper()
        repair_log.append(
            {
                "round": round_idx,
                "must_fix_count": len(must_fix_items),
                "patches_succeeded": len(patches),
                "errors": patch_errors,
                "new_verdict": new_verdict,
                "outcome": "round_complete",
            }
        )

        if new_verdict == "PASS":
            log.info("governance_repair: PASS after round %d — done", round_idx)
            break

    out: dict[str, Any] = {
        "plan": plan,
        "governance_review": working_state.get("governance_review", {}),
        "governance_repair_rounds": min(rounds_done + len(repair_log), MAX_REPAIR_ROUNDS),
        "governance_repair_log": repair_log,
        "code_summary": working_state.get("code_summary", state.get("code_summary", "")),
        "code_session_id": working_state.get(
            "code_session_id", state.get("code_session_id", "")
        ),
        "code_diff": working_state.get("code_diff", ""),
        "error": None,
    }
    return out
