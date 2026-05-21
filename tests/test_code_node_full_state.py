"""Tests for the v0.3.1 full-state implementer prompt wrapper.

These tests exercise `build_wrapped_prompt` directly. No LLM calls;
no subprocess; pure-Python only. The fixtures simulate the
PipelineState as it would appear when the code node fires on, say,
stage 2 of 4.
"""

from __future__ import annotations

import os

import pytest

from claude_pipeline.nodes.code import (
    _full_state_flag,
    build_wrapped_prompt,
)


# --- Fixtures ----------------------------------------------------------------


@pytest.fixture
def expanded_prompt() -> str:
    """A stand-in for a real per-stage expansion (~1 KB)."""
    return (
        "## 1. Truth boundary\n\n"
        "Known: foo exists at bar.py:42.\n\n"
        "## 2. Do not claim completion unless\n\n"
        "- test_foo passes\n\n"
        "## 3. Goal\n\n"
        "Add foo_node module.\n\n"
        "## 11. Stop condition\n\n"
        "Stage complete: S2\n"
    )


@pytest.fixture
def state_full(expanded_prompt: str) -> dict:
    """A PipelineState dict matching the shape after research + contract +
    plan + prompt_expand have all run, and we're mid-implementation
    on stage 2 of 4."""
    return {
        "run_id": "test-run-abc",
        "repo": "shhaider/claude-pipeline",
        "issue_number": 9,
        "issue_title": "Adversarial gap-analysis pre-lane (system_gap_analyst)",
        "issue_body": (
            "We need an adversarial reviewer node that runs BEFORE the contract "
            "to catch infrastructure-assumed-but-not-mentioned gaps and "
            "silent-failure paths.\n\nAcceptance:\n- new node at nodes/system_gap_analyst.py\n"
            "- 8 named lenses verbatim\n- wired in graph.py"
        ),
        "worktree_path": "/tmp/wt-test",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "risk_flags": ["new-node", "graph-wiring"],
            "right_thing_answer": "Adversarial gap analysis catches issues a single planner would miss.",
            "scope_plan": "Add the node, wire it, write tests.",
            "acceptance_criteria": [
                "nodes/system_gap_analyst.py exists",
                "8 named lenses appear verbatim in the packet",
                "node wired into graph.py between research and contract",
                "pytest suite passes",
            ],
            "wiring_plan": "Insert after research, before contract.",
        },
        "research_brief": (
            "# Research brief\n\nrun_claude lives at src/claude_pipeline/claude.py:111. "
            "extract_json at line 273. PipelineState at state.py:43. Existing nodes "
            "follow the pattern `def X_node(state) -> dict`."
        ),
        "contract": {
            "contract_title": "system_gap_analyst lane contract",
            "deliverables": [
                {
                    "id": "D1",
                    "name": "system_gap_analyst.py",
                    "description": "the new node module",
                    "success_criteria": ["module imports cleanly", "exports system_gap_analyst_node"],
                },
                {
                    "id": "D2",
                    "name": "35_system_gap_analyst.md",
                    "description": "verbatim role prompt",
                    "success_criteria": ["file exists at prompts/metabuilder/35_system_gap_analyst.md"],
                },
                {
                    "id": "D3",
                    "name": "tests/test_system_gap_analyst.py",
                    "description": "pytest coverage",
                    "success_criteria": ["pytest -q passes"],
                },
            ],
        },
        "plan": [
            {
                "stage_id": "S1",
                "name": "Land verbatim prompt and extend state schema",
                "purpose": "Drop the role prompt + extend PipelineState with gap_analysis key.",
                "file_touch_map": {
                    "create": ["prompts/metabuilder/35_system_gap_analyst.md"],
                    "modify": ["src/claude_pipeline/state.py"],
                    "do_not_touch": [],
                },
            },
            {
                "stage_id": "S2",
                "name": "Implement system_gap_analyst node",
                "purpose": "Create the node module that calls Claude with the 8 lenses.",
                "file_touch_map": {
                    "create": ["src/claude_pipeline/nodes/system_gap_analyst.py"],
                    "modify": [],
                    "do_not_touch": ["src/claude_pipeline/graph.py"],
                },
                "expanded_prompt": expanded_prompt,
            },
            {
                "stage_id": "S3",
                "name": "Wire node into graph",
                "purpose": "Insert the new node into graph.py.",
                "file_touch_map": {
                    "create": [],
                    "modify": ["src/claude_pipeline/graph.py"],
                    "do_not_touch": [],
                },
            },
            {
                "stage_id": "S4",
                "name": "Add pytest suite + update README",
                "purpose": "Tests + docs.",
                "file_touch_map": {
                    "create": ["tests/test_system_gap_analyst.py"],
                    "modify": ["README.md"],
                    "do_not_touch": [],
                },
            },
        ],
        "current_stage_idx": 1,  # mid-pipeline: stage S2 (index 1)
        "code_summary": (
            "Created prompts/metabuilder/35_system_gap_analyst.md verbatim from the "
            "metabuilder source, and extended PipelineState to include gap_analysis."
        ),
    }


# --- Tests ------------------------------------------------------------------


class TestWrappedPromptIncludesIssue:
    def test_includes_issue_body_verbatim(self, state_full: dict, expanded_prompt: str) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        # Issue body MUST appear verbatim — that's the whole point of Fix 3.
        assert state_full["issue_body"] in wrapped

    def test_includes_issue_number_and_title(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        assert "Issue #9" in wrapped
        assert state_full["issue_title"] in wrapped


class TestWrappedPromptIncludesAcceptanceCriteria:
    def test_all_intake_acceptance_criteria_appear(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        for criterion in state_full["intake"]["acceptance_criteria"]:
            assert criterion in wrapped, f"missing acceptance criterion: {criterion}"


class TestWrappedPromptIncludesPriorStages:
    def test_prior_stage_summary_appears(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        # The most recent code_summary (from S1) must be visible.
        assert "Created prompts/metabuilder/35_system_gap_analyst.md" in wrapped

    def test_prior_stage_name_appears(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        # The S1 stage name should be in the prior-stages block.
        assert "Land verbatim prompt and extend state schema" in wrapped

    def test_first_stage_has_no_prior_block_content(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        # On stage 0 there should be no prior stages.
        st = dict(state_full)
        st["current_stage_idx"] = 0
        st["code_summary"] = ""
        wrapped = build_wrapped_prompt(st, expanded_prompt)
        assert "(none — this is the first stage)" in wrapped


class TestWrappedPromptIncludesExpansion:
    def test_expansion_appears_verbatim(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        # The expansion content must be present in full — it's the
        # planner's per-stage discipline, we just frame it inside more
        # context.
        assert expanded_prompt in wrapped

    def test_this_stage_marker_present(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        # The "THIS STAGE" header tells the implementer where its narrow
        # work begins.
        assert "## THIS STAGE — your specific work" in wrapped
        assert "stage 2 of 4" in wrapped


class TestWrappedPromptIncludesContractAndPlan:
    def test_all_deliverables_appear(self, state_full: dict, expanded_prompt: str) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        for d in state_full["contract"]["deliverables"]:
            assert d["id"] in wrapped
            assert d["name"] in wrapped

    def test_all_plan_stage_names_appear(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        for stage in state_full["plan"]:
            assert stage["name"] in wrapped


class TestWrappedPromptSizeIsReasonable:
    def test_under_30kb_on_typical_state(
        self, state_full: dict, expanded_prompt: str
    ) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        size_kb = len(wrapped.encode("utf-8")) / 1024
        assert size_kb <= 30, f"wrapped prompt is {size_kb:.1f} KB, expected <= 30 KB"


class TestWrappedPromptIncludesWorkingPrinciple:
    def test_footer_present(self, state_full: dict, expanded_prompt: str) -> None:
        wrapped = build_wrapped_prompt(state_full, expanded_prompt)
        assert "Working principle" in wrapped
        assert "accountable for the WHOLE acceptance criteria list" in wrapped


class TestDefensiveAgainstMissingFields:
    def test_minimal_state_does_not_crash(self, expanded_prompt: str) -> None:
        # Pipeline could fire the implementer with a sparse state if
        # upstream nodes errored. Wrapper must not raise.
        wrapped = build_wrapped_prompt(
            {"current_stage_idx": 0, "plan": [{"name": "only-stage"}]},
            expanded_prompt,
        )
        assert "Working principle" in wrapped
        assert expanded_prompt in wrapped

    def test_string_risk_flags_handled(self, state_full: dict, expanded_prompt: str) -> None:
        st = dict(state_full)
        st_intake = dict(st["intake"])
        st_intake["risk_flags"] = "not-a-list"  # malformed upstream
        st["intake"] = st_intake
        # Should not raise.
        wrapped = build_wrapped_prompt(st, expanded_prompt)
        assert "not-a-list" in wrapped


class TestFullStateFlag:
    def test_default_is_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("IMPLEMENTER_INCLUDE_FULL_STATE", raising=False)
        assert _full_state_flag() is True

    def test_explicit_false_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for val in ("0", "false", "False", "NO", "off", ""):
            monkeypatch.setenv("IMPLEMENTER_INCLUDE_FULL_STATE", val)
            assert _full_state_flag() is False, f"expected False for {val!r}"

    def test_truthy_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for val in ("1", "true", "yes", "on"):
            monkeypatch.setenv("IMPLEMENTER_INCLUDE_FULL_STATE", val)
            assert _full_state_flag() is True, f"expected True for {val!r}"
