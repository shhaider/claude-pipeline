"""Shared state for the LangGraph pipeline.

Each node receives the full PipelineState, mutates a slice, and returns
the updated state. LangGraph reduces these slices into the persisted
state via the default channel behaviour (last-write-wins per key).
"""

from __future__ import annotations

from typing import TypedDict


class IntakeDecisions(TypedDict, total=False):
    """The seven autonomous-resolver outputs (mirrors metabuilder's
    `autonomous_software_resolver.js` shape)."""

    task_type: str  # bug_fix | new_feature | refactor | test_addition | documentation | exploration
    complexity_tier: int  # 1 trivial, 2 moderate, 3 complex
    scope_plan: str
    risk_flags: list[str]
    right_thing_answer: str
    acceptance_criteria: list[str]
    wiring_plan: str


class Stage(TypedDict, total=False):
    """One unit of work in the plan. Implementer consumes one Stage per
    `claude --print` invocation."""

    name: str
    description: str
    file_touch_map: list[str]  # files this stage is allowed to touch
    prompt_path: str  # filled in by prompt-expansion node


class VerifyReport(TypedDict, total=False):
    passed: bool
    summary: str
    failing_tests: list[str]
    suggested_fix: str


class PipelineState(TypedDict, total=False):
    """End-to-end pipeline state. Persisted to SQLite checkpoint after
    each node. Resume reloads this dict and continues from the next node.
    """

    # Inputs (set once by the CLI on run start)
    run_id: str
    repo: str  # "owner/name"
    issue_number: int
    worktree_path: str  # filesystem path to the per-run git worktree
    base_branch: str  # what to branch from (typically 'main' or 'dev')
    feature_branch: str  # the branch this run will push

    # Phase outputs (one per node)
    issue_title: str
    issue_body: str
    intake: IntakeDecisions
    research_brief: str  # markdown — research-node output
    plan: list[Stage]  # ordered stages from plan node
    current_stage_idx: int  # which stage is being implemented right now
    code_summary: str  # what was changed, one paragraph
    verify: VerifyReport
    gap_analysis: dict

    # Terminal
    pr_url: str
    pr_number: int

    # Bookkeeping
    retry_count: int  # how many times verify has looped back to code
    error: str | None  # last error message if a node failed
