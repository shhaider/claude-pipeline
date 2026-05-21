"""LangGraph wiring for the pipeline (v0.3).

Topology:

    intake -> research -> contract -> plan -> prompt_expand
                                                 |
                                                 v
                                       code (shared session across stages)
                                                 |
                                       (more stages? -> code; else -> verify)
                                                 |
                                                 v
                                              verify (tests only)
                                                 |
                                                 v
                                       pack_reviewer (fresh)
                                                 |
                                                 v
                                     reasoning_reviewer (fresh)
                                                 |
                                                 v
                                    governance_reviewer (fresh)
                                                 |
                                       (PASS -> release_gatekeeper;
                                        NEEDS_REVISION/FAIL -> governance_repair
                                                        -> release_gatekeeper)
                                                 |
                                                 v
                                          release_gatekeeper
                                                 |
                                       (PASS -> pr; FAIL/BLOCKED -> error_exit)
                                                 |
                                                 v
                                                pr / error_exit

v0.3 changes vs v0.2:
  - code_node uses a shared Claude session across stages (resume).
  - Verify node only runs tests; acceptance is judged by reviewers.
  - 4-role review ladder replaces the single verify-judges-everything node.
  - governance_repair_loop with max 2 rounds.
  - retry_code edge removed (governance_repair owns repair).

Persists state to SQLite after every node so crashes can resume.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from claude_pipeline.nodes.code import code_node
from claude_pipeline.nodes.contract import contract_node
from claude_pipeline.nodes.governance_repair import governance_repair_node
from claude_pipeline.nodes.governance_reviewer import governance_reviewer_node
from claude_pipeline.nodes.intake import intake_node
from claude_pipeline.nodes.pack_reviewer import pack_reviewer_node
from claude_pipeline.nodes.plan import plan_node
from claude_pipeline.nodes.pr import pr_node
from claude_pipeline.nodes.prompt_expand import prompt_expand_node
from claude_pipeline.nodes.reasoning_reviewer import reasoning_reviewer_node
from claude_pipeline.nodes.release_gatekeeper import release_gatekeeper_node
from claude_pipeline.nodes.research import research_node
from claude_pipeline.nodes.verify import verify_node
from claude_pipeline.state import PipelineState

log = logging.getLogger(__name__)


def _has_more_stages(state: PipelineState) -> str:
    """After code_node: are there more stages? Branches to next code call
    or to verify."""
    plan = state.get("plan", [])
    idx = state.get("current_stage_idx", 0)
    if idx < len(plan):
        return "code"  # keep coding
    return "verify"


def _governance_route(state: PipelineState) -> str:
    """After governance_reviewer: PASS -> gatekeeper; else -> repair."""
    gov = state.get("governance_review", {})
    verdict = str(gov.get("governance_verdict", "")).upper()
    if verdict == "PASS":
        return "release_gatekeeper"
    return "governance_repair"


def _gatekeeper_route(state: PipelineState) -> str:
    """After release_gatekeeper: PASS -> pr; FAIL/BLOCKED -> error_exit."""
    gk = state.get("gatekeeper", {})
    decision = str(gk.get("decision", "")).upper()
    if decision == "PASS":
        return "pr"
    return "error_exit"


def _error_exit(state: PipelineState) -> dict:
    """Terminal node when gatekeeper says FAIL/BLOCKED. No PR is created;
    the caller inspects state to decide next steps. v0.4 will add
    human-in-the-loop here."""
    gk = state.get("gatekeeper", {})
    decision = str(gk.get("decision", "?"))
    unresolved = gk.get("unresolved_items", []) or []
    rationale = gk.get("rationale", "")
    log.warning(
        "error_exit: gatekeeper decision=%s unresolved=%s rationale=%s",
        decision,
        unresolved,
        rationale[:200],
    )
    return {
        "error": f"release_gatekeeper {decision}: {rationale[:200]}",
    }


def _add_nodes(g: StateGraph) -> None:
    g.add_node("intake", intake_node)
    g.add_node("research", research_node)
    g.add_node("contract", contract_node)
    g.add_node("plan", plan_node)
    g.add_node("prompt_expand", prompt_expand_node)
    g.add_node("code", code_node)
    g.add_node("verify", verify_node)
    g.add_node("pack_reviewer", pack_reviewer_node)
    g.add_node("reasoning_reviewer", reasoning_reviewer_node)
    g.add_node("governance_reviewer", governance_reviewer_node)
    g.add_node("governance_repair", governance_repair_node)
    g.add_node("release_gatekeeper", release_gatekeeper_node)
    g.add_node("pr", pr_node)
    g.add_node("error_exit", _error_exit)


def _add_edges(g: StateGraph) -> None:
    g.add_edge(START, "intake")
    g.add_edge("intake", "research")
    g.add_edge("research", "contract")
    g.add_edge("contract", "plan")
    g.add_edge("plan", "prompt_expand")
    g.add_edge("prompt_expand", "code")
    g.add_conditional_edges(
        "code",
        _has_more_stages,
        {"code": "code", "verify": "verify"},
    )
    g.add_edge("verify", "pack_reviewer")
    g.add_edge("pack_reviewer", "reasoning_reviewer")
    g.add_edge("reasoning_reviewer", "governance_reviewer")
    g.add_conditional_edges(
        "governance_reviewer",
        _governance_route,
        {
            "release_gatekeeper": "release_gatekeeper",
            "governance_repair": "governance_repair",
        },
    )
    g.add_edge("governance_repair", "release_gatekeeper")
    g.add_conditional_edges(
        "release_gatekeeper",
        _gatekeeper_route,
        {"pr": "pr", "error_exit": "error_exit"},
    )
    g.add_edge("pr", END)
    g.add_edge("error_exit", END)


def build_graph(checkpoint_db: Path | str):
    """Compile the graph with a SQLite checkpointer pinned to
    checkpoint_db. Returns the compiled CompiledGraph."""
    g = StateGraph(PipelineState)
    _add_nodes(g)
    _add_edges(g)

    # SqliteSaver wraps a sqlite3 connection.
    conn = sqlite3.connect(str(checkpoint_db), check_same_thread=False)
    saver = SqliteSaver(conn)
    return g.compile(checkpointer=saver)


def render_mermaid() -> str:
    """Render the graph as a Mermaid diagram (for docs / debugging).
    Uses an in-memory uncompiled graph so this works without a DB."""
    g = StateGraph(PipelineState)
    _add_nodes(g)
    _add_edges(g)
    compiled = g.compile()
    return compiled.get_graph().draw_mermaid()
