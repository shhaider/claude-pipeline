"""Pure-Python tests for the system_gap_analyst node + its
integration into plan_node.

No tests in this module invoke `claude --print` or spawn
subprocesses — we exercise the pure packet builder and the
plan-prompt renderer directly.
"""

from __future__ import annotations

from claude_pipeline.nodes.plan import build_plan_prompt
from claude_pipeline.nodes.system_gap_analyst import (
    LENSES,
    build_gap_analysis_packet,
)


LENS_NAMES = [name for name, _ in LENSES]


def _base_state() -> dict:
    return {
        "run_id": "test-run",
        "repo": "shhaider/claude-pipeline",
        "issue_number": 9,
        "worktree_path": "/tmp/test-worktree",
        "issue_title": "Port system_gap_analyst adversarial pre-lane",
        "issue_body": "Insert system_gap_analyst between research and contract.",
        "intake": {
            "task_type": "new_feature",
            "complexity_tier": 3,
            "scope_plan": "Add adversarial gap pass before contract.",
            "risk_flags": ["llm_routing"],
            "right_thing_answer": "Yes — catches unstated dependencies.",
            "acceptance_criteria": [
                "Node exists",
                "Graph rewired",
                "Tests pass",
            ],
            "wiring_plan": "graph.py, plan.py, state.py, new node module",
        },
        "research_brief": (
            "## Current code shape\n\n"
            "The pipeline has intake -> research -> plan -> code -> verify -> pr.\n"
            "research_node returns a markdown brief at src/claude_pipeline/nodes/research.py:50.\n"
        ),
    }


def test_packet_contains_all_eight_lenses():
    """(a) The user packet must spell out every one of the 8 named
    lenses so the model walks each one explicitly."""
    packet = build_gap_analysis_packet(_base_state())
    assert len(LENS_NAMES) == 8, "expected exactly 8 lenses"
    for name in LENS_NAMES:
        assert name in packet, f"lens name missing from packet: {name}"


def test_packet_includes_intake_and_research():
    """(b) The packet must inject intake decisions AND the research
    brief content so the analyst can reason against the actual
    framing."""
    state = _base_state()
    packet = build_gap_analysis_packet(state)

    # Intake values present (rendered via json.dumps so we look for
    # distinctive field values, not the surrounding JSON syntax).
    assert state["intake"]["scope_plan"] in packet
    assert state["intake"]["right_thing_answer"] in packet
    assert "new_feature" in packet
    assert "llm_routing" in packet

    # Research brief present verbatim, under the codebaseAnchor block.
    assert "codebaseAnchor" in packet
    assert "intake -> research -> plan -> code -> verify -> pr" in packet
    assert "src/claude_pipeline/nodes/research.py:50" in packet

    # Issue framing too — the analyst needs the original ask.
    assert "Port system_gap_analyst adversarial pre-lane" in packet


def test_blocking_gaps_injected_into_plan_prompt_as_mandatory():
    """(c) When state['gap_analysis']['blocking_gaps'] is non-empty,
    plan_node's rendered prompt must contain a MANDATORY ADDITIONAL
    DELIVERABLES section that names each blocking gap."""
    state = _base_state()
    state["gap_analysis"] = {
        "blocking_gaps": [
            {
                "lens": "infrastructure-assumed-but-not-mentioned",
                "gap": "No CLAUDE_CONFIG_DIR check in CI workflow.",
                "recommendation": "Add a precondition stage that asserts the env var exists.",
            },
            {
                "lens": "silent-failure",
                "gap": "research_node swallows empty briefs and continues.",
                "recommendation": "Convert empty brief to an error state.",
            },
        ],
        "advisory_gaps": [],
        "summary": "Two infra/silent-failure gaps must be fixed before planning.",
    }

    prompt = build_plan_prompt(state)

    # The mandatory section header is present.
    assert "MANDATORY ADDITIONAL DELIVERABLES" in prompt

    # Each blocking gap's substance shows up under that header.
    for gap in state["gap_analysis"]["blocking_gaps"]:
        assert gap["gap"] in prompt
        assert gap["recommendation"] in prompt
        assert gap["lens"] in prompt

    # And the planner's own contract (the rest of the prompt) is
    # still intact.
    assert "JSON array of stages" in prompt


def test_advisory_gaps_present_but_not_marked_mandatory():
    """(d) Advisory gaps appear in the prompt but NOT under the
    MANDATORY header; they sit under a non-mandatory section."""
    state = _base_state()
    advisory_gap_text = "Logging format for the new node is unspecified."
    state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [
            {
                "lens": "developer-contract-completeness",
                "gap": advisory_gap_text,
                "recommendation": "Pick structured JSON logs or note free-form.",
            }
        ],
        "summary": "Minor contract clarity nits only.",
    }

    prompt = build_plan_prompt(state)

    # MANDATORY header MUST NOT be present (no blocking gaps).
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt

    # Non-mandatory advisory header is present.
    assert "Advisory gaps" in prompt
    assert "suggestions, not requirements" in prompt

    # The advisory gap text is in the prompt.
    assert advisory_gap_text in prompt

    # And specifically: the advisory text is NOT under any text that
    # would mark it mandatory. Split on the advisory header and
    # confirm the gap text lives in the part AFTER the header.
    after_header = prompt.split("Advisory gaps")[1]
    assert advisory_gap_text in after_header


def test_empty_gap_analysis_renders_cleanly():
    """Belt-and-braces: when gap_analysis is absent or both lists are
    empty, the planner prompt must render with no orphan headers and
    no broken format placeholders."""
    # Case 1: gap_analysis key absent.
    prompt = build_plan_prompt(_base_state())
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "Advisory gaps" not in prompt
    assert "{gap_block}" not in prompt  # template fully rendered

    # Case 2: gap_analysis present but both lists empty.
    state = _base_state()
    state["gap_analysis"] = {
        "blocking_gaps": [],
        "advisory_gaps": [],
        "summary": "No gaps found.",
    }
    prompt = build_plan_prompt(state)
    assert "MANDATORY ADDITIONAL DELIVERABLES" not in prompt
    assert "Advisory gaps" not in prompt
