#!/usr/bin/env python3
"""
check_gate_package.py — Gate 5.4 executable package checker.

Validates a gate package directory or zip against required proof files,
profile-selection rules, raw-output rules, warning audits, final git status,
package integrity, and (Gate 5.4) the final packet auditor report.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


FULL_PROFILES = {"GATE_FULL", "GATE_FULL_PLUS_DOMAIN_ADDENDUM"}
STANDARD_AND_UP = {"GATE_STANDARD", *FULL_PROFILES}
PROFILE_ORDER = {
    "GATE_LITE": 1,
    "GATE_STANDARD": 2,
    "GATE_FULL": 3,
    "GATE_FULL_PLUS_DOMAIN_ADDENDUM": 4,
}
RISK_TIERS = {"D0", "D1", "D2", "D2_HOT", "D3", "D4"}
TASK_KINDS = {
    "docs",
    "tiny_test",
    "normal_impl",
    "hot_file",
    "migration",
    "runtime_state",
    "merge_verification",
    "release_verification",
    "production_wiring",
    "provider_model_routing",
    "gate_change",
    "prompt_authoring",
    "evidence_package",
}
SUMMARY_DOC_PATTERNS = [
    "HANDOFF*.md",
    "*SUMMARY*.md",
    "*RTM*.md",
    "*REQUIREMENTS_TRACEABILITY_MATRIX*.md",
    "PACKAGE_MANIFEST.md",
]
BLOCKING_CONTRACT_TOKENS = [
    "STALE_CONTRACT_CLAIM",
    "STALE_MILESTONE_LABEL",
    "STALE_FIELD_NAME",
    "STALE_ARTIFACT_NAME",
    "CONTRADICTS_SOURCE",
    "CONTRADICTS_TESTS",
    "BLOCKING",
    "FAIL",
]
BLOCKING_WARNING_TOKENS = [
    "POST_PASS_UNCAUGHT_ERROR",
    "CONTRADICTS_SUCCESS_CLAIM",
    "EXIT_CODE_BLANK",
    "EXIT_CODE_MISSING",
    "EXIT_CODE_NONZERO",
    "EXIT_CODE_NON_NUMERIC",
    "EXIT_CODE_CONFLICTING",
    "EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW",
    "RAW_OUTPUT_DECLARED_MISSING",
    "HOST_PATH_NOT_PACKAGE_EVIDENCE",
    "REQUIRED_TEST_MISSING_FROM_RUN",
    "REQUIRED_TEST_EXCLUDED_BY_PATTERN",
    "REQUIRED_TEST_SET_UNCLEAR",
    "CHECKPOINT_READBACK_WARNING_BLOCKING",
    "BLOCKING",
]


@dataclass
class CheckResult:
    check_name: str
    passed: bool
    message: str
    flag: str | None = None


@dataclass
class RawOutputRef:
    key: str
    declared: str
    path: Path | None
    source: str
    # Gate 5.2-R1: host-path leakage tracking
    host_path_leak: bool = False  # declared path is absolute and resolves outside the package
    has_package_relative_copy: bool = False  # paired with package_relative_path that exists in-package


def load_yaml_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    content = path.read_text(encoding="utf-8")
    if YAML_AVAILABLE:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML parse error in {path}: {exc}")
    return {"_raw": content, "_path": str(path)}


def load_package(package_arg: str):
    package = Path(package_arg)
    if not package.exists():
        print(f"ERROR: Package path does not exist: {package_arg}", file=sys.stderr)
        sys.exit(2)

    if package.is_file() and package.suffix.lower() == ".zip":
        tmp_dir = Path(tempfile.mkdtemp(prefix="gate_check_"))
        try:
            with zipfile.ZipFile(package, "r") as zf:
                zf.extractall(tmp_dir)
        except zipfile.BadZipFile as exc:
            print(f"ERROR: Cannot extract zip: {exc}", file=sys.stderr)
            sys.exit(2)
        children = [path for path in tmp_dir.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            return children[0], lambda: shutil.rmtree(tmp_dir, ignore_errors=True)
        return tmp_dir, lambda: shutil.rmtree(tmp_dir, ignore_errors=True)

    if package.is_dir():
        return package, lambda: None

    print(f"ERROR: Package must be a .zip file or directory: {package_arg}", file=sys.stderr)
    sys.exit(2)


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip()


_SUPPORTED_STRUCTURED_FENCE_LANGS = {"yaml", "yml", "json"}
_DOMAIN_ADDENDUM_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_ZERO_WIDTH_TRANSLATION = str.maketrans({
    "\ufeff": "",
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\u2060": "",
    "\xa0": " ",
})
_RECOGNIZED_NA_REASON_FRAGMENTS = (
    "docs-only",
    "documentation-only",
    "audit-only",
    "no migration",
    "no consumer api",
    "no production caller",
    "no raw test output",
    "no raw output",
    "no warning output",
    "no implementer prompts",
    "no new symbols",
    "no helper exports",
    "no concurrency",
    "no downstream consumer",
)


def iter_markdown_fenced_blocks(content: str):
    fence_marker = None
    fence_lang = ""
    body_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if fence_marker is None:
            match = re.match(r"^(```|~~~)\s*([A-Za-z0-9_-]*)\s*$", stripped)
            if match:
                fence_marker = match.group(1)
                fence_lang = match.group(2).lower()
                body_lines = []
            continue
        if stripped == fence_marker:
            yield fence_lang, "\n".join(body_lines)
            fence_marker = None
            fence_lang = ""
            body_lines = []
            continue
        body_lines.append(line)


def strip_markdown_fenced_blocks(content: str) -> str:
    lines = []
    in_fence = False
    current_fence = None
    for line in content.splitlines():
        stripped = line.strip()
        match = re.match(r"^(```|~~~)\s*([A-Za-z0-9_-]*)\s*$", stripped)
        if not in_fence and match:
            in_fence = True
            current_fence = match.group(1)
            continue
        if in_fence and stripped == current_fence:
            in_fence = False
            current_fence = None
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def _parse_structured_block(lang: str, body: str):
    if lang not in _SUPPORTED_STRUCTURED_FENCE_LANGS:
        return None, None
    try:
        if lang in {"yaml", "yml"}:
            if not YAML_AVAILABLE:
                return None, "PyYAML unavailable"
            parsed = yaml.safe_load(body)
        else:
            parsed = json.loads(body)
    except Exception as exc:
        return None, str(exc)
    if not isinstance(parsed, dict):
        return None, "structured block must parse to a mapping"
    return parsed, None


def find_structured_mapping_block(content: str, root_key: str | None = None) -> tuple[dict | None, bool]:
    """Return the first parsed mapping block, optionally narrowed to a root key.

    Returns ``(mapping, candidate_parse_failed)``. ``candidate_parse_failed`` is True
    when a fenced yaml/yml/json block referenced ``root_key`` but failed to parse or did
    not parse to the expected mapping shape.
    """
    candidate_parse_failed = False
    for lang, body in iter_markdown_fenced_blocks(content):
        if lang not in _SUPPORTED_STRUCTURED_FENCE_LANGS:
            continue
        parsed, error = _parse_structured_block(lang, body)
        if root_key is None:
            if parsed is not None:
                return parsed, False
            continue
        if root_key not in body:
            continue
        if error is not None or parsed is None:
            candidate_parse_failed = True
            continue
        value = parsed.get(root_key)
        if isinstance(value, dict):
            return value, False
        candidate_parse_failed = True
    return None, candidate_parse_failed


def _fallback_markdown_key_value_map(content: str) -> dict:
    data = {}
    for line in content.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            data[key] = value
    return data


def _is_path_in_package(file_path: str | Path, package_path: str | Path) -> bool:
    """Return True iff file_path resolves under package_path (after symlink/normalization).

    Used by Gate 5.2-R1 to enforce that every declared evidence artifact lives inside the
    exported package. Absolute host paths (e.g. ``/tmp/...``) that do not resolve under
    package_path are treated as host-path leakage, not in-package evidence.
    """
    try:
        real_file = os.path.realpath(os.path.abspath(str(file_path)))
        real_pkg = os.path.realpath(os.path.abspath(str(package_path)))
        return os.path.commonpath([real_file, real_pkg]) == real_pkg
    except (ValueError, OSError):
        return False


def extract_markdown_yaml_map(path: Path) -> dict:
    content = path.read_text(encoding="utf-8", errors="ignore")
    parsed, _ = find_structured_mapping_block(content)
    if parsed is not None:
        return parsed
    return _fallback_markdown_key_value_map(content)


def normalize_domain_addenda(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1]
        items = [item.strip() for item in text.split(",")]
    else:
        return []
    result = []
    for item in items:
        if item is None:
            continue
        text = str(item).strip().strip('"').strip("'")
        if text:
            result.append(text)
    return result


def resolve_profile_context(package_path: Path, task_area: str, args) -> tuple[list[CheckResult], dict]:
    results = []
    selection_path = package_path / "reports" / task_area / "GATE_PROFILE_SELECTION.md"
    selection_data = {}
    if selection_path.exists():
        try:
            selection_data = extract_markdown_yaml_map(selection_path)
        except Exception as exc:
            results.append(CheckResult(
                "profile_selection_context",
                False,
                f"Cannot parse {selection_path.relative_to(package_path)}: {exc}",
                flag="PROFILE_SELECTION_PARSE_ERROR",
            ))

    file_profile = normalize_text(selection_data.get("selected_profile") or selection_data.get("gate_profile"))
    file_risk = normalize_text(selection_data.get("risk_tier"))
    file_task_kind = normalize_text(selection_data.get("task_kind"))
    file_domain_addenda = normalize_domain_addenda(selection_data.get("domain_addenda"))
    file_reason = normalize_text(
        selection_data.get("reason")
        or selection_data.get("profile_selection_rationale")
    )

    profile = normalize_text(args.profile) or file_profile
    risk_tier = normalize_text(args.risk_tier) or file_risk
    task_kind = normalize_text(args.task_kind) or file_task_kind

    if profile is None:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            "No selected profile supplied via CLI or GATE_PROFILE_SELECTION.md",
            flag="MISSING_GATE_PROFILE_SELECTION",
        ))
    # Gate 5.2-R1: risk_tier and task_kind are now mandatory for ALL profiles, including
    # GATE_LITE. Without them the WRONG_GATE_PROFILE selector cannot mechanically detect
    # that a package picked too-weak a profile for its actual task class.
    if risk_tier is None:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            "No risk tier supplied via CLI or GATE_PROFILE_SELECTION.md (required for all profiles, including GATE_LITE)",
            flag="MISSING_RISK_TIER",
        ))
    if task_kind is None:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            "No task kind supplied via CLI or GATE_PROFILE_SELECTION.md (required for all profiles, including GATE_LITE)",
            flag="MISSING_TASK_KIND",
        ))
    if selection_path.exists() and not file_reason:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"{selection_path.relative_to(package_path)} missing rationale/reason field (required for all profiles, including GATE_LITE)",
            flag="MISSING_PROFILE_REASON",
        ))

    if args.profile and file_profile and normalize_text(args.profile) != file_profile:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"CLI profile {args.profile} disagrees with {selection_path.relative_to(package_path)} profile {file_profile}",
            flag="PROFILE_SELECTION_DISAGREEMENT",
        ))
    if args.risk_tier and file_risk and normalize_text(args.risk_tier) != file_risk:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"CLI risk tier {args.risk_tier} disagrees with {selection_path.relative_to(package_path)} risk tier {file_risk}",
            flag="PROFILE_SELECTION_DISAGREEMENT",
        ))
    if args.task_kind and file_task_kind and normalize_text(args.task_kind) != file_task_kind:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"CLI task kind {args.task_kind} disagrees with {selection_path.relative_to(package_path)} task kind {file_task_kind}",
            flag="PROFILE_SELECTION_DISAGREEMENT",
        ))

    if profile and profile not in PROFILE_ORDER:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"Unknown profile: {profile}",
            flag="UNKNOWN_GATE_PROFILE",
        ))
    if risk_tier and risk_tier not in RISK_TIERS:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"Unknown risk tier: {risk_tier}",
            flag="UNKNOWN_RISK_TIER",
        ))
    if task_kind and task_kind not in TASK_KINDS:
        results.append(CheckResult(
            "profile_selection_context",
            False,
            f"Unknown task kind: {task_kind}",
            flag="UNKNOWN_TASK_KIND",
        ))

    return results, {
        "profile": profile,
        "risk_tier": risk_tier,
        "task_kind": task_kind,
        "domain_addenda": file_domain_addenda,
        "selection_path": selection_path,
    }


def required_min_profile(risk_tier: str | None, task_kind: str | None) -> str | None:
    if risk_tier is None or task_kind is None:
        return None
    if task_kind in {"docs", "tiny_test"} and risk_tier in {"D0", "D1"}:
        return "GATE_LITE"
    if risk_tier == "D2" and task_kind == "normal_impl":
        return "GATE_STANDARD"
    if (
        risk_tier in {"D2_HOT", "D3", "D4"}
        or task_kind in {
            "hot_file",
            "migration",
            "runtime_state",
            "merge_verification",
            "release_verification",
            "production_wiring",
            "provider_model_routing",
            "gate_change",
            "prompt_authoring",
            "evidence_package",
        }
    ):
        return "GATE_FULL"
    return "GATE_STANDARD"


def check_gate_profile_strength(profile: str | None, risk_tier: str | None, task_kind: str | None) -> list[CheckResult]:
    if profile is None:
        return []
    required = required_min_profile(risk_tier, task_kind)
    if required is None:
        return []
    if PROFILE_ORDER[profile] < PROFILE_ORDER[required]:
        return [CheckResult(
            "gate_profile_strength",
            False,
            f"Selected profile {profile} is weaker than required {required} for risk_tier={risk_tier}, task_kind={task_kind}",
            flag="WRONG_GATE_PROFILE",
        )]
    return [CheckResult(
        "gate_profile_strength",
        True,
        f"Selected profile {profile} satisfies minimum {required} for risk_tier={risk_tier}, task_kind={task_kind}",
    )]


def load_required_proof_yaml(gate_dir: Path):
    data = load_yaml_file(gate_dir / "REQUIRED_PROOF_FILES_BY_PROFILE.yaml")
    if not YAML_AVAILABLE or "_raw" in data:
        raise ValueError("PyYAML is required for structured required-proof-file checks")
    return data


def task_report_dir(package_path: Path, task_area: str) -> Path:
    return package_path / "reports" / task_area


def _existing_task_files(package_path: Path, task_area: str, pattern: str) -> list[Path]:
    report_dir = task_report_dir(package_path, task_area)
    if report_dir.exists():
        return sorted(path for path in report_dir.rglob(pattern) if path.is_file())
    return sorted(path for path in package_path.rglob(pattern) if path.is_file())


def _required_proof_templates_for_profile(data: dict, profile: str) -> list[str] | None:
    profile_data = data.get(profile)
    if profile_data is None:
        return None
    if profile == "GATE_FULL_PLUS_DOMAIN_ADDENDUM":
        inherited = profile_data.get("inherits", "GATE_FULL")
        inherited_data = data.get(inherited)
        if inherited_data is None:
            return None
        return (
            list(inherited_data.get("required_always", []))
            + list(profile_data.get("required_always", []))
            + list(profile_data.get("required_always_additional", []))
        )
    return list(profile_data.get("required_always", []))


def check_required_proof_files(
    package_path: Path,
    profile: str,
    gate_dir: Path,
    task_area: str,
    final_mode: bool,
    domain_addenda: list[str] | None = None,
) -> list[CheckResult]:
    results = []
    try:
        data = load_required_proof_yaml(gate_dir)
    except Exception as exc:
        return [CheckResult("required_proof_files", False, f"Cannot load required proof file YAML: {exc}")]

    profile_data = data.get(profile)
    if profile_data is None:
        return [CheckResult("required_proof_files", False, f"Profile {profile} not found in YAML")]

    required = _required_proof_templates_for_profile(data, profile)
    if required is None:
        return [CheckResult("required_proof_files", False, f"Cannot resolve inherited required proof files for profile {profile}")]

    if profile == "GATE_FULL_PLUS_DOMAIN_ADDENDUM":
        domain_addenda = domain_addenda or []
        if not domain_addenda:
            results.append(CheckResult(
                "required_proof_files",
                False,
                "GATE_FULL_PLUS_DOMAIN_ADDENDUM selected but domain_addenda is missing or empty",
                flag="DOMAIN_ADDENDA_MISSING",
            ))

    for template in required:
        expanded_templates = [template]
        if "{name}" in template:
            expanded_templates = []
            for addendum in domain_addenda or []:
                if not _DOMAIN_ADDENDUM_NAME_RE.match(addendum):
                    results.append(CheckResult(
                        "required_proof_files",
                        False,
                        f"Invalid domain addendum name: {addendum}",
                        flag="DOMAIN_ADDENDUM_NAME_INVALID",
                    ))
                    continue
                source_path = gate_dir / "domain_addenda" / f"{addendum}.md"
                if not source_path.exists():
                    results.append(CheckResult(
                        "required_proof_files",
                        False,
                        f"Domain addendum source missing: {source_path}",
                        flag="DOMAIN_ADDENDUM_SOURCE_MISSING",
                    ))
                expanded_templates.append(template.replace("{name}", addendum))
            if not expanded_templates:
                continue
        for expanded in expanded_templates:
            rel_path = Path(expanded.replace("{task_area}", task_area))
            if rel_path.name == "GATE_PACKAGE_VALIDATION_REPORT.md" and not final_mode:
                results.append(CheckResult(
                    "required_proof_files",
                    True,
                    f"SKIP first-run circular validation for {rel_path.as_posix()}",
                ))
                continue
            exact_path = package_path / rel_path
            if exact_path.exists():
                results.append(CheckResult("required_proof_files", True, f"{rel_path.as_posix()} found"))
            else:
                flag = "REQUIRED_PROOF_FILE_WRONG_PATH_OR_MISSING"
                if "DOMAIN_ADDENDUM_" in rel_path.name:
                    flag = "DOMAIN_ADDENDUM_PROOF_MISSING"
                results.append(CheckResult(
                    "required_proof_files",
                    False,
                    f"MISSING exact required proof path: {rel_path.as_posix()}",
                    flag=flag,
                ))
    return results


_NA_TEMPLATE_TOKENS = {
    "[STATE_NAME]",
    "[GATE_PROFILE]",
    "[one sentence]",
    "[reason]",
    "[REASON]",
    "<reason>",
    "TODO",
    "TBD",
}
_NA_PLACEHOLDER_ONLY_RE = re.compile(
    r"^\s*(?:\[reason\]|<reason>|todo|tbd|n/?a|not applicable\.?|because(?:\s+\[reason\])?|\.\.\.|lorem ipsum)\s*$",
    re.IGNORECASE,
)


def _normalize_reason_text(content: str) -> str:
    if not content:
        return ""
    text = content.translate(_ZERO_WIDTH_TRANSLATION)
    text = strip_markdown_fenced_blocks(text)
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if any(token.lower() in stripped.lower() for token in _NA_TEMPLATE_TOKENS):
            continue
        cleaned_lines.append(stripped)
    normalized = " ".join(cleaned_lines)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _reason_text_is_substantive(text: str) -> bool:
    normalized = _normalize_reason_text(text)
    if not normalized:
        return False
    lowered = normalized.lower()
    if _NA_PLACEHOLDER_ONLY_RE.match(lowered):
        return False
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", normalized)
    alpha_chars = len(re.findall(r"[A-Za-z]", normalized))
    if len(words) >= 8 and alpha_chars >= 40:
        return True
    if any(fragment in lowered for fragment in _RECOGNIZED_NA_REASON_FRAGMENTS) and alpha_chars >= 20:
        return True
    return False


def _na_reason_is_substantive(content: str) -> bool:
    return _reason_text_is_substantive(content)


def check_not_applicable_files(package_path: Path, profile: str, gate_dir: Path, task_area: str) -> list[CheckResult]:
    try:
        data = load_required_proof_yaml(gate_dir)
    except Exception:
        return []
    profile_data = data.get(profile, {})
    if profile == "GATE_FULL_PLUS_DOMAIN_ADDENDUM" and not profile_data:
        profile_data = data.get("GATE_FULL", {})

    results = []
    for state_name in profile_data.get("not_applicable_proof_required", []):
        rel_path = Path(f"reports/{task_area}/{state_name}_NOT_APPLICABLE.md")
        full_path = package_path / rel_path
        if not full_path.exists():
            # Gate 5.2-R1: missing NA proof is now blocking, not advisory.
            results.append(CheckResult(
                "not_applicable_files",
                False,
                f"MISSING required NOT_APPLICABLE proof: {rel_path.as_posix()}",
                flag="MISSING_NOT_APPLICABLE_PROOF",
            ))
            continue
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            results.append(CheckResult(
                "not_applicable_files",
                False,
                f"{rel_path.as_posix()}: cannot read file ({exc})",
                flag="NOT_APPLICABLE_REASON_MISSING",
            ))
            continue
        if not content.strip():
            results.append(CheckResult(
                "not_applicable_files",
                False,
                f"{rel_path.as_posix()}: empty file",
                flag="NOT_APPLICABLE_REASON_MISSING",
            ))
            continue
        if not _na_reason_is_substantive(content):
            results.append(CheckResult(
                "not_applicable_files",
                False,
                f"{rel_path.as_posix()}: present but missing substantive reason",
                flag="NOT_APPLICABLE_REASON_MISSING",
            ))
            continue
        results.append(CheckResult("not_applicable_files", True, f"{rel_path.as_posix()} present with substantive reason"))
    return results


def check_gate_source_included(package_path: Path):
    gate_dirs = [p for p in package_path.rglob("gate_used") if p.is_dir()]
    gate_hashes = list(package_path.rglob("gate_hash.txt"))
    if gate_dirs or gate_hashes:
        found = "gate_used/" if gate_dirs else "gate_hash.txt"
        return CheckResult("gate_source_included", True, f"Gate source proof found: {found}")
    return CheckResult(
        "gate_source_included",
        False,
        "MISSING: neither gate_used/ directory nor gate_hash.txt found",
    )


def register_raw_ref(
    raw_refs: dict[str, RawOutputRef],
    package_path: Path,
    declared: str,
    source: str,
    *,
    package_relative_override: str | None = None,
):
    """Register a raw-output reference and track host-path leakage.

    Gate 5.2-R1 adds host-path leakage detection: if ``declared`` is an absolute path
    that does not resolve under ``package_path``, the entry is marked
    ``host_path_leak=True``. If a sibling ``package_relative_override`` is supplied and
    its target exists in-package, ``has_package_relative_copy=True`` is set so the
    leak does not block PASS. The package-relative copy becomes the resolved path so
    downstream EXIT_CODE/post-PASS scanning runs against the in-package artifact.
    """
    declared = declared.strip()
    if not declared:
        return

    declared_path = Path(declared)
    host_path_leak = False
    if declared_path.is_absolute():
        if not _is_path_in_package(declared_path, package_path):
            host_path_leak = True

    candidates: list[Path] = []
    candidates.append(package_path / declared_path)
    if not declared_path.is_absolute():
        candidates.append(package_path / declared_path.name)
        candidates.extend(package_path.rglob(declared_path.name))
    resolved = None
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            resolved = candidate
            break

    has_package_relative_copy = False
    if host_path_leak and package_relative_override:
        override = Path(package_relative_override.strip())
        override_candidates: list[Path] = [package_path / override]
        if not override.is_absolute():
            override_candidates.append(package_path / override.name)
            override_candidates.extend(package_path.rglob(override.name))
        for candidate in override_candidates:
            if candidate.exists() and candidate.is_file():
                has_package_relative_copy = True
                if resolved is None:
                    resolved = candidate
                break

    key = str(declared_path).replace("\\", "/")
    if key not in raw_refs:
        raw_refs[key] = RawOutputRef(
            key=key,
            declared=declared,
            path=resolved,
            source=source,
            host_path_leak=host_path_leak,
            has_package_relative_copy=has_package_relative_copy,
        )
    else:
        existing = raw_refs[key]
        if existing.path is None and resolved is not None:
            existing.path = resolved
        if host_path_leak:
            existing.host_path_leak = True
        if has_package_relative_copy:
            existing.has_package_relative_copy = True


def discover_raw_test_outputs(package_path: Path, task_area: str | None = None) -> list[RawOutputRef]:
    raw_refs: dict[str, RawOutputRef] = {}

    ledger_paths = (
        _existing_task_files(package_path, task_area, "EVIDENCE_LEDGER.yaml")
        if task_area
        else sorted(package_path.rglob("EVIDENCE_LEDGER.yaml"))
    )
    for ledger_path in ledger_paths:
        try:
            data = load_yaml_file(ledger_path)
        except Exception:
            continue
        if not YAML_AVAILABLE or "_raw" in data:
            continue
        artifacts = data.get("artifacts", [])
        if not isinstance(artifacts, list):
            continue
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            if artifact.get("artifact_type") != "raw_test_output":
                continue
            # Gate 5.2-R1: prefer the explicit `package_path`/`package_relative_path` for
            # registration. If only `provenance_host_path` is supplied, register the host
            # path so host-path leakage detection fires; if both are supplied, register the
            # host path with the package-relative override so the in-package copy resolves
            # the leak.
            package_relative = (
                artifact.get("package_relative_path")
                or artifact.get("package_path")
            )
            provenance_host = artifact.get("provenance_host_path")
            artifact_path_field = artifact.get("artifact_path")
            artifact_filename = artifact.get("artifact_filename")

            if provenance_host:
                # Host path declared explicitly. Pair with package-relative copy if any.
                register_raw_ref(
                    raw_refs,
                    package_path,
                    str(provenance_host),
                    "evidence_ledger",
                    package_relative_override=str(package_relative) if package_relative else None,
                )
                if package_relative:
                    register_raw_ref(raw_refs, package_path, str(package_relative), "evidence_ledger")
                continue

            declared = package_relative or artifact_path_field or artifact_filename
            if declared:
                register_raw_ref(raw_refs, package_path, str(declared), "evidence_ledger")

    manifest_paths = (
        _existing_task_files(package_path, task_area, "PACKAGE_MANIFEST.md")
        if task_area
        else sorted(package_path.rglob("PACKAGE_MANIFEST.md"))
    )
    for manifest_path in manifest_paths:
        try:
            content = manifest_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        in_section = False
        header_passed = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("## Raw Test Outputs") or stripped.startswith("### Raw Test Outputs"):
                in_section = True
                header_passed = False
                continue
            if in_section and stripped.startswith("## "):
                in_section = False
            if not in_section or "|" not in stripped:
                continue
            parts = [part.strip() for part in stripped.split("|") if part.strip()]
            if not header_passed:
                if len(parts) >= 2 and parts[1] == "File":
                    header_passed = True
                continue
            if all(set(part) <= set("-: ") for part in parts):
                continue
            if len(parts) >= 2:
                register_raw_ref(raw_refs, package_path, parts[1], "package_manifest")

    exactness_paths = (
        _existing_task_files(package_path, task_area, "REQUIRED_TEST_SET_EXACTNESS*.md")
        if task_area
        else sorted(package_path.rglob("REQUIRED_TEST_SET_EXACTNESS*.md"))
    )
    for exactness_path in exactness_paths:
        if "NOT_APPLICABLE" in exactness_path.name:
            continue
        try:
            content = exactness_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line in content.splitlines():
            if "|" not in line or "raw output path" in line.lower():
                continue
            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) >= 2 and parts[-1] not in {"---", "PASS", "FAIL"}:
                register_raw_ref(raw_refs, package_path, parts[1], "required_test_set_exactness")
            elif len(parts) >= 2 and parts[1].endswith((".txt", ".log", ".out")):
                register_raw_ref(raw_refs, package_path, parts[1], "required_test_set_exactness")

    return list(raw_refs.values())


EXIT_CODE_ANY_RE = re.compile(r"^EXIT_CODE:\s*(.*?)\s*$", re.MULTILINE)
EXIT_CODE_EXACT_ZERO_RE = re.compile(r"^EXIT_CODE:0$", re.MULTILINE)
EXIT_CODE_NORMALIZED_ZERO_RE = re.compile(r"^EXIT_CODE:\s+0$", re.MULTILINE)
PASS_SUMMARY_RE = re.compile(
    r"^(PASS\s|Tests:\s+\d+\s+passed|✓\s+\d+\s+passing|All\s+tests\s+passed)",
    re.MULTILINE | re.IGNORECASE,
)
POST_PASS_ERROR_PATTERNS = [
    re.compile(r"^.*Error:", re.MULTILINE),
    re.compile(r"ENOENT", re.MULTILINE),
    re.compile(r"UnhandledPromiseRejection", re.MULTILINE),
    re.compile(r"uncaughtException", re.MULTILINE),
    re.compile(r"Jest did not exit", re.MULTILINE),
    re.compile(r"^\s{4}at ", re.MULTILINE),
]


def parse_exit_code_status(content: str) -> tuple[bool, str | None, str | None]:
    unfenced = strip_markdown_fenced_blocks(content)
    matches = EXIT_CODE_ANY_RE.findall(unfenced)
    if not matches:
        return False, "EXIT_CODE_MISSING", "no EXIT_CODE line found"
    values = [match.strip() for match in matches]
    unique_values = set(values)
    if len(unique_values) > 1:
        return False, "EXIT_CODE_CONFLICTING", f"multiple EXIT_CODE values found: {sorted(unique_values)}"
    value = values[0]
    if value == "":
        return False, "EXIT_CODE_BLANK", "EXIT_CODE line is blank"
    if not value.isdigit():
        return False, "EXIT_CODE_NON_NUMERIC", f"EXIT_CODE value '{value}' is not numeric"
    if value != "0":
        return False, "EXIT_CODE_NONZERO", f"EXIT_CODE:{value} is nonzero"
    if EXIT_CODE_EXACT_ZERO_RE.search(unfenced):
        return True, None, "EXIT_CODE:0 exact"
    if EXIT_CODE_NORMALIZED_ZERO_RE.search(unfenced):
        return True, None, "EXIT_CODE: 0 normalized"
    return False, "EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW", "EXIT_CODE value is 0 but raw line is not in accepted exact/normalized form"


def summary_docs_claim_exit_zero(package_path: Path, task_area: str | None = None) -> list[Path]:
    found = []
    seen = set()
    for pattern in SUMMARY_DOC_PATTERNS:
        docs = (
            _existing_task_files(package_path, task_area, pattern)
            if task_area
            else sorted(package_path.rglob(pattern))
        )
        for doc in docs:
            if doc in seen or not doc.is_file():
                continue
            seen.add(doc)
            try:
                content = doc.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "EXIT_CODE:0" in strip_markdown_fenced_blocks(content):
                found.append(doc)
    return found


def check_exit_code_strict(package_path: Path, profile: str, task_area: str | None = None) -> list[CheckResult]:
    results = []
    raw_outputs = discover_raw_test_outputs(package_path, task_area)
    if not raw_outputs:
        return [CheckResult("exit_code_strict", True, "No raw test outputs discovered from manifest/ledger/exactness sources")]

    summary_claim_docs = summary_docs_claim_exit_zero(package_path, task_area)
    for raw_ref in raw_outputs:
        # Gate 5.2-R1: flag absolute host paths that don't resolve into the package and
        # have no in-package copy. Evidence must be EXPORTED, not referenced from the
        # execution host's filesystem.
        if raw_ref.host_path_leak and not raw_ref.has_package_relative_copy:
            results.append(CheckResult(
                "exit_code_strict",
                False,
                f"{raw_ref.declared}: declared via {raw_ref.source} but path is absolute and resolves outside the package",
                flag="HOST_PATH_NOT_PACKAGE_EVIDENCE",
            ))
            continue
        if raw_ref.path is None:
            results.append(CheckResult(
                "exit_code_strict",
                False,
                f"{raw_ref.declared}: raw output declared via {raw_ref.source} but file is missing",
                flag="RAW_OUTPUT_DECLARED_MISSING",
            ))
            continue

        content = raw_ref.path.read_text(encoding="utf-8", errors="ignore")
        rel_path = raw_ref.path.relative_to(package_path).as_posix()
        passed, flag, detail = parse_exit_code_status(content)
        if passed:
            results.append(CheckResult("exit_code_strict", True, f"{rel_path}: {detail}"))
        else:
            results.append(CheckResult("exit_code_strict", False, f"{rel_path}: {detail}", flag=flag))
        unfenced = strip_markdown_fenced_blocks(content)
        if summary_claim_docs and not EXIT_CODE_EXACT_ZERO_RE.search(unfenced) and not EXIT_CODE_NORMALIZED_ZERO_RE.search(unfenced):
            claim_sources = ", ".join(doc.relative_to(package_path).as_posix() for doc in summary_claim_docs[:3])
            results.append(CheckResult(
                "exit_code_summary_vs_raw",
                False,
                f"{rel_path}: summary docs claim EXIT_CODE:0 but raw output lacks accepted EXIT_CODE:0 proof; sources: {claim_sources}",
                flag="EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW",
            ))

    if profile not in STANDARD_AND_UP:
        return [r for r in results if r.check_name != "exit_code_summary_vs_raw"] + [
            CheckResult("exit_code_profile_scope", True, "Gate Lite package: summary-vs-raw EXIT_CODE enforcement not required")
        ]
    return results


def check_post_pass_uncaught_errors(package_path: Path, task_area: str | None = None) -> list[CheckResult]:
    results = []
    for raw_ref in discover_raw_test_outputs(package_path, task_area):
        if raw_ref.path is None:
            continue
        content = raw_ref.path.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        pass_line_idx = None
        for index, line in enumerate(lines):
            if PASS_SUMMARY_RE.match(line):
                pass_line_idx = index
        if pass_line_idx is None:
            continue
        post_pass = "\n".join(lines[pass_line_idx + 1 :])
        for pattern in POST_PASS_ERROR_PATTERNS:
            match = pattern.search(post_pass)
            if match:
                results.append(CheckResult(
                    "post_pass_uncaught_errors",
                    False,
                    f"{raw_ref.path.relative_to(package_path).as_posix()}: post-PASS error found: {match.group(0)[:120]}",
                    flag="POST_PASS_UNCAUGHT_ERROR",
                ))
                break
        else:
            results.append(CheckResult(
                "post_pass_uncaught_errors",
                True,
                f"{raw_ref.path.relative_to(package_path).as_posix()}: no post-PASS errors found",
            ))
    return results


def check_package_stat_files(package_path: Path, profile: str, task_area: str) -> list[CheckResult]:
    if profile not in FULL_PROFILES:
        return []
    results = []
    for rel in [
        Path(f"reports/{task_area}/package_file_sizes.txt"),
        Path(f"reports/{task_area}/package_file_hashes.txt"),
    ]:
        if (package_path / rel).exists():
            results.append(CheckResult("package_stat_files", True, f"{rel.as_posix()} found"))
        else:
            results.append(CheckResult("package_stat_files", False, f"MISSING: {rel.as_posix()}"))
    return results


def check_manifest_self_size(package_path: Path, task_area: str | None = None) -> list[CheckResult]:
    manifests = (
        _existing_task_files(package_path, task_area, "PACKAGE_MANIFEST.md")
        if task_area
        else sorted(package_path.rglob("PACKAGE_MANIFEST.md"))
    )
    if not manifests:
        return [CheckResult("manifest_self_size", True, "No PACKAGE_MANIFEST.md found — skipping")]
    results = []
    patterns = [
        re.compile(r"PACKAGE_MANIFEST\.md[^\n]*\|\s*(\d+)\s*bytes", re.IGNORECASE),
        re.compile(r"PACKAGE_MANIFEST\.md[^\n]*\s+(\d+)\s*$", re.MULTILINE),
    ]
    for manifest in manifests:
        content = manifest.read_text(encoding="utf-8", errors="ignore")
        listed_size = None
        for pattern in patterns:
            match = pattern.search(content)
            if match:
                listed_size = int(match.group(1))
                break
        rel_path = manifest.relative_to(package_path).as_posix()
        actual = manifest.stat().st_size
        if listed_size is None:
            results.append(CheckResult("manifest_self_size", True, f"{rel_path}: no self-size entry found"))
        elif listed_size == 0:
            results.append(CheckResult(
                "manifest_self_size",
                False,
                f"{rel_path}: manifest lists itself as 0 bytes (actual {actual})",
                flag="MANIFEST_SELF_SIZE_STALE",
            ))
        else:
            ratio = abs(listed_size - actual) / max(actual, 1)
            if ratio > 0.10:
                results.append(CheckResult(
                    "manifest_self_size",
                    False,
                    f"{rel_path}: listed size {listed_size} differs from actual {actual} by more than 10%",
                    flag="MANIFEST_SELF_SIZE_STALE",
                ))
            else:
                results.append(CheckResult("manifest_self_size", True, f"{rel_path}: self-size within tolerance"))
    return results


def dirty_paths_from_git_status(content: str) -> list[str]:
    dirty = []
    for line in content.splitlines():
        raw = line.rstrip("\r\n")
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("On branch ") or stripped.startswith("git status") or stripped.startswith("git rev-parse"):
            continue
        if "working tree clean" in stripped.lower() or "(empty" in stripped.lower():
            continue
        path = None
        if len(raw) >= 3 and raw[2] == " " and re.match(r"^[ MARCUD\?!]{2}\s", raw):
            path = raw[3:]
        elif len(raw) >= 2 and raw[1] == " " and re.match(r"^[MARCUD\?!]\s", raw):
            path = raw[2:]
        if path is not None:
            dirty.append(path.strip())
    return dirty


def find_dirty_worktree_classification(package_path: Path) -> Path | None:
    candidates = [
        "DIRTY_WORKTREE_CLASSIFICATION.md",
        "DIRTY_WORKTREE_RECURRENCE.md",
        "DIRTY_WORKTREE_RECURRENCE_AUDIT.md",
    ]
    for candidate in candidates:
        matches = list(package_path.rglob(candidate))
        if matches:
            return matches[0]
    return None


def check_final_git_status(package_path: Path, profile: str, task_area: str) -> list[CheckResult]:
    rel = Path(f"reports/{task_area}/git_status_final.txt")
    if not (package_path / rel).exists():
        matches = list(package_path.rglob("git_status_final.txt"))
        if matches:
            git_status_path = matches[0]
        else:
            return [CheckResult("final_git_status", False, "MISSING: git_status_final.txt", flag="MISSING_GIT_STATUS_PROOF")]
    else:
        git_status_path = package_path / rel

    content = git_status_path.read_text(encoding="utf-8", errors="ignore")
    if not content.strip():
        return [CheckResult("final_git_status", True, f"{git_status_path.relative_to(package_path).as_posix()}: empty file accepted as clean worktree proof")]
    if "working tree clean" in content.lower() or "(empty" in content.lower():
        return [CheckResult("final_git_status", True, f"{git_status_path.relative_to(package_path).as_posix()}: clean worktree markers found")]

    dirty_paths = dirty_paths_from_git_status(content)
    if not dirty_paths:
        return [CheckResult("final_git_status", True, f"{git_status_path.relative_to(package_path).as_posix()}: no dirty paths parsed")]

    if profile not in FULL_PROFILES:
        return [CheckResult("final_git_status", True, f"{git_status_path.relative_to(package_path).as_posix()}: dirty paths present but Gate Full classification not required for this profile")]

    classification_path = find_dirty_worktree_classification(package_path)
    if classification_path is None:
        return [CheckResult(
            "final_git_status",
            False,
            f"{git_status_path.relative_to(package_path).as_posix()}: dirty paths present with no classification file",
            flag="DIRTY_GIT_STATUS_UNCLASSIFIED",
        )]

    text = classification_path.read_text(encoding="utf-8", errors="ignore")
    # Gate 5.2-R1: approved dirty-worktree labels (any of these allows non-empty
    # git_status_final.txt if EVERY dirty path is classified with one of them).
    approved_labels = (
        "ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH",
        "AMBIENT_UNRELATED_DOC_COMMIT",
        "UNRELATED_EXTERNAL_WORK",
        "UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN",
    )
    # Always-blocking generated/runtime tokens (regardless of label).
    always_blocking_tokens = (
        "node_modules",
        ".run_artifacts",
        "raw_test_output",
        "raw_outputs",
        "doc_freshness_report",
    )
    results = []
    for dirty_path in dirty_paths:
        lower = dirty_path.lower()
        if any(token in lower for token in always_blocking_tokens):
            results.append(CheckResult(
                "final_git_status",
                False,
                f"{dirty_path}: generated/runtime evidence path is dirty (blocking regardless of label)",
                flag="DIRTY_GIT_STATUS_TASK_RELEVANT",
            ))
            continue
        if dirty_path not in text:
            results.append(CheckResult(
                "final_git_status",
                False,
                f"{dirty_path}: missing from dirty-worktree classification",
                flag="DIRTY_PATH_NOT_CLASSIFIED",
            ))
            continue
        # Build a regex that captures whichever label appears on the same row as the
        # dirty path. Markdown table rows separate cells with `|`, so consume up to the
        # next row break.
        label_pattern = re.compile(
            re.escape(dirty_path) + r"[^\n]*?(" + "|".join(approved_labels) + r"|UNKNOWN_REQUIRES_HUMAN|unrelated external work)",
            re.IGNORECASE,
        )
        match = label_pattern.search(text)
        if not match:
            # Path is mentioned but not paired with any approved or known-blocker label.
            results.append(CheckResult(
                "final_git_status",
                False,
                f"{dirty_path}: classification row missing approved label",
                flag="DIRTY_PATH_NOT_CLASSIFIED",
            ))
            continue
        label = match.group(1).upper().replace(" ", "_").replace("-", "_")
        if "UNKNOWN_REQUIRES_HUMAN" in label:
            results.append(CheckResult(
                "final_git_status",
                False,
                f"{dirty_path}: classified UNKNOWN_REQUIRES_HUMAN — blocking until classification is resolved",
                flag="UNKNOWN_REQUIRES_HUMAN_BLOCKER",
            ))
            continue
        if "UNRELATED_EXTERNAL_WORK" in label:
            results.append(CheckResult(
                "final_git_status",
                True,
                f"{dirty_path}: classified UNRELATED_EXTERNAL_WORK",
            ))
            continue
        if "ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH" in label:
            results.append(CheckResult(
                "final_git_status",
                True,
                f"{dirty_path}: classified ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH",
            ))
            continue
        if "AMBIENT_UNRELATED_DOC_COMMIT" in label:
            results.append(CheckResult(
                "final_git_status",
                True,
                f"{dirty_path}: classified AMBIENT_UNRELATED_DOC_COMMIT",
            ))
            continue
        if "UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN" in label:
            results.append(CheckResult(
                "final_git_status",
                True,
                f"{dirty_path}: classified UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN",
            ))
            continue
        results.append(CheckResult(
            "final_git_status",
            False,
            f"{dirty_path}: classification label {label} is not in approved set",
            flag="DIRTY_GIT_STATUS_TASK_RELEVANT",
        ))
    return results


def check_required_test_set_exactness(package_path: Path, profile: str, task_area: str | None = None) -> list[CheckResult]:
    files = [
        path for path in (
            _existing_task_files(package_path, task_area, "REQUIRED_TEST_SET_EXACTNESS*.md")
            if task_area
            else sorted(package_path.rglob("REQUIRED_TEST_SET_EXACTNESS*.md"))
        )
        if "NOT_APPLICABLE" not in path.name
    ]
    if not files:
        na = (
            _existing_task_files(package_path, task_area, "REQUIRED_TEST_SET_EXACTNESS_NOT_APPLICABLE.md")
            if task_area
            else list(package_path.rglob("REQUIRED_TEST_SET_EXACTNESS_NOT_APPLICABLE.md"))
        )
        if na:
            return [CheckResult("required_test_set_exactness", True, "REQUIRED_TEST_SET_EXACTNESS_NOT_APPLICABLE.md found")]
        return [CheckResult("required_test_set_exactness", True, "No REQUIRED_TEST_SET_EXACTNESS file found")]
    results = []
    for path in files:
        content = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(package_path).as_posix()
        if re.search(r"\|\s*FAIL\s*\|?\s*$", content, re.MULTILINE):
            results.append(CheckResult("required_test_set_exactness", False, f"{rel}: contains FAIL verdict", flag="REQUIRED_TEST_SET_FAIL"))
        elif profile in FULL_PROFILES and "EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW" in content:
            results.append(CheckResult(
                "required_test_set_exactness",
                False,
                f"{rel}: contains EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW",
                flag="EXIT_CODE_ONLY_IN_SUMMARY_NOT_RAW",
            ))
        else:
            results.append(CheckResult("required_test_set_exactness", True, f"{rel}: no FAIL verdicts found"))
    return results


def check_warning_audit(package_path: Path, task_area: str | None = None) -> list[CheckResult]:
    files = [
        path for path in (
            _existing_task_files(package_path, task_area, "WARNING_OUTPUT_AUDIT*.md")
            if task_area
            else sorted(package_path.rglob("WARNING_OUTPUT_AUDIT*.md"))
        )
        if "NOT_APPLICABLE" not in path.name and "TEMPLATE" not in path.name
    ]
    if not files:
        na = (
            _existing_task_files(package_path, task_area, "WARNING_OUTPUT_AUDIT_NOT_APPLICABLE.md")
            if task_area
            else list(package_path.rglob("WARNING_OUTPUT_AUDIT_NOT_APPLICABLE.md"))
        )
        if na:
            return [CheckResult("warning_audit", True, "WARNING_OUTPUT_AUDIT_NOT_APPLICABLE.md found")]
        return [CheckResult("warning_audit", True, "No WARNING_OUTPUT_AUDIT file found")]
    results = []
    for path in files:
        content = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(package_path).as_posix()
        structured, _ = find_structured_mapping_block(content, "warning_output_audit")
        if structured is not None:
            verdict = str(structured.get("verdict", "")).strip().upper()
            blocking_warnings = structured.get("blocking_warnings", [])
            if not isinstance(blocking_warnings, list):
                blocking_warnings = [str(blocking_warnings)]
            pass_equiv = {"PASS", "WARNING_OUTPUT_AUDIT_PASS"}
            fail_equiv = {"FAIL", "BLOCKING_FOUND", "WARNING_OUTPUT_AUDIT_BLOCKING_FOUND"}
            if verdict in pass_equiv:
                if blocking_warnings:
                    results.append(CheckResult(
                        "warning_audit",
                        False,
                        f"{rel}: structured verdict is PASS but blocking_warnings is non-empty: {blocking_warnings}",
                        flag="WARNING_OUTPUT_AUDIT_VERDICT_INCONSISTENT",
                    ))
                else:
                    results.append(CheckResult("warning_audit", True, f"{rel}: structured verdict PASS with no blocking warnings"))
                continue
            if verdict in fail_equiv:
                upper_joined = " ".join(str(item).upper() for item in blocking_warnings)
                flag = next((token for token in BLOCKING_WARNING_TOKENS if token in upper_joined), "WARNING_OUTPUT_AUDIT_BLOCKING_FOUND")
                results.append(CheckResult(
                    "warning_audit",
                    False,
                    f"{rel}: structured verdict {verdict} with blocking warnings {blocking_warnings}",
                    flag=flag,
                ))
                continue
        token = next((token for token in BLOCKING_WARNING_TOKENS if _scan_blocking_token_with_negation(content, token)), None)
        if token:
            results.append(CheckResult("warning_audit", False, f"{rel}: unresolved blocking token {token} present", flag=token))
        else:
            results.append(CheckResult("warning_audit", True, f"{rel}: no unresolved blocking tokens found"))
    return results


_OUTPUT_CONTRACT_VERDICT_BLOCK_RE = re.compile(
    r"```yaml\s*\n(?P<body>.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def _extract_structured_output_contract_verdict(content: str) -> dict | None:
    """Find a fenced YAML block containing the ``output_contract_consistency`` key.

    Gate 5.2-R1 prefers a structured verdict block to avoid false positives from
    negated prose like "no STALE_MILESTONE_LABEL". Returns the parsed
    ``output_contract_consistency`` mapping, or None if no structured block is found.
    """
    if not YAML_AVAILABLE:
        return None
    for match in _OUTPUT_CONTRACT_VERDICT_BLOCK_RE.finditer(content):
        body = match.group("body")
        if "output_contract_consistency" not in body:
            continue
        try:
            parsed = yaml.safe_load(body)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, dict) and isinstance(parsed.get("output_contract_consistency"), dict):
            return parsed["output_contract_consistency"]
    return None


def _scan_blocking_token_with_negation(content: str, token: str) -> bool:
    """Return True iff ``token`` appears in a non-negated, non-heading context.

    Skips matches like:
      - "no STALE_MILESTONE_LABEL"
      - "STALE_MILESTONE_LABEL not found"
      - "STALE_MILESTONE_LABEL: none"
      - "STALE_MILESTONE_LABEL: absent"
      - lines that are pure markdown headings (e.g. ``# STALE_MILESTONE_LABEL``)
      - lines inside fenced code blocks (which usually quote the token as a label name)
    """
    for raw_line in strip_markdown_fenced_blocks(content).splitlines():
        stripped = raw_line.strip()
        if token not in stripped:
            continue
        # Skip pure markdown headings.
        if stripped.lstrip("#").strip() == token:
            continue
        if re.match(r"^#{1,6}\s+" + re.escape(token) + r"\s*$", stripped):
            continue
        # Find each occurrence and inspect the surrounding context on this line.
        for match in re.finditer(re.escape(token), stripped):
            start, end = match.span()
            preceding = stripped[:start].lower()
            following = stripped[end:].lower().lstrip()
            # Negation prefixes within ~30 chars
            preceding_window = preceding[-30:]
            if re.search(r"\bno\b\s*$", preceding_window):
                continue
            if re.search(r"\bnot\b\s*$", preceding_window):
                continue
            if re.search(r"\babsent\b[^a-z]*$", preceding_window):
                continue
            if re.search(r"\bzero\b[^a-z]*$", preceding_window):
                continue
            if re.search(r"\bnone\b[^a-z]*$", preceding_window):
                continue
            # Negation suffixes
            if following.startswith((
                "not found",
                "not detected",
                "not present",
                "is not",
                "absent",
                ": none",
                ": absent",
                ": not found",
                ": no",
                "= none",
            )):
                continue
            if following.startswith(":") and re.match(r":\s*(none|absent|n\/a|not\s+found|no)\b", following):
                continue
            # If the line starts a markdown table header listing the token as a column
            # name (e.g. ``| token | description |``), skip it.
            if "|" in stripped and stripped.startswith("|"):
                cells = [cell.strip().lower() for cell in stripped.strip("|").split("|")]
                if token.lower() in cells and not any("detected" in cell or "found" in cell for cell in cells):
                    continue
            return True
    return False


def check_output_contract_consistency(package_path: Path, profile: str, task_area: str) -> list[CheckResult]:
    if profile not in FULL_PROFILES:
        return []
    audit_path = package_path / "reports" / task_area / "OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md"
    na_path = package_path / "reports" / task_area / "OUTPUT_CONTRACT_CONSISTENCY_AUDIT_NOT_APPLICABLE.md"
    if audit_path.exists():
        content = audit_path.read_text(encoding="utf-8", errors="ignore")
        rel = audit_path.relative_to(package_path).as_posix()
        # Gate 5.2-R1: prefer structured verdict block
        structured = _extract_structured_output_contract_verdict(content)
        if structured is not None:
            verdict = str(structured.get("verdict", "")).strip().upper()
            blocking_findings = structured.get("blocking_findings") or []
            if not isinstance(blocking_findings, list):
                blocking_findings = [str(blocking_findings)]
            checked_surfaces = structured.get("checked_surfaces") or []
            results: list[CheckResult] = []
            if verdict not in {"PASS", "FAIL", "UNCERTAIN"}:
                results.append(CheckResult(
                    "output_contract_consistency",
                    False,
                    f"{rel}: structured verdict has unknown value '{verdict}'",
                    flag="OUTPUT_CONTRACT_VERDICT_UNKNOWN",
                ))
                return results
            if verdict in {"FAIL", "UNCERTAIN"}:
                first_finding = blocking_findings[0] if blocking_findings else None
                # Pick a flag matching the first known token if possible.
                token_flag = None
                if first_finding:
                    upper = str(first_finding).upper()
                    for token in BLOCKING_CONTRACT_TOKENS:
                        if token in upper:
                            token_flag = token
                            break
                results.append(CheckResult(
                    "output_contract_consistency",
                    False,
                    f"{rel}: structured verdict is {verdict}; findings={blocking_findings}",
                    flag=token_flag or ("STALE_MILESTONE_LABEL" if verdict == "FAIL" else "OUTPUT_CONTRACT_VERDICT_UNCERTAIN"),
                ))
                return results
            # verdict == PASS
            if blocking_findings:
                results.append(CheckResult(
                    "output_contract_consistency",
                    False,
                    f"{rel}: structured verdict is PASS but blocking_findings is non-empty: {blocking_findings}",
                    flag="OUTPUT_CONTRACT_VERDICT_INCONSISTENT",
                ))
                return results
            if not checked_surfaces:
                results.append(CheckResult(
                    "output_contract_consistency",
                    True,
                    f"{rel}: structured verdict PASS but checked_surfaces is empty (warn)",
                ))
            else:
                results.append(CheckResult(
                    "output_contract_consistency",
                    True,
                    f"{rel}: structured verdict PASS over {len(checked_surfaces)} surfaces",
                ))
            return results

        # Fallback prose scan with negation awareness.
        for token in BLOCKING_CONTRACT_TOKENS:
            if _scan_blocking_token_with_negation(content, token):
                return [CheckResult(
                    "output_contract_consistency",
                    False,
                    f"{rel}: blocking contradiction token {token} present (fallback prose scan)",
                    flag=token,
                )]
        return [CheckResult(
            "output_contract_consistency",
            True,
            f"{rel}: present with no blocking contradiction tokens (fallback prose scan)",
        )]
    if na_path.exists():
        text = na_path.read_text(encoding="utf-8", errors="ignore")
        if _na_reason_is_substantive(text):
            return [CheckResult("output_contract_consistency", True, f"{na_path.relative_to(package_path).as_posix()}: not applicable with reason recorded")]
        return [CheckResult(
            "output_contract_consistency",
            False,
            f"{na_path.relative_to(package_path).as_posix()}: missing specific not-applicable reason",
            flag="OUTPUT_CONTRACT_NA_REASON_MISSING",
        )]
    return [CheckResult(
        "output_contract_consistency",
        False,
        f"MISSING: reports/{task_area}/OUTPUT_CONTRACT_CONSISTENCY_AUDIT.md",
        flag="MISSING_OUTPUT_CONTRACT_CONSISTENCY_AUDIT",
    )]


def check_checker_report_included(package_path: Path, profile: str, task_area: str, final_mode: bool) -> list[CheckResult]:
    if profile not in FULL_PROFILES:
        return []
    rel = Path(f"reports/{task_area}/GATE_PACKAGE_VALIDATION_REPORT.md")
    if (package_path / rel).exists():
        return [CheckResult("checker_report_included", True, f"{rel.as_posix()} found")]
    if final_mode:
        return [CheckResult(
            "checker_report_included",
            False,
            f"MISSING final-mode checker report: {rel.as_posix()}",
            flag="MISSING_CHECKER_REPORT_FINAL_MODE",
        )]
    return [CheckResult("checker_report_included", True, f"{rel.as_posix()} skipped in non-final first-run mode")]


# -----------------------------------------------------------------------------
# Gate 5.4 — Final Packet Auditor enforcement
# -----------------------------------------------------------------------------

_FINAL_AUDITOR_ALLOWED_VERDICTS = {"PASS", "FAIL", "HUMAN_DECISION_REQUIRED"}
_FINAL_AUDITOR_ALLOWED_CONTEXTS = {"fresh-subagent", "fresh-session", "fresh-model", "isolated-session"}
_FINAL_AUDITOR_HANDOFF_READY_TOKENS = (
    "READY",
    "MERGED",
    "VERIFIED",
    "PASS_HANDOFF_COMPLETE",
    "ACCEPTED",
)
_FINAL_AUDITOR_HANDOFF_BLOCKED_TOKENS = (
    "BLOCKED",
    "HUMAN_DECISION",
    "REQUIRES_HUMAN",
    "NEEDS_HUMAN",
)


def _normalize_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _valid_final_auditor_rerun(value: str) -> bool:
    return value in {"BEGINNING", "HUMAN_DECISION"} or value.startswith("TARGETED_STATE:")


def _read_handoff_text(package_path: Path, task_area: str) -> str:
    """Return concatenated text of every status-bearing handoff document the package
    exposes. The auditor verdict cross-checks the handoff(s)."""
    candidates = [
        package_path / "reports" / task_area / "HANDOFF.md",
        package_path / "reports" / task_area / "BLOCKED_HANDOFF.md",
    ]
    chunks = []
    for path in candidates:
        if path.is_file():
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
    return "\n".join(chunks)


def check_final_packet_auditor_report(
    package_path: Path,
    profile: str,
    task_area: str,
) -> list[CheckResult]:
    """Gate 5.4: Verify FINAL_PACKET_AUDITOR_REPORT.md exists with required schema.

    Emitted flags:
      - FINAL_PACKET_AUDITOR_MISSING
      - FINAL_PACKET_AUDITOR_FAIL
      - FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED
      - FINAL_PACKET_AUDITOR_SCHEMA_INVALID
      - FINAL_PACKET_AUDITOR_RERUN_REQUIRED
    """
    report_path = package_path / "reports" / task_area / "FINAL_PACKET_AUDITOR_REPORT.md"
    na_path = package_path / "reports" / task_area / "FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md"

    if not report_path.is_file():
        if profile == "GATE_LITE" and na_path.is_file():
            try:
                na_content = na_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                return [CheckResult(
                    "final_packet_auditor",
                    False,
                    f"FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md unreadable ({exc})",
                    flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
                )]
            if _na_reason_is_substantive(na_content):
                return [CheckResult(
                    "final_packet_auditor",
                    True,
                    "NOT_APPLICABLE for GATE_LITE non-export",
                )]
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_NOT_APPLICABLE.md lacks substantive reason",
                flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
            )]
        return [CheckResult(
            "final_packet_auditor",
            False,
            f"FINAL_PACKET_AUDITOR_MISSING: {report_path.relative_to(package_path).as_posix()} not found",
            flag="FINAL_PACKET_AUDITOR_MISSING",
        )]

    try:
        content = report_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return [CheckResult(
            "final_packet_auditor",
            False,
            f"FINAL_PACKET_AUDITOR_REPORT.md unreadable ({exc})",
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]

    auditor_block, parse_failed = find_structured_mapping_block(content, "final_packet_auditor")
    if auditor_block is None:
        message = "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: missing structured final_packet_auditor block"
        if parse_failed:
            message = "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: structured final_packet_auditor block failed to parse"
        return [CheckResult(
            "final_packet_auditor",
            False,
            message,
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]

    verdict = str(auditor_block.get("verdict", "")).strip().upper()
    reason = auditor_block.get("reason")
    blockers = auditor_block.get("blockers")
    required_fix = auditor_block.get("required_fix")
    rerun_from = str(auditor_block.get("rerun_from", "")).strip()
    missing_keys = [
        key for key in ("verdict", "reason", "blockers", "required_fix", "rerun_from", "independence")
        if key not in auditor_block
    ]
    if missing_keys:
        return [CheckResult(
            "final_packet_auditor",
            False,
            f"FINAL_PACKET_AUDITOR_SCHEMA_INVALID: missing keys {missing_keys}",
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]
    if verdict not in _FINAL_AUDITOR_ALLOWED_VERDICTS:
        return [CheckResult(
            "final_packet_auditor",
            False,
            "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: verdict not in PASS|FAIL|HUMAN_DECISION_REQUIRED",
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]
    if not _reason_text_is_substantive(str(reason)):
        return [CheckResult(
            "final_packet_auditor",
            False,
            "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: reason is missing or non-substantive",
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]
    if not isinstance(blockers, list):
        return [CheckResult(
            "final_packet_auditor",
            False,
            "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: blockers must be a list",
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]
    if not _valid_final_auditor_rerun(rerun_from):
        return [CheckResult(
            "final_packet_auditor",
            False,
            "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: rerun_from must be BEGINNING, HUMAN_DECISION, or TARGETED_STATE:<state>",
            flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
        )]
    if verdict == "PASS":
        if blockers:
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: PASS verdict requires empty blockers",
                flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
            )]
        if isinstance(required_fix, list):
            if required_fix:
                return [CheckResult(
                    "final_packet_auditor",
                    False,
                    "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: PASS verdict requires required_fix to be NONE or an empty list",
                    flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
                )]
        elif str(required_fix).strip().upper() not in {"", "NONE"}:
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: PASS verdict requires required_fix to be NONE or empty",
                flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
            )]
    if verdict == "FAIL":
        if not blockers:
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: FAIL verdict requires non-empty blockers",
                flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
            )]
        if not _reason_text_is_substantive(str(required_fix)):
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: FAIL verdict requires substantive required_fix",
                flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
            )]
    if verdict == "HUMAN_DECISION_REQUIRED":
        combined = f"{reason} {required_fix}"
        if "human" not in combined.lower() and "operator" not in combined.lower() and "decision" not in combined.lower():
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_SCHEMA_INVALID: HUMAN_DECISION_REQUIRED must explain the human decision needed",
                flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
            )]

    independence = auditor_block.get("independence")
    if profile in STANDARD_AND_UP:
        if not isinstance(independence, dict):
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED: independence block missing or invalid",
                flag="FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED",
            )]
        achieved = independence.get("achieved")
        if not isinstance(achieved, bool):
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED: independence.achieved must be boolean",
                flag="FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED",
            )]
        auditor_context = str(independence.get("auditor_context", "")).strip()
        auditor_model = str(independence.get("auditor_model", "")).strip()
        auditor_session_id = str(independence.get("auditor_session_id", "")).strip()
        implementer_session_id = str(independence.get("implementer_session_id", "")).strip()
        prior_reviewer_session_ids = _normalize_list(independence.get("prior_reviewer_session_ids"))
        prior_reviewer_session_ids = [str(item).strip() for item in prior_reviewer_session_ids if str(item).strip()]
        if verdict == "PASS" and not achieved:
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_INDEPENDENCE_NOT_ACHIEVED: PASS verdict requires achieved=true",
                flag="FINAL_PACKET_AUDITOR_INDEPENDENCE_NOT_ACHIEVED",
            )]
        if achieved:
            if not all([auditor_context, auditor_model, auditor_session_id, implementer_session_id]):
                return [CheckResult(
                    "final_packet_auditor",
                    False,
                    "FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED: required independence provenance fields are missing",
                    flag="FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED",
                )]
            if auditor_context not in _FINAL_AUDITOR_ALLOWED_CONTEXTS:
                return [CheckResult(
                    "final_packet_auditor",
                    False,
                    f"FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED: unsupported auditor_context '{auditor_context}'",
                    flag="FINAL_PACKET_AUDITOR_INDEPENDENCE_UNVERIFIED",
                )]
            if auditor_session_id == implementer_session_id or auditor_session_id in prior_reviewer_session_ids:
                return [CheckResult(
                    "final_packet_auditor",
                    False,
                    "FINAL_PACKET_AUDITOR_INDEPENDENCE_CONFLICT: auditor session matches implementer or prior reviewer session",
                    flag="FINAL_PACKET_AUDITOR_INDEPENDENCE_CONFLICT",
                )]

    handoff_text = _read_handoff_text(package_path, task_area)
    handoff_claims_ready = any(token in handoff_text for token in _FINAL_AUDITOR_HANDOFF_READY_TOKENS)
    handoff_claims_blocked = any(token in handoff_text for token in _FINAL_AUDITOR_HANDOFF_BLOCKED_TOKENS)

    if verdict == "FAIL":
        return [CheckResult(
            "final_packet_auditor",
            False,
            "FINAL_PACKET_AUDITOR_FAIL: auditor verdict is FAIL",
            flag="FINAL_PACKET_AUDITOR_FAIL",
        )]

    if verdict == "HUMAN_DECISION_REQUIRED":
        if not handoff_claims_blocked:
            return [CheckResult(
                "final_packet_auditor",
                False,
                "FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED: verdict is HUMAN_DECISION_REQUIRED but handoff does not declare a blocked/human-decision status",
                flag="FINAL_PACKET_AUDITOR_HUMAN_DECISION_REQUIRED",
            )]

    if rerun_from == "BEGINNING" and handoff_claims_ready:
        return [CheckResult(
            "final_packet_auditor",
            False,
            "FINAL_PACKET_AUDITOR_RERUN_REQUIRED: RERUN_FROM is BEGINNING but final status claims READY/MERGED/VERIFIED",
            flag="FINAL_PACKET_AUDITOR_RERUN_REQUIRED",
        )]

    if verdict == "PASS":
        return [CheckResult(
            "final_packet_auditor",
            True,
            f"auditor verdict PASS, rerun_from={rerun_from}",
        )]

    if verdict == "HUMAN_DECISION_REQUIRED":
        return [CheckResult(
            "final_packet_auditor",
            True,
            f"auditor verdict HUMAN_DECISION_REQUIRED with consistent blocked handoff, rerun_from={rerun_from}",
        )]

    return [CheckResult(
        "final_packet_auditor",
        False,
        f"unexpected state: verdict={verdict}, rerun_from={rerun_from}",
        flag="FINAL_PACKET_AUDITOR_SCHEMA_INVALID",
    )]


def print_report(results: list[CheckResult], task_area: str):
    width = 72
    print("=" * width)
    print("check_gate_package — Gate 5.4")
    print(f"Task area: {task_area}")
    print("=" * width)
    passed = failed = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        flag = f" [{result.flag}]" if result.flag else ""
        print(f"[{status}] {result.check_name}{flag}: {result.message}")
        if result.passed:
            passed += 1
        else:
            failed += 1
    print("-" * width)
    print(f"Result: {'PASS' if failed == 0 else 'FAIL'}")
    print(f"Checks passed: {passed}  |  Checks failed: {failed}")
    if failed:
        print("\nBlocking issues:")
        for result in results:
            if not result.passed:
                flag = f" [{result.flag}]" if result.flag else ""
                print(f"  - {result.check_name}{flag}: {result.message}")
    print("=" * width)


def write_report_to_package(results: list[CheckResult], package_path: Path, task_area: str, final_mode: bool) -> Path:
    report_dir = package_path / "reports" / task_area
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "GATE_PACKAGE_VALIDATION_REPORT.md"
    passed = sum(1 for result in results if result.passed)
    failed = sum(1 for result in results if not result.passed)
    lines = [
        "# Gate Package Validation Report",
        "",
        f"**Generated by:** check_gate_package.py (Gate 5.4)",
        f"**Task area:** {task_area}",
        f"**Validation mode:** {'final' if final_mode else 'first-run'}",
        f"**Result:** {'PASS' if failed == 0 else 'FAIL'}",
        f"**Checks passed:** {passed}",
        f"**Checks failed:** {failed}",
        "",
        "| Check | Status | Flag | Message |",
        "|---|---|---|---|",
    ]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        flag = result.flag or ""
        message = result.message.replace("|", "\\|")
        lines.append(f"| {result.check_name} | {status} | {flag} | {message} |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Gate 5.4 package checker. Validates proof files, profile/risk selection, raw output proof, warning audits, package integrity, domain addenda, and the final packet auditor report."
    )
    parser.add_argument("--package", required=True, help="Path to package zip or directory")
    parser.add_argument("--profile", choices=list(PROFILE_ORDER), help="Selected gate profile")
    parser.add_argument("--task-area", required=True, help="Task area string used for report paths")
    parser.add_argument("--task-prompt", default=None, help="Optional task prompt path")
    parser.add_argument("--gate-dir", default=None, help="Path to gate folder")
    parser.add_argument("--risk-tier", choices=sorted(RISK_TIERS), help="Risk tier input")
    parser.add_argument("--task-kind", choices=sorted(TASK_KINDS), help="Task kind input")
    parser.add_argument("--final", action="store_true", help="Require final checker report presence; only final mode PASS supports acceptance")
    return parser.parse_args()


def main():
    args = parse_args()
    gate_dir = Path(args.gate_dir) if args.gate_dir else Path(__file__).parent.parent
    if not gate_dir.exists():
        print(f"ERROR: Gate directory not found: {gate_dir}", file=sys.stderr)
        sys.exit(2)

    package_path, cleanup = load_package(args.package)
    try:
        results: list[CheckResult] = []
        context_results, context = resolve_profile_context(package_path, args.task_area, args)
        results.extend(context_results)
        profile = context["profile"]
        if profile is None:
            print_report(results, args.task_area)
            write_report_to_package(results, package_path, args.task_area, args.final)
            sys.exit(1)

        results.extend(check_gate_profile_strength(profile, context["risk_tier"], context["task_kind"]))
        results.extend(check_required_proof_files(
            package_path,
            profile,
            gate_dir,
            args.task_area,
            args.final,
            context.get("domain_addenda"),
        ))
        results.extend(check_not_applicable_files(package_path, profile, gate_dir, args.task_area))
        results.append(check_gate_source_included(package_path))
        results.extend(check_exit_code_strict(package_path, profile, args.task_area))
        results.extend(check_post_pass_uncaught_errors(package_path, args.task_area))
        results.extend(check_package_stat_files(package_path, profile, args.task_area))
        results.extend(check_manifest_self_size(package_path, args.task_area))
        results.extend(check_final_git_status(package_path, profile, args.task_area))
        results.extend(check_required_test_set_exactness(package_path, profile, args.task_area))
        results.extend(check_warning_audit(package_path, args.task_area))
        results.extend(check_output_contract_consistency(package_path, profile, args.task_area))
        results.extend(check_checker_report_included(package_path, profile, args.task_area, args.final))
        results.extend(check_final_packet_auditor_report(package_path, profile, args.task_area))

        print_report(results, args.task_area)
        report_path = write_report_to_package(results, package_path, args.task_area, args.final)
        print(f"\nReport written to: {report_path}")
        failed = sum(1 for result in results if not result.passed)
        sys.exit(0 if failed == 0 else 1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
