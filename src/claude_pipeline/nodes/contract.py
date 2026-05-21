"""Contract-writer packet builder with gap-analysis injection."""

from __future__ import annotations


def build_contract_packet(state: dict) -> str:
    intake = state.get("intake", {}) or {}
    research_brief = state.get("research_brief", "") or ""
    gap_analysis = state.get("gap_analysis") or {}

    blocking_gaps = gap_analysis.get("blocking_gaps") or []
    advisory_gaps = gap_analysis.get("advisory_gaps") or []
    gap_summary = gap_analysis.get("summary") or ""

    acceptance_criteria = intake.get("acceptance_criteria") or []

    lines: list[str] = []

    lines.append("## PRIMARY GOAL")
    lines.append(f"task_type: {intake.get('task_type', '(not set)')}")
    lines.append(f"complexity_tier: {intake.get('complexity_tier', '(not set)')}")
    lines.append(f"scope_plan: {intake.get('scope_plan', '(not set)')}")
    lines.append(f"right_thing_answer: {intake.get('right_thing_answer', '(not set)')}")
    lines.append("")

    if acceptance_criteria:
        lines.append("## ACCEPTANCE CRITERIA")
        for c in acceptance_criteria:
            lines.append(f"- {c}")
        lines.append("")

    if research_brief:
        lines.append("## RESEARCH BRIEF")
        lines.append(research_brief)
        lines.append("")

    if gap_summary:
        lines.append("## GAP ANALYSIS SUMMARY")
        lines.append(gap_summary)
        lines.append("")

    if blocking_gaps:
        lines.append("## MANDATORY ADDITIONAL DELIVERABLES")
        lines.append(
            "The following blocking gaps MUST be addressed as explicit deliverables. "
            "Each gap below must appear in at least one stage's acceptance criteria."
        )
        lines.append("")
        for gap in blocking_gaps:
            lens = gap.get("lens", "(unknown)")
            description = gap.get("gap") or gap.get("description", "")
            recommendation = gap.get("recommendation") or gap.get("fix", "")
            lines.append(f"- **[{lens}]** {description}")
            if recommendation:
                lines.append(f"  Recommendation: {recommendation}")
        lines.append("")

    if advisory_gaps:
        lines.append("## SUGGESTIONS")
        lines.append(
            "The following advisory gaps are non-blocking but should be considered."
        )
        lines.append("")
        for gap in advisory_gaps:
            lens = gap.get("lens", "(unknown)")
            description = gap.get("gap") or gap.get("description", "")
            recommendation = gap.get("recommendation") or gap.get("fix", "")
            lines.append(f"- **[{lens}]** {description}")
            if recommendation:
                lines.append(f"  Suggestion: {recommendation}")
        lines.append("")

    return "\n".join(lines)
