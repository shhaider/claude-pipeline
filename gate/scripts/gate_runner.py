#!/usr/bin/env python3
"""Script-backed runner for the Gate state machine.

The runner deliberately keeps deterministic mechanics outside the LLM:

- initialize a gate run and core ledgers;
- select the required gate profile from task kind, changed files, and prompt text;
- render compact prompts for judgment-heavy LLM review steps;
- optionally call a configured LLM command and write the step output artifact;
- invoke the existing deterministic package checker.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False


GATE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE_ROOT = GATE_DIR

PROFILE_ORDER = {
    "GATE_LITE": 1,
    "GATE_STANDARD": 2,
    "GATE_FULL": 3,
    "GATE_FULL_PLUS_DOMAIN_ADDENDUM": 4,
}

VALIDATION_MODES = {
    "NO_CHANGE",
    "FOCUSED_EVIDENCE",
    "FORMAL_GATE",
}

TASK_KINDS = {
    "no_change",
    "docs",
    "docs_process_policy",
    "tiny_test",
    "normal_impl",
    "hot_file",
    "migration",
    "runtime_state",
    "merge_verification",
    "release_verification",
    "production_wiring",
    "provider_model_routing",
    "gui_visible_workflow",
    "gate_change",
    "prompt_authoring",
    "evidence_package",
}

RISK_TIERS = {"D0", "D1", "D2", "D2_HOT", "D3", "D4"}

GUI_PATH_RE = re.compile(
    r"(^|/)(gui|client|frontend|public|pages|components)(/|$)"
    r"|(\.(jsx|tsx|vue|svelte|css|scss|html)$)"
    r"|(server_local\.js$)"
)
GUI_PROMPT_RE = re.compile(
    r"\b(gui|browser|frontend|front-end|ui|user-facing|chat interface|"
    r"playwright|dom)\b",
    re.IGNORECASE,
)
GUI_ACTION_PROMPT_RE = re.compile(
    r"\b(user|browser|gui|ui|frontend|front-end|screen|page|dom|playwright)\b"
    r".{0,80}\b(click|submit|type|navigate|see|visible|render|journey|form)\b"
    r"|\b(click|submit|type|navigate|see|visible|render|journey|form)\b"
    r".{0,80}\b(user|browser|gui|ui|frontend|front-end|screen|page|dom|playwright)\b",
    re.IGNORECASE | re.DOTALL,
)
PROVIDER_PROMPT_RE = re.compile(
    r"\b(provider|llm|openrouter)\b"
    r".{0,80}\b(route|router|routing|model|selection|id)\b"
    r"|\b(model)\s+(id|selection|routing|router|provider)\b"
    r"|\b(route|router|routing)\b.{0,80}\b(provider|llm|model id|model selection|openrouter)\b",
    re.IGNORECASE | re.DOTALL,
)
GUI_SCOPE_EXCLUSION_RE = re.compile(
    r"\b(no|non|not|without|exclude[sd]?|excluding)\b[-\s]*(gui|browser|frontend|front-end|ui)\b"
    r"|\b(no|non|not|without|exclude[sd]?|excluding)\b.{0,60}\b(gui|browser|frontend|front-end|ui)\b"
    r"|\b(gui|browser|frontend|front-end|ui)\b.{0,40}\b(no scope|out of scope|excluded|not touched|unchanged)\b",
    re.IGNORECASE | re.DOTALL,
)
PROVIDER_SCOPE_EXCLUSION_RE = re.compile(
    r"\b(no|non|not|without|exclude[sd]?|excluding)\b[-\s]*(provider|model|llm|openrouter)\b"
    r"|\b(no|non|not|without|exclude[sd]?|excluding)\b.{0,60}\b(provider|model|llm|openrouter)\b"
    r"|\b(provider|model|llm|openrouter)\b.{0,40}\b(no scope|out of scope|excluded|not touched|unchanged)\b",
    re.IGNORECASE | re.DOTALL,
)
PROD_PROMPT_RE = re.compile(r"\b(live behavior|production wiring|production caller|deploy|release)\b", re.IGNORECASE)
MERGE_PROMPT_RE = re.compile(r"\b(merge verification|merge gate|pr acceptance|pull request|branch protection)\b", re.IGNORECASE)
RUNTIME_PROMPT_RE = re.compile(r"\b(runtime state|checkpoint|resume|persistence|queue|concurrency)\b", re.IGNORECASE)
GATE_PROMPT_RE = re.compile(r"\b(gate state|gate profile|gate package|evidence package|review state machine)\b", re.IGNORECASE)

PROCESS_DOC_PREFIXES = (
    "docs/agent_coordination/",
    "docs/agent_rules/",
    "docs/roadmap/",
    "docs/subsystems/",
    "docs/metabuilder/",
)
PROCESS_DOC_FILES = {"agents.md", "claude.md", "readme.md"}
RUNTIME_PROMPT_PREFIXES = (
    "skills/",
    "prompts/",
    "runtime_prompts/",
)


@dataclass(frozen=True)
class StepDef:
    alias: str
    doc: str
    output: str
    in_progress: str | None = None
    default_complete: str | None = None
    decision_markers: tuple[tuple[str, str], ...] = ()
    llm_owned: bool = True


STEP_DEFS: dict[str, StepDef] = {
    "evidence_adequacy": StepDef(
        "evidence_adequacy",
        "01_EVIDENCE_ADEQUACY.md",
        "EVIDENCE_ADEQUACY_ASSESSMENT.md",
        "EVIDENCE_ADEQUACY_IN_PROGRESS",
        "EVIDENCE_ALREADY_ADEQUATE",
        (
            ("EVIDENCE_BLOCKED_REQUIRES_HUMAN", "EVIDENCE_BLOCKED_REQUIRES_HUMAN"),
            ("EVIDENCE_UPGRADE_REQUIRED", "EVIDENCE_UPGRADE_REQUIRED"),
            ("EVIDENCE_ALREADY_ADEQUATE", "EVIDENCE_ALREADY_ADEQUATE"),
        ),
    ),
    "test_plan": StepDef(
        "test_plan",
        "02_TEST_AND_EVIDENCE_PLAN.md",
        "TEST_AND_EVIDENCE_PLAN.md",
        "TEST_PLAN_IN_PROGRESS",
        "TEST_PLAN_COMPLETE",
    ),
    "evidence_consistency": StepDef(
        "evidence_consistency",
        "03_EVIDENCE_CONSISTENCY.md",
        "EVIDENCE_CONSISTENCY_REGISTER.md",
        "EVIDENCE_CONSISTENCY_IN_PROGRESS",
        "EVIDENCE_CONSISTENCY_PASS",
        (
            ("EVIDENCE_CONSISTENCY_BLOCKED", "EVIDENCE_CONSISTENCY_BLOCKED"),
            ("BLOCKING_CONTRADICTIONS_FOUND", "EVIDENCE_CONSISTENCY_BLOCKED"),
            ("PASS", "EVIDENCE_CONSISTENCY_PASS"),
        ),
    ),
    "enforcement": StepDef(
        "enforcement",
        "14_ENFORCEMENT_AUTHORITY_AUDIT.md",
        "ENFORCEMENT_AUTHORITY_AUDIT.md",
        "ENFORCEMENT_AUDIT_IN_PROGRESS",
        "ENFORCEMENT_AUDIT_PASS",
    ),
    "r1": StepDef(
        "r1",
        "05_R1_REQUIREMENTS.md",
        "COLD_REVIEW_REQUIREMENTS_AUDIT.md",
        "R1_IN_PROGRESS",
        "R1_COMPLETE",
    ),
    "r2": StepDef(
        "r2",
        "06_R2_ACTIVE_PROOF.md",
        "COLD_REVIEW_ACTIVE_PROOF_AUDIT.md",
        "R2_IN_PROGRESS",
        "R2_COMPLETE",
    ),
    "r3": StepDef(
        "r3",
        "07_R3_AI_PATTERNS.md",
        "COLD_REVIEW_AI_FAILURE_PATTERN_AUDIT.md",
        "R3_IN_PROGRESS",
        "R3_COMPLETE",
    ),
    "r4": StepDef(
        "r4",
        "08_R4_HANDOFF.md",
        "COLD_REVIEW_HANDOFF_COMPLETENESS_AUDIT.md",
        "R4_IN_PROGRESS",
        "R4_COMPLETE",
    ),
    "r5": StepDef(
        "r5",
        "09_R5_ADJUDICATION.md",
        "COLD_REVIEW_ADJUDICATION.md",
        "R5_IN_PROGRESS",
        "R5_COMPLETE",
    ),
    "verdict": StepDef(
        "verdict",
        "10_GATE_VERDICT.md",
        "GATE_VERDICT.md",
        "GATE_VERDICT_ISSUED",
        "GATE_PASS_FOR_HANDOFF",
    ),
    "production_caller": StepDef(
        "production_caller",
        "20_PRODUCTION_CALLER_ACTIVE_PATH_AUDIT.md",
        "PRODUCTION_CALLER_AUDIT.md",
        "PRODUCTION_CALLER_AUDIT_IN_PROGRESS",
        "PRODUCTION_CALLER_AUDIT_PASS",
    ),
    "consumer_api": StepDef(
        "consumer_api",
        "21_CONSUMER_API_PROOF_AUDIT.md",
        "CONSUMER_API_PROOF_AUDIT.md",
        "CONSUMER_API_PROOF_AUDIT_IN_PROGRESS",
        "CONSUMER_API_PROOF_AUDIT_PASS",
    ),
    "required_tests": StepDef(
        "required_tests",
        "23_REQUIRED_TEST_SET_EXACTNESS.md",
        "REQUIRED_TEST_SET_EXACTNESS.md",
        "REQUIRED_TEST_SET_EXACTNESS_IN_PROGRESS",
        "REQUIRED_TEST_SET_EXACTNESS_PASS",
    ),
    "final_auditor": StepDef(
        "final_auditor",
        "37_FINAL_PACKET_AUDITOR.md",
        "FINAL_PACKET_AUDITOR_REPORT.md",
        "FINAL_PACKET_AUDITOR",
        "PASS_HANDOFF_COMPLETE",
    ),
}

NEXT_BY_STATE = {
    "GATE_PROFILE_SELECTION_COMPLETE": "evidence_adequacy",
    "EVIDENCE_UPGRADE_REQUIRED": "test_plan",
    "EVIDENCE_ALREADY_ADEQUATE": "evidence_consistency",
    "TEST_PLAN_COMPLETE": "evidence_consistency",
    "EVIDENCE_CONSISTENCY_PASS": "enforcement",
    "ENFORCEMENT_AUDIT_PASS": "r1",
    "ENFORCEMENT_AUDIT_NOT_APPLICABLE": "r1",
    "PANEL_ENTRY_VERIFIED": "r1",
    "R1_COMPLETE": "r2",
    "R2_COMPLETE": "r3",
    "R3_COMPLETE": "r4",
    "R4_COMPLETE": "r5",
    "R5_COMPLETE": "verdict",
    "GATE_PASS_FOR_HANDOFF": "final_auditor",
}


class GateRunnerError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def package_root_from_arg(value: str | None) -> Path:
    return Path(value).expanduser().resolve() if value else DEFAULT_PACKAGE_ROOT


def report_dir(package_root: Path, task_area: str) -> Path:
    return package_root / "reports" / task_area


def state_path(package_root: Path, task_area: str) -> Path:
    return report_dir(package_root, task_area) / "CURRENT_STATE.yaml"


def read_text_or_empty(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GateRunnerError(f"Missing YAML file: {path}")
    if YAML_AVAILABLE:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise GateRunnerError(f"Expected mapping in {path}")
        return data
    # Small fallback for status-only use when PyYAML is unavailable.
    result: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if YAML_AVAILABLE:
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return
    lines = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            lines.append(f"{key}: {value!r}")
        elif value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def template_text(name: str) -> str:
    path = GATE_DIR / name
    if not path.exists():
        raise GateRunnerError(f"Missing gate template/source: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def replace_common_placeholders(text: str, *, task_id: str, task_area: str, gate_run_id: str, timestamp: str) -> str:
    replacements = {
        "[task id]": task_id,
        "[task_id]": task_id,
        "[REQUIRED]": task_id,
        "[REQUIRED: unique task ID, e.g. ORCH-FIXES-001]": task_id,
        "[REQUIRED: directory name under reports/, e.g. agentos-ng-governance-fixes]": task_area,
        "[AUTO: gate-<ISO-timestamp>]": gate_run_id,
        "[AUTO: ISO-8601]": timestamp,
        "[ISO timestamp]": timestamp,
        "[task_area]": task_area,
        "[reports/<task_area>/]": f"reports/{task_area}/",
        "reports/[task_area]/": f"reports/{task_area}/",
        "[N]": "1",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_path_token(path: str) -> str:
    return path.strip().replace("\\", "/")


def normalized_lower_paths(changed_files: list[str]) -> list[str]:
    return [normalize_path_token(path).lower().lstrip("./") for path in changed_files]


def is_gui_visible_path(path: str) -> bool:
    return bool(GUI_PATH_RE.search(path))


def prompt_describes_gui_visible_work(prompt_text: str) -> bool:
    if GUI_SCOPE_EXCLUSION_RE.search(prompt_text):
        return False
    return bool(GUI_PROMPT_RE.search(prompt_text) or GUI_ACTION_PROMPT_RE.search(prompt_text))


def is_provider_model_path(path: str) -> bool:
    return any(token in path for token in ("model", "provider", "llm", "openrouter"))


def prompt_describes_provider_model_routing(prompt_text: str) -> bool:
    if PROVIDER_SCOPE_EXCLUSION_RE.search(prompt_text):
        return False
    return bool(PROVIDER_PROMPT_RE.search(prompt_text))


def is_markdown_like(path: str) -> bool:
    return path.endswith((".md", ".markdown", ".txt", ".rst"))


def is_process_doc_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        is_markdown_like(path)
        and (
            any(path.startswith(prefix) for prefix in PROCESS_DOC_PREFIXES)
            or name in PROCESS_DOC_FILES
        )
    )


def is_runtime_prompt_path(path: str) -> bool:
    return (
        is_markdown_like(path)
        and any(path.startswith(prefix) for prefix in RUNTIME_PROMPT_PREFIXES)
        and "agent_coordination" not in path
    )


def is_gate_logic_path(path: str) -> bool:
    return (
        path.startswith("gate/")
        or path.startswith("/users/syedhaider/downloads/gate/")
        or path.startswith("scripts/gate/")
        or path.endswith((
            "gate_runner.py",
            "check_gate_package.py",
            "gate_profiles.md",
            "gate_profile_selector.md",
            "required_proof_files_by_profile.yaml",
            "state_machine.md",
            "state_schema.md",
            "transition_rules.md",
        ))
    )


def is_ci_governance_path(path: str) -> bool:
    return (
        path.startswith(".github/workflows/")
        or "branch_protection" in path
        or "pr-checks" in path
        or "merge_queue" in path
        or "autonomous_merge" in path
    )


def is_active_config_path(path: str) -> bool:
    return (
        path == ".env"
        or path.startswith(".env.")
        or path.startswith("deploy/")
        or path.startswith("infra/")
        or path.endswith((".tf", ".tfvars"))
    )


def is_env_example_only_path(path: str) -> bool:
    return path == ".env.example" or path.endswith("/.env.example")


def has_high_risk_file_trigger(changed_files: list[str]) -> bool:
    paths = normalized_lower_paths(changed_files)
    return any(
        is_gate_logic_path(path)
        or is_ci_governance_path(path)
        or (is_active_config_path(path) and not is_env_example_only_path(path))
        or is_runtime_prompt_path(path)
        for path in paths
    )


def is_focused_evidence_candidate(changed_files: list[str]) -> bool:
    paths = normalized_lower_paths(changed_files)
    return bool(paths) and all(is_process_doc_path(path) or is_env_example_only_path(path) for path in paths)


def infer_task_kind(changed_files: list[str], prompt_text: str) -> str:
    normalized = [normalize_path_token(path) for path in changed_files]
    lower_paths = normalized_lower_paths(changed_files)
    lower_prompt = prompt_text.lower()

    if is_focused_evidence_candidate(changed_files):
        return "docs_process_policy"
    if any(is_gate_logic_path(path) for path in lower_paths):
        return "gate_change"
    if GATE_PROMPT_RE.search(prompt_text) and not lower_paths:
        return "gate_change"
    if any(is_ci_governance_path(path) for path in lower_paths):
        return "gate_change"
    if any(path.endswith(".sql") or "/migration" in path or "migrations/" in path for path in lower_paths):
        return "migration"
    if any(is_runtime_prompt_path(path) for path in lower_paths):
        return "prompt_authoring"
    if RUNTIME_PROMPT_RE.search(prompt_text):
        return "runtime_state"
    if MERGE_PROMPT_RE.search(prompt_text):
        return "merge_verification"
    if PROD_PROMPT_RE.search(prompt_text):
        return "production_wiring"
    if prompt_describes_provider_model_routing(prompt_text) or any(is_provider_model_path(path) for path in lower_paths):
        return "provider_model_routing"
    if prompt_describes_gui_visible_work(prompt_text) or any(is_gui_visible_path(path) for path in lower_paths):
        return "gui_visible_workflow"
    if lower_paths and all(path.startswith("tests/") or path.endswith((".test.js", "_test.py", ".spec.js")) for path in lower_paths):
        return "tiny_test"
    if normalized and all(is_markdown_like(path) for path in lower_paths):
        return "docs"
    return "normal_impl"


def infer_risk_tier(task_kind: str, changed_files: list[str], prompt_text: str) -> str:
    if task_kind == "no_change":
        return "D0"
    if task_kind in {"provider_model_routing", "gui_visible_workflow"}:
        return "D4"
    if task_kind in {
        "gate_change",
        "migration",
        "runtime_state",
        "merge_verification",
        "release_verification",
        "production_wiring",
        "evidence_package",
        "prompt_authoring",
    }:
        return "D3"
    if task_kind in {"docs", "docs_process_policy", "tiny_test"}:
        return "D1" if task_kind == "tiny_test" else "D0"
    if any(is_hot_file(path) for path in changed_files):
        return "D2_HOT"
    return "D2"


def is_hot_file(path: str) -> bool:
    token = normalize_path_token(path).lower()
    hot_names = {
        "runtime_lane_registry.js",
        "scribbli_model_policy.js",
        "fallback_state_manager.js",
        "llm_proxy.js",
        "scribbli_llm.js",
        "00_start.md",
        "state_machine.md",
        "transition_rules.md",
        "state_schema.md",
        "gate_profiles.md",
        "gate_profile_selector.md",
    }
    name = token.rsplit("/", 1)[-1]
    return (
        name in hot_names
        or "/.github/workflows/" in token
        or "migrations/index.js" in token
        or token.endswith("/.env")
        or token == ".env"
    )


def required_profile(risk_tier: str, task_kind: str) -> str:
    if task_kind in {"docs", "docs_process_policy", "tiny_test"} and risk_tier in {"D0", "D1"}:
        return "GATE_LITE"
    if risk_tier == "D2" and task_kind == "normal_impl":
        return "GATE_STANDARD"
    if task_kind in {"provider_model_routing", "gui_visible_workflow"}:
        return "GATE_FULL_PLUS_DOMAIN_ADDENDUM"
    return "GATE_FULL"


def strongest_profile(left: str, right: str) -> str:
    return left if PROFILE_ORDER[left] >= PROFILE_ORDER[right] else right


def infer_domain_addenda(task_kind: str, prompt_text: str, explicit: list[str]) -> list[str]:
    addenda = list(dict.fromkeys(explicit))
    if task_kind == "provider_model_routing" and "model_id_validation" not in addenda:
        addenda.append("model_id_validation")
    if task_kind == "gui_visible_workflow" and "real_user_gui_journey" not in addenda:
        addenda.append("real_user_gui_journey")
    return addenda


def evidence_requirements_for_mode(validation_mode: str, selected_profile: str | None, task_kind: str) -> list[str]:
    if validation_mode == "NO_CHANGE":
        return ["clean_git_status_or_noop_note"]
    if validation_mode == "FOCUSED_EVIDENCE":
        if task_kind == "tiny_test":
            return ["targeted_tests", "syntax_or_static_check", "pr_ci"]
        if task_kind == "normal_impl":
            return ["targeted_tests", "relevant_integration_tests", "syntax_or_static_check", "repo_boundary_guard", "pr_ci"]
        return [
            "repo_boundary_guard_changed_files_or_repo_policy",
            "docsync_or_docs_truth_check_if_applicable",
            "markdown_link_path_check_if_available",
            "pr_ci",
        ]
    if selected_profile == "GATE_LITE":
        return ["targeted_tests", "syntax_or_static_check", "pr_ci"]
    if selected_profile == "GATE_STANDARD":
        return ["targeted_tests", "relevant_integration_tests", "repo_boundary_guard", "pr_ci"]
    if selected_profile == "GATE_FULL_PLUS_DOMAIN_ADDENDUM":
        requirements = ["full_relevant_suite", "domain_addendum_evidence", "repo_boundary_guard", "pr_ci"]
        if task_kind == "gui_visible_workflow":
            requirements.append("real_user_gui_journey")
        if task_kind == "provider_model_routing":
            requirements.append("model_id_validation")
        return requirements
    return ["full_relevant_suite", "repo_boundary_guard", "pr_ci"]


def decide_validation_mode(
    *,
    changed_files: list[str],
    prompt_text: str,
    task_kind: str,
    risk_tier: str,
    selected_profile: str | None,
    domain_addenda: list[str],
    no_change: bool = False,
) -> dict[str, Any]:
    paths = normalized_lower_paths(changed_files)
    escalation_triggers = {
        "gate_logic": any(is_gate_logic_path(path) for path in paths),
        "ci_branch_governance": any(is_ci_governance_path(path) for path in paths),
        "active_runtime_config": any(is_active_config_path(path) and not is_env_example_only_path(path) for path in paths),
        "runtime_prompt_template": any(is_runtime_prompt_path(path) for path in paths),
        "gui_visible": task_kind == "gui_visible_workflow" or any(is_gui_visible_path(path) for path in paths),
        "provider_model_routing": task_kind == "provider_model_routing",
        "runtime_state_or_production": task_kind in {"runtime_state", "production_wiring", "migration", "release_verification"},
        "security_auth_secrets_payment": any(
            token in path for path in paths for token in ("auth", "secret", "payment", "billing", "security")
        ),
    }

    if no_change:
        validation_mode = "NO_CHANGE"
        terminal_state = "NO_CHANGE_COMPLETE"
        formal_gate_required = False
        runtime_tests_required: bool | str = False
        profile = None
        rationale = "No committed diff/no-op declared."
        skip_rationale = "No committed diff; formal Gate and runtime tests are not applicable."
    elif is_focused_evidence_candidate(changed_files) and not any(escalation_triggers.values()):
        validation_mode = "FOCUSED_EVIDENCE"
        terminal_state = "FOCUSED_EVIDENCE_COMPLETE"
        formal_gate_required = False
        runtime_tests_required = False
        profile = None
        rationale = "Docs/process/policy/prompt-text-only change with no escalation trigger."
        skip_rationale = (
            "Docs/process-only change. No runtime code, schema, active production config, "
            "CI/branch governance, Gate logic, provider routing, GUI-visible behavior, "
            "auth/secrets/payment, or production wiring touched."
        )
    elif task_kind == "tiny_test" and risk_tier in {"D0", "D1"} and not any(escalation_triggers.values()):
        validation_mode = "FOCUSED_EVIDENCE"
        terminal_state = "FOCUSED_EVIDENCE_COMPLETE"
        formal_gate_required = False
        runtime_tests_required = "targeted_only"
        profile = None
        rationale = "Low-risk test-only change with no escalation trigger; focused evidence plus PR CI are sufficient."
        skip_rationale = (
            "Formal LLM proof-package is not required for low-risk test-only changes when changed files do not "
            "touch Gate logic, CI/branch governance, active runtime config, runtime prompt templates, "
            "GUI-visible application behavior, provider/model routing, runtime state/production wiring, "
            "or auth/secrets/payment."
        )
    elif (
        task_kind == "normal_impl"
        and risk_tier == "D2"
        and selected_profile == "GATE_STANDARD"
        and not domain_addenda
        and not any(escalation_triggers.values())
    ):
        validation_mode = "FOCUSED_EVIDENCE"
        terminal_state = "FOCUSED_EVIDENCE_COMPLETE"
        formal_gate_required = False
        runtime_tests_required = "targeted_plus_relevant_integration"
        profile = None
        rationale = (
            "Bounded D2 normal implementation with no escalation trigger; focused runtime "
            "and integration evidence plus PR CI are sufficient."
        )
        skip_rationale = (
            "Formal LLM proof-package is not required for bounded D2 normal implementation "
            "when changed files do not touch Gate logic, CI/branch governance, active runtime "
            "config, runtime prompt templates, GUI-visible behavior, provider/model routing, "
            "runtime state/production wiring, or auth/secrets/payment."
        )
    else:
        validation_mode = "FORMAL_GATE"
        terminal_state = "GATE_PROFILE_SELECTION_COMPLETE"
        formal_gate_required = True
        if selected_profile == "GATE_LITE":
            runtime_tests_required = "targeted_only"
        elif selected_profile == "GATE_STANDARD":
            runtime_tests_required = "targeted_plus_relevant_integration"
        elif selected_profile == "GATE_FULL_PLUS_DOMAIN_ADDENDUM":
            runtime_tests_required = "full_suite_plus_domain_evidence"
        else:
            runtime_tests_required = "full_relevant_suite"
        profile = selected_profile
        rationale = f"{task_kind} classified as {risk_tier}; formal Gate profile {selected_profile} required."
        skip_rationale = None

    return {
        "validation_mode": validation_mode,
        "formal_gate_required": formal_gate_required,
        "runtime_tests_required": runtime_tests_required,
        "selected_profile": profile,
        "risk_tier": risk_tier,
        "task_kind": task_kind,
        "changed_files": changed_files,
        "required_evidence": evidence_requirements_for_mode(validation_mode, profile, task_kind),
        "skip_formal_gate_rationale": skip_rationale,
        "escalation_triggers_checked": escalation_triggers,
        "domain_addenda": domain_addenda,
        "human_decision_required": False,
        "terminal_state": terminal_state,
        "rationale": rationale,
    }


def write_validation_decision(out_dir: Path, decision: dict[str, Any]) -> None:
    dump_yaml(out_dir / "VALIDATION_DECISION.yaml", decision)


def state_template(task_id: str, task_area: str, gate_run_id: str, timestamp: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "task_area": task_area,
        "gate_run_id": gate_run_id,
        "gate_started_at": timestamp,
        "last_updated_at": timestamp,
        "current_state": "GATE_NOT_STARTED",
        "gate_completed": False,
        "gate_profile": None,
        "risk_tier": None,
        "task_kind": None,
        "domain_addenda": [],
        "validation_mode": None,
        "formal_gate_required": None,
        "runtime_tests_required": None,
        "validation_decision_path": f"reports/{task_area}/VALIDATION_DECISION.yaml",
        "profile_override_required": None,
        "profile_selection_rationale": None,
        "cycle_count": 0,
        "max_cycles": 5,
        "claims_ledger_path": f"reports/{task_area}/CLAIMS_LEDGER.yaml",
        "evidence_ledger_path": f"reports/{task_area}/EVIDENCE_LEDGER.yaml",
        "package_manifest_path": f"reports/{task_area}/PACKAGE_MANIFEST.md",
        "stale_file_register_path": f"reports/{task_area}/STALE_FILE_REGISTER.yaml",
        "cycle_tracker_path": f"reports/{task_area}/CYCLE_TRACKER.md",
        "state_history": [{"state": "GATE_NOT_STARTED", "entered_at": timestamp, "exited_at": None}],
        "cycles": {
            1: {
                "started_at": None,
                "completed_at": None,
                "evidence_adequacy_decision": None,
                "consistency_result": None,
                "consistency_contradictions_found": None,
                "enforcement_audit_applicable": None,
                "enforcement_audit_result": None,
                "r1_blocking": None,
                "r1_nonblocking": None,
                "r2_blocking": None,
                "r2_nonblocking": None,
                "r3_blocking": None,
                "r3_nonblocking": None,
                "r4_blocking": None,
                "r4_nonblocking": None,
                "r5_verdict": None,
                "gate_verdict": None,
                "blockers_autofix": None,
                "blockers_human_blocked": None,
                "fixes_applied": None,
                "execution_context_audit_applicable": None,
                "execution_context_audit_result": None,
                "final_outcome_label": None,
            }
        },
        "final_package_audit_result": None,
        "canonical_handoff_audit_result": None,
        "execution_context_audit_result": None,
        "final_packet_auditor_verdict": None,
        "rerun_from": None,
        "final_gate_verdict": None,
        "final_r5_verdict": None,
        "handoff_type": None,
        "handoff_completed_at": None,
        "remaining_human_blocked_blockers": None,
    }


def transition_state(data: dict[str, Any], new_state: str, **fields: Any) -> dict[str, Any]:
    timestamp = now_iso()
    history = data.setdefault("state_history", [])
    if history and history[-1].get("exited_at") is None:
        history[-1]["exited_at"] = timestamp
    history.append({"state": new_state, "entered_at": timestamp, "exited_at": None})
    data["current_state"] = new_state
    data["last_updated_at"] = timestamp
    data.update(fields)
    if new_state in {
        "PASS_HANDOFF_COMPLETE",
        "BLOCKED_HANDOFF_COMPLETE",
        "GATE_LITE_PASS_HANDOFF_COMPLETE",
        "GATE_STANDARD_PASS_HANDOFF_COMPLETE",
        "GATE_FULL_PASS_HANDOFF_COMPLETE",
        "GATE_PROFILE_SELECTION_BLOCKED",
        "FOCUSED_EVIDENCE_COMPLETE",
        "FORMAL_GATE_NOT_REQUIRED_COMPLETE",
        "NO_CHANGE_COMPLETE",
    }:
        data["gate_completed"] = True
    return data


def write_initial_artifacts(out_dir: Path, *, task_id: str, task_area: str, gate_run_id: str, timestamp: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "CYCLE_TRACKER.md": "CYCLE_TRACKER_TEMPLATE.md",
        "CLAIMS_LEDGER.yaml": "CLAIMS_LEDGER_TEMPLATE.yaml",
        "EVIDENCE_LEDGER.yaml": "EVIDENCE_LEDGER_TEMPLATE.yaml",
        "STALE_FILE_REGISTER.yaml": "STALE_FILE_REGISTER_TEMPLATE.yaml",
        "PACKAGE_MANIFEST.md": "PACKAGE_MANIFEST_TEMPLATE.md",
    }
    for dest_name, template_name in artifacts.items():
        dest = out_dir / dest_name
        if dest.exists():
            continue
        text = replace_common_placeholders(
            template_text(template_name),
            task_id=task_id,
            task_area=task_area,
            gate_run_id=gate_run_id,
            timestamp=timestamp,
        )
        dest.write_text(text, encoding="utf-8")


def write_profile_selection(
    out_dir: Path,
    *,
    task_id: str,
    task_area: str,
    gate_run_id: str,
    changed_files: list[str],
    prompt_text: str,
    operator_profile: str | None,
    risk_tier: str,
    task_kind: str,
    selected_profile: str,
    required: str,
    domain_addenda: list[str],
) -> str:
    timestamp = now_iso()
    override_required = bool(operator_profile and PROFILE_ORDER[operator_profile] < PROFILE_ORDER[required])
    missing_addenda = [name for name in domain_addenda if not (GATE_DIR / "domain_addenda" / f"{name}.md").exists()]
    human_decision = bool(missing_addenda)
    rationale = f"{task_kind} classified as {risk_tier}; selected {selected_profile}."

    changed_lines = "\n".join(f"- {path}" for path in changed_files) if changed_files else "- none provided"
    addenda_lines = "\n".join(
        f"- {name} - file: `gate/domain_addenda/{name}.md` - EXISTS: {'YES' if name not in missing_addenda else 'NO'}"
        for name in domain_addenda
    ) or "- none applicable"
    missing_lines = "\n".join(f"- gate/domain_addenda/{name}.md - MISSING" for name in missing_addenda) or "- none"

    text = f"""# Gate Profile Selection

**Task ID:** {task_id}
**Task area:** {task_area}
**Gate run ID:** {gate_run_id}
**Selection completed at:** {timestamp}

---

## Risk Tier Assessment

**Files in task file-touch map:**
{changed_lines}

**Determined risk tier:** {risk_tier}

**Risk tier rationale:** {rationale}

---

## Profile Selection

**Operator-specified profile (from task prompt):** {operator_profile or "not specified"}

**Default profile for this risk tier:** {required}

**Selected profile:** {selected_profile}

**Profile override required:** {"YES" if override_required else "NO"}

---

## Domain Addenda

**Addenda applicable to this task:**
{addenda_lines}

**Addendum files missing (blocking):**
{missing_lines}

---

## Human Decision Assessment

**Human decision required:** {"YES" if human_decision else "NO"}

---

## YAML Selector Output

```yaml
gate_profile: {selected_profile}
selected_profile: {selected_profile}
risk_tier: {risk_tier}
task_kind: {task_kind}
profile_selection_rationale: "{rationale}"
domain_addenda: {domain_addenda}
profile_override_required: {str(override_required).lower()}
human_decision_required: {str(human_decision).lower()}
```

## Next step

Route to `01_EVIDENCE_ADEQUACY.md`.
"""
    (out_dir / "GATE_PROFILE_SELECTION.md").write_text(text, encoding="utf-8")
    return rationale


def command_init(args: argparse.Namespace) -> int:
    package_root = package_root_from_arg(args.package_root)
    out_dir = report_dir(package_root, args.task_area)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        raise GateRunnerError(f"Report directory already exists: {out_dir}. Use --force to reuse it.")

    prompt_text = args.task_prompt or ""
    if args.task_prompt_file:
        prompt_text += "\n" + read_text_or_empty(Path(args.task_prompt_file).expanduser())

    changed_files = args.changed_file or []
    task_kind = "no_change" if args.no_change else (args.task_kind or infer_task_kind(changed_files, prompt_text))
    if task_kind not in TASK_KINDS:
        raise GateRunnerError(f"Unknown task kind: {task_kind}")
    risk_tier = args.risk_tier or infer_risk_tier(task_kind, changed_files, prompt_text)
    risk_tier = "D2_HOT" if risk_tier == "D2-hot" else risk_tier
    if risk_tier not in RISK_TIERS:
        raise GateRunnerError(f"Unknown risk tier: {risk_tier}")
    required = required_profile(risk_tier, task_kind)
    operator_profile = args.profile
    if operator_profile and operator_profile not in PROFILE_ORDER:
        raise GateRunnerError(f"Unknown profile: {operator_profile}")
    selected_profile = strongest_profile(operator_profile, required) if operator_profile else required
    domain_addenda = infer_domain_addenda(task_kind, prompt_text, args.domain_addendum or [])
    if selected_profile == "GATE_FULL_PLUS_DOMAIN_ADDENDUM" and not domain_addenda:
        domain_addenda = ["operator_required_addendum_missing"]
    decision = decide_validation_mode(
        changed_files=changed_files,
        prompt_text=prompt_text,
        task_kind=task_kind,
        risk_tier=risk_tier,
        selected_profile=selected_profile,
        domain_addenda=domain_addenda,
        no_change=args.no_change,
    )

    timestamp = now_iso()
    gate_run_id = args.gate_run_id or f"gate-{timestamp}"
    write_initial_artifacts(out_dir, task_id=args.task_id, task_area=args.task_area, gate_run_id=gate_run_id, timestamp=timestamp)
    write_validation_decision(out_dir, decision)

    state = state_template(args.task_id, args.task_area, gate_run_id, timestamp)
    transition_state(state, "CYCLE_TRACKER_INITIALIZED", cycle_count=1)
    state["cycles"][1]["started_at"] = now_iso()
    if not decision["formal_gate_required"]:
        transition_state(
            state,
            str(decision["terminal_state"]),
            gate_profile=None,
            risk_tier=risk_tier,
            task_kind=task_kind,
            domain_addenda=[],
            validation_mode=decision["validation_mode"],
            formal_gate_required=False,
            runtime_tests_required=decision["runtime_tests_required"],
            profile_override_required=False,
            profile_selection_rationale=decision["rationale"],
            final_gate_verdict=decision["terminal_state"],
            handoff_type=decision["validation_mode"],
            handoff_completed_at=now_iso(),
        )
        dump_yaml(state_path(package_root, args.task_area), state)
        print(f"Initialized validation-router run: {out_dir}")
        print(
            f"validation_mode={decision['validation_mode']} formal_gate_required=false "
            f"runtime_tests_required={decision['runtime_tests_required']}"
        )
        print(f"current_state={decision['terminal_state']}")
        return 0

    transition_state(state, "GATE_PROFILE_SELECTION_IN_PROGRESS")
    rationale = write_profile_selection(
        out_dir,
        task_id=args.task_id,
        task_area=args.task_area,
        gate_run_id=gate_run_id,
        changed_files=changed_files,
        prompt_text=prompt_text,
        operator_profile=operator_profile,
        risk_tier=risk_tier,
        task_kind=task_kind,
        selected_profile=selected_profile,
        required=required,
        domain_addenda=domain_addenda,
    )
    missing_addenda = [name for name in domain_addenda if not (GATE_DIR / "domain_addenda" / f"{name}.md").exists()]
    final_profile_state = "GATE_PROFILE_SELECTION_BLOCKED" if missing_addenda else "GATE_PROFILE_SELECTION_COMPLETE"
    decision["human_decision_required"] = bool(missing_addenda)
    decision["terminal_state"] = final_profile_state
    write_validation_decision(out_dir, decision)
    transition_state(
        state,
        final_profile_state,
        gate_profile=selected_profile,
        risk_tier=risk_tier,
        task_kind=task_kind,
        domain_addenda=domain_addenda,
        validation_mode="FORMAL_GATE",
        formal_gate_required=True,
        runtime_tests_required=decision["runtime_tests_required"],
        profile_override_required=bool(operator_profile and PROFILE_ORDER[operator_profile] < PROFILE_ORDER[required]),
        profile_selection_rationale=rationale,
    )
    dump_yaml(state_path(package_root, args.task_area), state)
    print(f"Initialized gate run: {out_dir}")
    print(f"profile={selected_profile} risk_tier={risk_tier} task_kind={task_kind} domain_addenda={domain_addenda}")
    print(f"current_state={final_profile_state}")
    return 0 if final_profile_state == "GATE_PROFILE_SELECTION_COMPLETE" else 2


def load_state_for_task(package_root: Path, task_area: str) -> dict[str, Any]:
    return load_yaml(state_path(package_root, task_area))


def command_status(args: argparse.Namespace) -> int:
    package_root = package_root_from_arg(args.package_root)
    state = load_state_for_task(package_root, args.task_area)
    print(f"task_area={state.get('task_area')}")
    print(f"current_state={state.get('current_state')}")
    print(f"gate_profile={state.get('gate_profile')}")
    print(f"risk_tier={state.get('risk_tier')}")
    print(f"task_kind={state.get('task_kind')}")
    print(f"domain_addenda={state.get('domain_addenda')}")
    print(f"gate_completed={state.get('gate_completed')}")
    return 0


def choose_next_step(state: dict[str, Any]) -> str | None:
    current = str(state.get("current_state") or "")
    return NEXT_BY_STATE.get(current)


def command_next(args: argparse.Namespace) -> int:
    package_root = package_root_from_arg(args.package_root)
    state = load_state_for_task(package_root, args.task_area)
    alias = choose_next_step(state)
    if not alias:
        print(f"No scripted next step for current_state={state.get('current_state')}")
        return 1
    step = STEP_DEFS[alias]
    print(f"next_step={alias}")
    print(f"step_doc={step.doc}")
    print(f"expected_output=reports/{args.task_area}/{step.output}")
    print(f"render_command=python3 scripts/gate_runner.py render-prompt --task-area {args.task_area} --step {alias}")
    return 0


def render_prompt(package_root: Path, task_area: str, step: StepDef) -> str:
    out_dir = report_dir(package_root, task_area)
    state = load_state_for_task(package_root, task_area)
    source_doc = template_text(step.doc)
    existing_files = sorted(path.name for path in out_dir.iterdir() if path.is_file()) if out_dir.exists() else []
    existing_files_text = "\n".join(f"- {name}" for name in existing_files) or "- none"
    output_path = out_dir / step.output

    return f"""You are running one bounded state in the Gate review state machine.

Gate root: {GATE_DIR}
Package root: {package_root}
Task area: {task_area}
Current state: {state.get("current_state")}
Gate profile: {state.get("gate_profile")}
Risk tier: {state.get("risk_tier")}
Task kind: {state.get("task_kind")}
Domain addenda: {state.get("domain_addenda")}

Existing report files:
{existing_files_text}

State source document: {step.doc}
Expected output file: {output_path}

Output contract:
- Return only the complete content for `{step.output}`.
- Do not include chat narration before or after the artifact.
- Base findings on files under `reports/{task_area}/` and the source document below.
- If evidence is insufficient, say so explicitly and mark the relevant blocker.
- Do not invent raw outputs, commands, screenshots, traces, or exit codes.

--- SOURCE DOCUMENT START ---
{source_doc}
--- SOURCE DOCUMENT END ---
"""


def command_render_prompt(args: argparse.Namespace) -> int:
    package_root = package_root_from_arg(args.package_root)
    alias = args.step or choose_next_step(load_state_for_task(package_root, args.task_area))
    if not alias or alias not in STEP_DEFS:
        raise GateRunnerError(f"Unknown or unavailable step: {alias}")
    prompt = render_prompt(package_root, args.task_area, STEP_DEFS[alias])
    if args.output:
        Path(args.output).expanduser().write_text(prompt, encoding="utf-8")
    else:
        print(prompt)
    return 0


def infer_completion_state(step: StepDef, output_text: str, override: str | None) -> str | None:
    if override:
        return override
    for marker, state in step.decision_markers:
        if marker in output_text:
            return state
    return step.default_complete


def command_run_step(args: argparse.Namespace) -> int:
    package_root = package_root_from_arg(args.package_root)
    alias = args.step or choose_next_step(load_state_for_task(package_root, args.task_area))
    if not alias or alias not in STEP_DEFS:
        raise GateRunnerError(f"Unknown or unavailable step: {alias}")
    step = STEP_DEFS[alias]
    prompt = render_prompt(package_root, args.task_area, step)
    out_dir = report_dir(package_root, args.task_area)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.prompt_out:
        Path(args.prompt_out).expanduser().write_text(prompt, encoding="utf-8")

    if args.dry_run or not args.llm_cmd:
        print(prompt)
        return 0

    state = load_state_for_task(package_root, args.task_area)
    if step.in_progress and not args.no_advance:
        transition_state(state, step.in_progress)
        dump_yaml(state_path(package_root, args.task_area), state)

    cmd = shlex.split(args.llm_cmd)
    if not cmd:
        raise GateRunnerError("--llm-cmd was empty after parsing")
    proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True, cwd=str(GATE_DIR))

    raw_dir = out_dir / "llm_outputs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{alias}_{now_iso().replace(':', '-')}.raw.md"
    raw_path.write_text(
        f"COMMAND: {args.llm_cmd}\nEXIT_CODE:{proc.returncode}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode != 0:
        print(f"LLM command failed; raw output: {raw_path}", file=sys.stderr)
        return proc.returncode

    output_text = proc.stdout.strip() + "\n"
    output_path = out_dir / (args.output_name or step.output)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Raw LLM output: {raw_path}")

    if not args.no_advance:
        state = load_state_for_task(package_root, args.task_area)
        completion = infer_completion_state(step, output_text, args.advance_to)
        if completion:
            transition_state(state, completion)
            dump_yaml(state_path(package_root, args.task_area), state)
            print(f"advanced_to={completion}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    package_root = package_root_from_arg(args.package_root)
    state = load_state_for_task(package_root, args.task_area)
    if state.get("formal_gate_required") is False:
        decision_path = report_dir(package_root, args.task_area) / "VALIDATION_DECISION.yaml"
        if not decision_path.exists():
            print(f"Missing validation decision: {decision_path}", file=sys.stderr)
            return 2
        decision = load_yaml(decision_path)
        mode = decision.get("validation_mode")
        terminal = state.get("current_state")
        allowed_terminals = {"FOCUSED_EVIDENCE_COMPLETE", "FORMAL_GATE_NOT_REQUIRED_COMPLETE", "NO_CHANGE_COMPLETE"}
        if mode not in {"FOCUSED_EVIDENCE", "NO_CHANGE"} or terminal not in allowed_terminals:
            print(f"Invalid non-formal validation decision: mode={mode} terminal={terminal}", file=sys.stderr)
            return 2
        out = report_dir(package_root, args.task_area) / "GATE_PACKAGE_VALIDATION_REPORT.md"
        out.write_text(
            "# Gate Validation Router Report\n\n"
            "EXIT_CODE:0\n\n"
            f"validation_mode: {mode}\n"
            "formal_gate_required: false\n"
            f"terminal_state: {terminal}\n"
            f"decision: {decision_path}\n",
            encoding="utf-8",
        )
        print(f"validation_mode={mode}")
        print("formal_gate_required=false")
        print(f"terminal_state={terminal}")
        print(f"validation_report={out}")
        return 0

    cmd = [
        sys.executable,
        str(GATE_DIR / "tools" / "check_gate_package.py"),
        "--package",
        str(package_root),
        "--task-area",
        args.task_area,
        "--gate-dir",
        str(GATE_DIR),
    ]
    if state.get("gate_profile"):
        cmd += ["--profile", str(state["gate_profile"])]
    if state.get("risk_tier"):
        cmd += ["--risk-tier", str(state["risk_tier"])]
    if state.get("task_kind"):
        cmd += ["--task-kind", str(state["task_kind"])]
    if args.final:
        cmd.append("--final")

    proc = subprocess.run(cmd, text=True, capture_output=True)
    out = report_dir(package_root, args.task_area) / "GATE_PACKAGE_VALIDATION_REPORT.md"
    out.write_text(
        "# Gate Package Validation Report\n\n"
        f"Command: `{' '.join(shlex.quote(part) for part in cmd)}`\n\n"
        f"EXIT_CODE:{proc.returncode}\n\n"
        "## STDOUT\n\n"
        "```text\n"
        f"{proc.stdout}\n"
        "```\n\n"
        "## STDERR\n\n"
        "```text\n"
        f"{proc.stderr}\n"
        "```\n",
        encoding="utf-8",
    )
    print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    print(f"validation_report={out}")
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and validate Gate state-machine packages.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a gate run and select the profile.")
    init.add_argument("--package-root", help="Package root containing reports/. Defaults to the gate directory.")
    init.add_argument("--task-area", required=True)
    init.add_argument("--task-id", required=True)
    init.add_argument("--task-prompt", default="")
    init.add_argument("--task-prompt-file")
    init.add_argument("--changed-file", action="append", default=[])
    init.add_argument("--task-kind", choices=sorted(TASK_KINDS))
    init.add_argument("--risk-tier", choices=sorted(RISK_TIERS | {"D2-hot"}))
    init.add_argument("--profile", choices=sorted(PROFILE_ORDER))
    init.add_argument("--domain-addendum", action="append", default=[])
    init.add_argument("--gate-run-id")
    init.add_argument("--no-change", action="store_true", help="Declare this run has no committed diff/no-op.")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=command_init)

    status = sub.add_parser("status", help="Print current gate state.")
    status.add_argument("--package-root")
    status.add_argument("--task-area", required=True)
    status.set_defaults(func=command_status)

    next_cmd = sub.add_parser("next", help="Print the next scripted step.")
    next_cmd.add_argument("--package-root")
    next_cmd.add_argument("--task-area", required=True)
    next_cmd.set_defaults(func=command_next)

    render = sub.add_parser("render-prompt", help="Render a compact prompt for one gate step.")
    render.add_argument("--package-root")
    render.add_argument("--task-area", required=True)
    render.add_argument("--step", choices=sorted(STEP_DEFS))
    render.add_argument("--output")
    render.set_defaults(func=command_render_prompt)

    run = sub.add_parser("run-step", help="Render a step prompt, optionally call an LLM command, and write the output artifact.")
    run.add_argument("--package-root")
    run.add_argument("--task-area", required=True)
    run.add_argument("--step", choices=sorted(STEP_DEFS))
    run.add_argument("--llm-cmd", help='Command that reads prompt on stdin, e.g. "claude -p" or "codex exec".')
    run.add_argument("--prompt-out")
    run.add_argument("--output-name")
    run.add_argument("--advance-to")
    run.add_argument("--no-advance", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(func=command_run_step)

    validate = sub.add_parser("validate", help="Run tools/check_gate_package.py and save its output.")
    validate.add_argument("--package-root")
    validate.add_argument("--task-area", required=True)
    validate.add_argument("--final", action="store_true")
    validate.set_defaults(func=command_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except GateRunnerError as exc:
        print(f"gate_runner: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
