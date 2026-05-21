"""LangGraph wiring for the pipeline.

Builds the state machine:
   intake -> research -> system_gap_analyst -> plan -> code -> verify
      -> (loop back to code if FAIL, max 2 retries) -> pr

system_gap_analyst is an adversarial pre-lane between research and plan
that surfaces unstated dependencies / silent-failure modes the plan must
cover. See nodes/system_gap_analyst.py.

Persists state to SQLite after every node so crashes can resume.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from claude_pipeline.nodes.code import code_node
from claude_pipeline.nodes.intake import intake_node
from claude_pipeline.nodes.plan import plan_node
from claude_pipeline.nodes.pr import pr_node
from claude_pipeline.nodes.research import research_node
from claude_pipeline.nodes.system_gap_analyst import system_gap_analyst_node
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
    smarter v0.2 would inspect which stage's files broke things.
    """
    log.info("retry_code: bumping retry_count and re-running last stage")
    return {
        "current_stage_idx": max(0, len(state.get("plan", [])) - 1),
        "retry_count": state.get("retry_count", 0) + 1,
    }


def build_graph(checkpoint_db: Path | str):
    """Compile the graph with a SQLite checkpointer pinned to
    checkpoint_db. Returns the compiled CompiledGraph."""
    g = StateGraph(PipelineState)
    g.add_node("intake", intake_node)
    g.add_node("research", research_node)
    g.add_node("system_gap_analyst", system_gap_analyst_node)
    g.add_node("plan", plan_node)
    g.add_node("code", code_node)
    g.add_node("verify", verify_node)
    g.add_node("retry_code", _retry_with_guidance)
    g.add_node("pr", pr_node)

    g.add_edge(START, "intake")
    g.add_edge("intake", "research")
    g.add_edge("research", "system_gap_analyst")
    g.add_edge("system_gap_analyst", "plan")
    g.add_edge("plan", "code")
    # After code: more stages? loop back to code; else verify.
    g.add_conditional_edges(
        "code",
        _has_more_stages,
        {"code": "code", "verify": "verify"},
    )
    # After verify: pass → pr; fail with retries left → retry_code → code; fail no retries → pr anyway.
    g.add_conditional_edges(
        "verify",
        should_retry,
        {"pr": "pr", "retry_code": "retry_code"},
    )
    g.add_edge("retry_code", "code")
    g.add_edge("pr", END)

    # SqliteSaver wraps a sqlite3 connection. `from_conn_string` is a
    # context manager in current langgraph-checkpoint-sqlite, so we
    # open the connection directly and let it live for the graph's
    # lifetime. check_same_thread=False because LangGraph may dispatch
    # node functions from worker threads.
    conn = sqlite3.connect(str(checkpoint_db), check_same_thread=False)
    saver = SqliteSaver(conn)
    return g.compile(checkpointer=saver)


def render_mermaid() -> str:
    """Render the graph as a Mermaid diagram (for docs / debugging).
    Uses an in-memory uncompiled graph so this works without a DB."""
    g = StateGraph(PipelineState)
    g.add_node("intake", intake_node)
    g.add_node("research", research_node)
    g.add_node("system_gap_analyst", system_gap_analyst_node)
    g.add_node("plan", plan_node)
    g.add_node("code", code_node)
    g.add_node("verify", verify_node)
    g.add_node("retry_code", _retry_with_guidance)
    g.add_node("pr", pr_node)
    g.add_edge(START, "intake")
    g.add_edge("intake", "research")
    g.add_edge("research", "system_gap_analyst")
    g.add_edge("system_gap_analyst", "plan")
    g.add_edge("plan", "code")
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
    compiled = g.compile()
    return compiled.get_graph().draw_mermaid()
