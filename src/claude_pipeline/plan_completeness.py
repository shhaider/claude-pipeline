"""Deterministic plan-completeness check.

Ports metabuilder's `checkPlanCompleteness(contractDeliverables, planStages)`
from `scripts/metabuilder/plan_self_upgrade.js`.

Rule: every contract `deliverable.id` (D1, D2, ...) must appear in at
least one plan stage's `file_touch_map` (as a path component) OR in
the stage's `purpose` (string match against deliverable.name).

If any deliverable is missing, we either (a) signal the planner to
re-run with a CORRECTION block, or (b) raise an error. The graph wires
this into a single 4-Correction cycle (max one extra pack_planner call).

This is pure-Python, no LLM calls — easy to unit-test against fixtures.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def _stage_text_blob(stage: dict[str, Any]) -> str:
    """Join all stage text fields into one searchable blob.

    Covers file_touch_map (create/modify/do_not_touch), purpose, name,
    description, and acceptance_criteria checks.
    """
    pieces: list[str] = []
    ftm = stage.get("file_touch_map", {})
    if isinstance(ftm, dict):
        for key in ("create", "modify", "do_not_touch"):
            v = ftm.get(key, [])
            if isinstance(v, list):
                pieces.extend(str(x) for x in v)
    elif isinstance(ftm, list):
        # flat list shape (current MVP)
        pieces.extend(str(x) for x in ftm)
    for k in ("purpose", "name", "description", "backward_compat_notes"):
        v = stage.get(k)
        if isinstance(v, str):
            pieces.append(v)
    crit = stage.get("acceptance_criteria", [])
    if isinstance(crit, list):
        for c in crit:
            if isinstance(c, dict):
                for k in ("check", "pass_condition"):
                    if isinstance(c.get(k), str):
                        pieces.append(c[k])
            elif isinstance(c, str):
                pieces.append(c)
    return "\n".join(pieces).lower()


def check_plan_completeness(
    contract_deliverables: list[dict[str, Any]],
    plan_stages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify every contract deliverable appears in at least one stage.

    Match rule (most-permissive-first, accepted on first hit):
      1. Stage's text blob contains the deliverable's `name` (case-insensitive substring)
      2. Stage's text blob contains the deliverable's `id` (D1, D2, ...)
      3. Stage's text blob contains any element from `success_criteria`

    Args:
        contract_deliverables: list of {id, name, description, success_criteria?, ...}
        plan_stages: list of stages as emitted by pack_planner

    Returns:
        {
          "ok": bool,
          "missing": [
            {"id": "D3", "name": "foo.py", "reason": "not in any stage"}
          ],
          "matched": {"D1": "S1", "D2": "S1", ...},
        }
    """
    if not contract_deliverables:
        return {"ok": True, "missing": [], "matched": {}}

    stage_blobs: list[tuple[str, str]] = []
    for s in plan_stages:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("stage_id") or s.get("name") or "S?")
        stage_blobs.append((sid, _stage_text_blob(s)))

    missing: list[dict[str, str]] = []
    matched: dict[str, str] = {}

    for d in contract_deliverables:
        if not isinstance(d, dict):
            continue
        did = str(d.get("id", ""))
        name = str(d.get("name", "")).strip()
        sc = d.get("success_criteria", []) or []

        if not name and not did:
            continue

        found_in: str | None = None
        # Pass 1 — match by name (most specific signal)
        if name:
            nlow = name.lower()
            for sid, blob in stage_blobs:
                if nlow in blob:
                    found_in = sid
                    break
        # Pass 2 — match by deliverable id
        if not found_in and did:
            for sid, blob in stage_blobs:
                if did.lower() in blob:
                    found_in = sid
                    break
        # Pass 3 — match by any success_criteria token
        if not found_in and isinstance(sc, list):
            for crit in sc:
                if not isinstance(crit, str):
                    continue
                # Skip empty / very generic criteria
                clow = crit.strip().lower()
                if len(clow) < 8:
                    continue
                # Avoid matching on the whole CLI command — use the
                # path component if there's a /
                probe = clow
                if "/" in clow:
                    probe = clow.rsplit("/", 1)[-1]
                    probe = probe.split()[0] if probe else clow
                if not probe or len(probe) < 4:
                    continue
                for sid, blob in stage_blobs:
                    if probe in blob:
                        found_in = sid
                        break
                if found_in:
                    break

        if found_in:
            matched[did or name] = found_in
        else:
            missing.append(
                {
                    "id": did,
                    "name": name,
                    "reason": "not referenced by any stage's file_touch_map or purpose",
                }
            )

    ok = len(missing) == 0
    log.info(
        "checkPlanCompleteness: %d deliverables, %d matched, %d missing",
        len(contract_deliverables),
        len(matched),
        len(missing),
    )
    return {"ok": ok, "missing": missing, "matched": matched}


def build_correction_block(missing: list[dict[str, str]]) -> str:
    """Render a CORRECTION REQUIRED block to append to a pack_planner retry.

    Matches metabuilder's wording so the planner recognizes the pattern.
    """
    if not missing:
        return ""
    lines = [
        "**CORRECTION REQUIRED:**",
        "",
        "Your previous plan was checked against the contract. The following deliverables",
        "are not referenced by any stage's file_touch_map or purpose:",
        "",
    ]
    for m in missing:
        did = m.get("id", "?")
        name = m.get("name", "?")
        lines.append(f"- {did}: {name}")
    lines.extend(
        [
            "",
            "Revise your plan so that EVERY contract deliverable above appears in at least",
            "one stage's file_touch_map (as a created or modified path) or in a stage's",
            "purpose string. Do not drop existing stages — add or amend stages as needed.",
            "",
            "Return the FULL revised plan JSON in the same shape as before.",
        ]
    )
    return "\n".join(lines)
