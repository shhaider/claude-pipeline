"""Shared state for the LangGraph pipeline.

Each node receives the full PipelineState, mutates a slice, and returns
the updated state. LangGraph reduces these slices into the persisted
state via the default channel behaviour (last-write-wins per key).
"""

from __future__ import annotations

from typing import Any, TypedDict


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


class ContractDeliverable(TypedDict, total=False):
    """One item from contract_writer's output."""

    id: str  # D1, D2, ...
    name: str
    description: str
    success_criteria: list[str]
    source_goal: str


class Contract(TypedDict, total=False):
    """contract_writer's full output (port of metabuilder's contract shape)."""

    contract_title: str
    deliverables: list[ContractDeliverable]
    ambiguity_flags: list[dict[str, str]]
    total_deliverables: int
    verification: dict[str, Any]


class Stage(TypedDict, total=False):
    """One unit of work in the plan. Implementer consumes one Stage per
    `claude --print` invocation.

    Two shapes supported:
      - v0.1 MVP (flat): {name, description, file_touch_map: [paths]}
      - v0.2 pack_planner (metabuilder): {stage_id, name, purpose, role,
        file_touch_map: {create, modify, do_not_touch}, acceptance_criteria,
        depends_on, backward_compat_notes}

    The current_stage_idx machinery in graph.py treats them uniformly —
    it only cares about ordering and length.
    """

    name: str
    description: str
    file_touch_map: Any  # list[str] (v0.1) or {create, modify, do_not_touch} (v0.2)
    # v0.2 fields
    stage_id: str
    purpose: str
    role: str
    acceptance_criteria: list[dict[str, str]]
    depends_on: list[str]
    backward_compat_notes: str
    # filled in by prompt-expansion node
    prompt_path: str
    expanded_prompt: str


class Plan(TypedDict, total=False):
    """pack_planner's full output."""

    plan_title: str
    stages: list[Stage]
    recommended_first_stage: str
    estimated_risk: str
    risk_rationale: str
    assumption_audit: dict[str, Any]
    verification: dict[str, Any]


class VerifyReport(TypedDict, total=False):
    passed: bool
    summary: str
    failing_tests: list[str]
    suggested_fix: str


class PackReviewerVerdict(TypedDict, total=False):
    """Output of pack_reviewer (12_pack_reviewer.md)."""

    must_fix: list[str]
    should_fix: list[str]
    notes: list[str]
    passed: bool
    hindsight: str  # one sentence + classification
    verification: str


class ReasoningConcern(TypedDict, total=False):
    category: str
    severity: str
    description: str
    fix: str


class ReasoningReviewerVerdict(TypedDict, total=False):
    """Output of software_reasoning_reviewer (34_software_reasoning_reviewer.md)."""

    reasoning_verdict: str  # PASS | CONCERN | FAIL
    overall_assessment: str
    concerns: list[ReasoningConcern]
    blocking_concerns: list[str]


class GovernanceFinding(TypedDict, total=False):
    criterion: str
    result: str
    note: str


class GovernanceVerdict(TypedDict, total=False):
    """Output of executive_governance_reviewer (08_*) (possibly per repair round)."""

    governance_verdict: str  # PASS | FAIL | NEEDS_REVISION
    overall_assessment: str
    findings: list[GovernanceFinding]
    blocking_issues: list[str]
    repair_round: int  # 0 = initial; 1..N = after repair


class GatekeeperVerdict(TypedDict, total=False):
    """Output of release_gatekeeper (19_release_gatekeeper.md)."""

    decision: str  # PASS | FAIL | BLOCKED
    rationale: str
    unresolved_items: list[str]
    verification: str


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
    research_packet: dict[str, Any]  # parsed JSON if research returns structured form
    excerpts: str  # gathered codebase excerpts (from excerpts.py)

    contract: Contract  # contract_writer output
    plan_meta: Plan  # full pack_planner output (with risk/assumption_audit)
    plan: list[Stage]  # ordered stages — flat list for graph iteration

    plan_correction_attempted: bool  # set by completeness gate

    current_stage_idx: int  # which stage is being implemented right now
    code_summary: str  # what was changed, one paragraph
    code_session_id: str  # Claude Code session id shared across stages (resume)
    code_diff: str  # `git diff` against base_branch after coding finished
    verify: VerifyReport

    # v0.3 review ladder
    pack_review: PackReviewerVerdict
    reasoning_review: ReasoningReviewerVerdict
    governance_review: GovernanceVerdict
    governance_repair_rounds: int  # how many repair rounds executed
    governance_repair_log: list[dict[str, Any]]  # audit trail per round
    gatekeeper: GatekeeperVerdict

    # Terminal
    pr_url: str
    pr_number: int

    # Bookkeeping
    retry_count: int  # how many times verify has looped back to code
    error: str | None  # last error message if a node failed
