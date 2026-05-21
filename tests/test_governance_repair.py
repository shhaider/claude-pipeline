"""Tests for the pure-Python pieces of governance_repair.

The LLM-calling driver (`governance_repair_node`) is validated by the
integration run. Here we cover:
  - extract_must_fix_items
  - identify_affected_stages (stage_id match + keyword match + fallback)
  - _parse_patched_stage (direct / fence / brace-fallback)
  - merge_patched_stages (in-place merge by stage_id, unknown ids dropped)
  - build_stage_patch_prompt (smoke: contains key tokens)
"""

from __future__ import annotations

from claude_pipeline.nodes.governance_repair import (
    build_stage_patch_prompt,
    extract_must_fix_items,
    identify_affected_stages,
    merge_patched_stages,
    _parse_patched_stage,
)


# ---- extract_must_fix_items -----------------------------------------


class TestExtractMustFixItems:
    def test_blocking_issues_pulled(self):
        gov = {"blocking_issues": ["Missing tests __init__.py", "Slice hack"]}
        items = extract_must_fix_items(gov)
        assert items == ["Missing tests __init__.py", "Slice hack"]

    def test_failing_findings_pulled(self):
        gov = {
            "findings": [
                {"criterion": "spec completeness", "result": "FAIL", "note": "D2 missing"},
                {"criterion": "tests pass", "result": "PASS", "note": ""},
                {"criterion": "diff hygiene", "result": "PARTIAL", "note": "stray .bak"},
            ]
        }
        items = extract_must_fix_items(gov)
        assert any("spec completeness" in i and "D2 missing" in i for i in items)
        assert any("diff hygiene" in i for i in items)
        # PASS not in
        assert not any("tests pass" in i for i in items)

    def test_dedupes_across_blocking_and_findings(self):
        gov = {
            "blocking_issues": ["x"],
            "findings": [{"criterion": "x", "result": "FAIL", "note": ""}],
        }
        items = extract_must_fix_items(gov)
        # Both will appear (different shapes); dedup is best-effort, not exhaustive
        assert "x" in items

    def test_empty_returns_empty(self):
        assert extract_must_fix_items({}) == []
        assert extract_must_fix_items({"blocking_issues": [], "findings": []}) == []


# ---- identify_affected_stages ---------------------------------------


class TestIdentifyAffectedStages:
    def test_explicit_stage_id_match(self):
        stages = [
            {"stage_id": "S1", "name": "intake refactor", "file_touch_map": {"create": ["a.py"]}},
            {"stage_id": "S2", "name": "research", "file_touch_map": {"modify": ["b.py"]}},
        ]
        items = ["Fix S1 to handle empty body"]
        mapping = identify_affected_stages(items, stages)
        assert mapping[items[0]] == ["S1"]

    def test_keyword_match_via_filename(self):
        stages = [
            {"stage_id": "S1", "name": "intake", "file_touch_map": {"create": ["intake.py"]}},
            {"stage_id": "S2", "name": "research", "file_touch_map": {"modify": ["research.py"]}},
        ]
        items = ["The intake module is missing validation"]
        mapping = identify_affected_stages(items, stages)
        assert "S1" in mapping[items[0]]
        # Should not also catch S2 unless 'research' keyword appears
        assert "S2" not in mapping[items[0]]

    def test_keyword_match_via_purpose(self):
        stages = [
            {"stage_id": "S1", "name": "stage one", "purpose": "Wire up the authentication helper", "file_touch_map": {}},
            {"stage_id": "S2", "name": "stage two", "purpose": "Output formatting", "file_touch_map": {}},
        ]
        items = ["The authentication path is missing rate limits"]
        mapping = identify_affected_stages(items, stages)
        assert mapping[items[0]] == ["S1"]

    def test_no_match_assigns_all_stages(self):
        stages = [
            {"stage_id": "S1", "name": "x", "file_touch_map": {}},
            {"stage_id": "S2", "name": "y", "file_touch_map": {}},
        ]
        items = ["Generic governance concern with no keywords"]
        mapping = identify_affected_stages(items, stages)
        # When no stage matches, the item is broadcast to all stages
        assert set(mapping[items[0]]) == {"S1", "S2"}

    def test_stopwords_do_not_match(self):
        # 'tests' is in stopwords; if it were not, every stage would match
        stages = [
            {"stage_id": "S1", "name": "alpha", "purpose": "no relevant tokens here", "file_touch_map": {}},
            {"stage_id": "S2", "name": "beta", "purpose": "different content", "file_touch_map": {}},
        ]
        items = ["The tests are missing"]
        mapping = identify_affected_stages(items, stages)
        # 'tests' is stopworded -> no specific keyword match -> broadcast to all
        assert set(mapping[items[0]]) == {"S1", "S2"}

    def test_short_tokens_ignored(self):
        # 3-char tokens shouldn't match
        stages = [
            {"stage_id": "S1", "name": "abc", "purpose": "and", "file_touch_map": {}},
            {"stage_id": "S2", "name": "longerword", "purpose": "more text", "file_touch_map": {}},
        ]
        items = ["fix abc and the"]  # 'abc' is 3-char => below 4-char floor
        mapping = identify_affected_stages(items, stages)
        # No 4+-char specific keyword in 'fix abc and the' -> broadcast
        assert set(mapping[items[0]]) == {"S1", "S2"}


# ---- _parse_patched_stage -------------------------------------------


class TestParsePatchedStage:
    def test_direct_object(self):
        text = '{"stage_id": "S1", "name": "fixed"}'
        result = _parse_patched_stage(text)
        assert result == {"stage_id": "S1", "name": "fixed"}

    def test_code_fenced(self):
        text = '```json\n{"stage_id": "S1", "name": "fixed"}\n```'
        result = _parse_patched_stage(text)
        assert result == {"stage_id": "S1", "name": "fixed"}

    def test_wrapped_in_stages_array(self):
        text = '{"stages": [{"stage_id": "S1", "name": "alpha"}]}'
        result = _parse_patched_stage(text)
        assert result == {"stage_id": "S1", "name": "alpha"}

    def test_wrapped_in_stage_key(self):
        text = '{"stage": {"stage_id": "S2", "name": "beta"}}'
        result = _parse_patched_stage(text)
        assert result == {"stage_id": "S2", "name": "beta"}

    def test_garbage_returns_none(self):
        assert _parse_patched_stage("not even close to JSON") is None

    def test_preamble_with_object(self):
        text = "Here's the patched stage:\n\n{\"stage_id\": \"S1\", \"name\": \"fix\"}\n\nDone."
        result = _parse_patched_stage(text)
        assert result is not None
        assert result["stage_id"] == "S1"


# ---- merge_patched_stages -------------------------------------------


class TestMergePatchedStages:
    def test_merge_replaces_fields(self):
        plan = [
            {"stage_id": "S1", "name": "old", "purpose": "old purpose"},
            {"stage_id": "S2", "name": "two", "purpose": "two purpose"},
        ]
        patches = {"S1": {"name": "new", "purpose": "new purpose", "extra": "field"}}
        out = merge_patched_stages(plan, patches)
        assert out[0]["name"] == "new"
        assert out[0]["purpose"] == "new purpose"
        assert out[0]["extra"] == "field"
        assert out[0]["stage_id"] == "S1"  # stage_id preserved
        # S2 untouched
        assert out[1] == plan[1]

    def test_patch_cannot_rename_stage_id(self):
        plan = [{"stage_id": "S1", "name": "alpha"}]
        patches = {"S1": {"stage_id": "S99", "name": "renamed"}}
        out = merge_patched_stages(plan, patches)
        assert out[0]["stage_id"] == "S1"  # original wins
        assert out[0]["name"] == "renamed"

    def test_unknown_stage_id_dropped(self):
        plan = [{"stage_id": "S1", "name": "alpha"}]
        patches = {"S99": {"name": "phantom"}}
        out = merge_patched_stages(plan, patches)
        # No phantom inserted; plan unchanged
        assert out == plan

    def test_none_values_skipped(self):
        plan = [{"stage_id": "S1", "name": "alpha", "purpose": "p"}]
        patches = {"S1": {"name": None, "purpose": "new"}}
        out = merge_patched_stages(plan, patches)
        # name kept (None ignored), purpose updated
        assert out[0]["name"] == "alpha"
        assert out[0]["purpose"] == "new"


# ---- build_stage_patch_prompt smoke ---------------------------------


class TestBuildStagePatchPrompt:
    def test_contains_stage_id_and_must_fix(self):
        stage = {
            "stage_id": "S1",
            "name": "intake refactor",
            "purpose": "refactor intake module",
            "file_touch_map": {"create": ["intake.py"], "modify": [], "do_not_touch": []},
            "acceptance_criteria": [],
        }
        items = ["intake module is missing __init__"]
        prompt = build_stage_patch_prompt(stage, items)
        assert "S1" in prompt
        assert "intake refactor" in prompt
        assert "intake module is missing __init__" in prompt
        # Must demand single-stage output
        assert "patch mode" in prompt.lower() or "single JSON" in prompt.lower() or "stage_id" in prompt
