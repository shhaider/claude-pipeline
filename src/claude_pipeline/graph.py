"""LangGraph wiring for the pipeline (v0.2).

Topology:

    intake -> research -> contract -> plan
                                       |
                                       v
                            prompt_expand (parallel per stage)
                                       |
                                       v
                                     code (one stage per call)
                                       |
                  (more stages? -> code; else -> verify)
                                       |
                                       v
                                    verify
                                       |
                  (pass? -> pr; fail+retries? -> retry_code -> code;
                   fail+no-retries? -> pr)

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
from claude_pipeline.nodes.intake import intake_node
from claude_pipeline.nodes.plan import plan_node
from claude_pipeline.nodes.pr import pr_node
from claude_pipeline.nodes.prompt_expand import prompt_expand_node
from claude_pipeline.nodes.research import research_node
from claude_pipeline.nodes.verify import MAX_RETRIES, should_retry, verify_node
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


def _retry_with_guidance(state: PipelineState) -> dict:
    """Internal node that re-points current_stage_idx back to the last
    stage when verify says FAIL, so code_node re-runs that stage with
    the verify guidance in the prompt context.

    For MVP we re-run only the final stage and bump retry_count. A
    smarter v0.3 would inspect which stage's files broke things.
    """
    log.info("retry_code: bumping retry_count and re-running last stage")
    return {
        "current_stage_idx": max(0, len(state.get("plan", [])) - 1),
        "retry_count": state.get("retry_count", 0) + 1,
    }


def _add_nodes(g: StateGraph) -> None:
    g.add_node("intake", intake_node)
    g.add_node("research", research_node)
    g.add_node("contract", contract_node)
    g.add_node("plan", plan_node)
    g.add_node("prompt_expand", prompt_expand_node)
    g.add_node("code", code_node)
    g.add_node("verify", verify_node)
    g.add_node("retry_code", _retry_with_guidance)
    g.add_node("pr", pr_node)


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
    g.add_conditional_edges(
        "verify",
        should_retry,
        {"pr": "pr", "retry_code": "retry_code"},
    )
    g.add_edge("retry_code", "code")
    g.add_edge("pr", END)


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
