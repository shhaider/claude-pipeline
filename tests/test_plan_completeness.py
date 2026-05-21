"""Tests for the deterministic plan-completeness check.

Pure-Python; no LLM calls.
"""

from __future__ import annotations

from claude_pipeline.plan_completeness import (
    build_correction_block,
    check_plan_completeness,
)


def _del(d_id: str, name: str, success: list[str] | None = None) -> dict:
    return {
        "id": d_id,
        "name": name,
        "description": f"{name} description",
        "success_criteria": success or [],
        "source_goal": "test goal",
    }


def _stage(
    sid: str, purpose: str, create: list[str] | None = None, modify: list[str] | None = None
) -> dict:
    return {
        "stage_id": sid,
        "name": sid,
        "purpose": purpose,
        "file_touch_map": {
            "create": create or [],
            "modify": modify or [],
            "do_not_touch": [],
        },
        "acceptance_criteria": [],
    }


class TestCheckPlanCompleteness:
    def test_empty_deliverables_is_ok(self):
        result = check_plan_completeness([], [_stage("S1", "do something")])
        assert result["ok"] is True
        assert result["missing"] == []

    def test_all_deliverables_matched_by_filename(self):
        deliverables = [
            _del("D1", "intake.py"),
            _del("D2", "research.py"),
        ]
        stages = [
            _stage("S1", "create intake module", create=["src/intake.py"]),
            _stage("S2", "create research module", create=["src/research.py"]),
        ]
        result = check_plan_completeness(deliverables, stages)
        assert result["ok"] is True
        assert len(result["matched"]) == 2

    def test_match_by_purpose_text(self):
        deliverables = [_del("D1", "intake.py")]
        stages = [
            _stage("S1", "Refactor intake.py to use new schema", create=[])
        ]
        result = check_plan_completeness(deliverables, stages)
        assert result["ok"] is True

    def test_match_by_id(self):
        deliverables = [_del("D1", "")]  # name empty — fall through to id
        stages = [_stage("S1", "implements D1 of the contract")]
        result = check_plan_completeness(deliverables, stages)
        assert result["ok"] is True

    def test_missing_deliverable_flagged(self):
        deliverables = [
            _del("D1", "intake.py"),
            _del("D2", "research.py"),
            _del("D3", "secret_file.py"),
        ]
        stages = [
            _stage("S1", "do D1 thing", create=["src/intake.py"]),
            _stage("S2", "do D2 thing", create=["src/research.py"]),
        ]
        result = check_plan_completeness(deliverables, stages)
        assert result["ok"] is False
        assert len(result["missing"]) == 1
        assert result["missing"][0]["id"] == "D3"

    def test_match_works_with_flat_file_touch_map(self):
        # v0.1 legacy shape: file_touch_map is just a list
        deliverables = [_del("D1", "intake.py")]
        stages = [
            {
                "stage_id": "S1",
                "purpose": "do stuff",
                "file_touch_map": ["src/intake.py"],
            }
        ]
        result = check_plan_completeness(deliverables, stages)
        assert result["ok"] is True


class TestBuildCorrectionBlock:
    def test_empty_missing_returns_empty(self):
        assert build_correction_block([]) == ""

    def test_includes_deliverable_ids_and_names(self):
        missing = [
            {"id": "D3", "name": "secret_file.py", "reason": "n/a"},
            {"id": "D5", "name": "other.py", "reason": "n/a"},
        ]
        block = build_correction_block(missing)
        assert "CORRECTION REQUIRED" in block
        assert "D3" in block
        assert "secret_file.py" in block
        assert "D5" in block
        assert "other.py" in block

    def test_says_revise_full_plan(self):
        missing = [{"id": "D1", "name": "x.py", "reason": "n/a"}]
        block = build_correction_block(missing)
        # Should clearly instruct to return the full revised plan
        assert "FULL" in block or "full" in block
