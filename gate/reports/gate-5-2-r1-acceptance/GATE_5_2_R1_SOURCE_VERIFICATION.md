# Gate 5.2-R1 Source Verification

**Date:** 2026-05-01
**Source-of-truth:** `/Users/syedhaider/Downloads/gate/tools/check_gate_package.py` (1403 lines)

For each of the 7 R1 behaviors required by the acceptance protocol, evidence is taken from the actual installed source, not implementer claims.

| # | R1 Behavior | Verdict | Evidence |
|---|-------------|---------|----------|
| 1 | Absolute host paths cannot serve as package evidence | **PASS** | See below |
| 2 | All profiles (incl. GATE_LITE) require selected_profile + risk_tier + task_kind + rationale | **PASS** | See below |
| 3 | NOT_APPLICABLE proof files are hard requirements with substantive-reason check | **PASS** | See below |
| 4 | Dirty-worktree classification accepts the 4 approved labels and blocks UNKNOWN_REQUIRES_HUMAN / unclassified paths | **PASS** | See below |
| 5 | Output-contract audit supports structured YAML verdict block AND has negation-aware fallback | **PASS** | See below |
| 6 | Final PASS still requires `--final` mode exit 0 | **PASS** | See below |
| 7 | Gate proof files must be exported (`gate_used/` or `gate_hash.txt`) | **PASS** | See below |

---

## (1) Absolute host paths blocked as package evidence — PASS

`tools/check_gate_package.py:139-151` — containment helper:
```python
def _is_path_in_package(file_path, package_path) -> bool:
    real_file = os.path.realpath(os.path.abspath(str(file_path)))
    real_pkg = os.path.realpath(os.path.abspath(str(package_path)))
    return os.path.commonpath([real_file, real_pkg]) == real_pkg
```

`tools/check_gate_package.py:531-534` — host-path leak detection at declaration time:
```python
if declared_path.is_absolute():
    if not _is_path_in_package(declared_path, package_path):
        host_path_leak = True
```

`tools/check_gate_package.py:742-748` — blocking flag emission:
```python
if raw_ref.host_path_leak and not raw_ref.has_package_relative_copy:
    results.append(CheckResult(
        "exit_code_strict",
        False,
        f"{raw_ref.declared}: ... absolute and resolves outside the package",
        flag="HOST_PATH_NOT_PACKAGE_EVIDENCE",
    ))
```

A declared raw output that is absolute and outside the package is blocking, unless an in-package copy exists (escape valve at lines 547-559).

---

## (2) All profiles require risk_tier + task_kind + rationale — PASS

`tools/check_gate_package.py:204-228` — Gate 5.2-R1 explicitly removes the GATE_LITE exemption:
```python
# Gate 5.2-R1: risk_tier and task_kind are now mandatory for ALL profiles, including
# GATE_LITE. Without them the WRONG_GATE_PROFILE selector cannot mechanically detect
# that a package picked too-weak a profile for its actual task class.
if risk_tier is None:
    results.append(... flag="MISSING_RISK_TIER", ...)
if task_kind is None:
    results.append(... flag="MISSING_TASK_KIND", ...)
```

Mandatory rationale enforcement (`MISSING_PROFILE_REASON` at line 226).

Documentation also updated:
- `GATE_PROFILE_SELECTOR.md:13-15` lists risk_tier, task_kind, reason as required
- `GATE_PROFILE_SELECTOR.md:19` explicitly notes: "Without ... risk_tier and task_kind, the selector cannot detect a too-weak profile choice."
- `GATE_PROFILES.md:20-22` documents allowed values
- `GATE_5_2_USAGE_RULE.md:16` and the merge-readiness checklist at line 132 require all four fields

---

## (3) NOT_APPLICABLE proof files are hard requirements with substantive reason — PASS

`tools/check_gate_package.py:409-441` — `_na_reason_is_substantive()`:
- Strips markdown headings and template tokens
- Requires either a known NA keyword or > 80 chars of substantive prose

`tools/check_gate_package.py:454-492` — `check_not_applicable_files()`:
```python
for state_name in profile_data.get("not_applicable_proof_required", []):
    if not full_path.exists():
        # Gate 5.2-R1: missing NA proof is now blocking, not advisory.
        results.append(... flag="MISSING_NOT_APPLICABLE_PROOF", ...)
        continue
    ...
    if not content.strip():
        results.append(... flag="NOT_APPLICABLE_REASON_MISSING", ...)
        continue
    if not _na_reason_is_substantive(content):
        results.append(... flag="NOT_APPLICABLE_REASON_MISSING", ...)
```

Three blocking branches: missing file, empty file, non-substantive reason.

---

## (4) Dirty-worktree classification approved labels + blocking unclassified — PASS

`tools/check_gate_package.py:933-994` — `final_git_status` check:

Approved labels (lines 936-941):
```python
approved_labels = (
    "ACTIVE_PARALLEL_WORK_DO_NOT_TOUCH",
    "AMBIENT_UNRELATED_DOC_COMMIT",
    "UNRELATED_EXTERNAL_WORK",
    "UNRELATED_EXTERNAL_CHANGE_NEEDS_HUMAN",
)
```

Always-blocking generated/runtime tokens (lines 943-949): `node_modules`, `.run_artifacts`, `raw_test_output`, `raw_outputs`, `doc_freshness_report`.

Path missing from classification → `DIRTY_PATH_NOT_CLASSIFIED` (lines 962-967).
Row without label → `DIRTY_PATH_NOT_CLASSIFIED` (lines 979-984).
`UNKNOWN_REQUIRES_HUMAN` → `UNKNOWN_REQUIRES_HUMAN_BLOCKER` (lines 987-993).

---

## (5) Output contract: structured YAML verdict + negation-aware fallback — PASS

`tools/check_gate_package.py:1088-1106` — `_extract_structured_output_contract_verdict()` parses fenced YAML blocks containing `output_contract_consistency:` mapping with `verdict`, `blocking_findings`, `checked_surfaces`.

`tools/check_gate_package.py:1186-1241` — structured path:
- Unknown verdict → `OUTPUT_CONTRACT_VERDICT_UNKNOWN`
- FAIL/UNCERTAIN → blocking with token-matched flag or `STALE_MILESTONE_LABEL` / `OUTPUT_CONTRACT_VERDICT_UNCERTAIN`
- PASS with non-empty `blocking_findings` → `OUTPUT_CONTRACT_VERDICT_INCONSISTENT`
- PASS with no surfaces → advisory pass

`tools/check_gate_package.py:1243-1256` — fallback prose scan with `_scan_blocking_token_with_negation` for unstructured audits.

`OUTPUT_CONTRACT_CONSISTENCY_AUDIT_TEMPLATE.md` exists at gate root.

---

## (6) `--final` mode required for acceptance — PASS

`tools/check_gate_package.py:1357` — CLI flag definition:
```python
parser.add_argument("--final", action="store_true",
    help="Require final checker report presence; only final mode PASS supports acceptance")
```

`tools/check_gate_package.py:1275-1288` — `check_checker_report_included()`:
```python
if final_mode:
    return [CheckResult(... flag="MISSING_CHECKER_REPORT_FINAL_MODE", ...)]
return [CheckResult(... "skipped in non-final first-run mode")]
```

`final_mode` flows through `check_required_proof_files` (line 334), `write_report_to_package` (line 1318), and `check_checker_report_included` (line 1391).

---

## (7) Gate proof files must be exported — PASS

`tools/check_gate_package.py:496-505` — `check_gate_source_included()`:
```python
def check_gate_source_included(package_path: Path):
    gate_dirs = [p for p in package_path.rglob("gate_used") if p.is_dir()]
    gate_hashes = list(package_path.rglob("gate_hash.txt"))
    if gate_dirs or gate_hashes:
        found = "gate_used/" if gate_dirs else "gate_hash.txt"
        return CheckResult("gate_source_included", True, ...)
    return CheckResult(
        "gate_source_included",
        False,
        "MISSING: neither gate_used/ directory nor gate_hash.txt found",
        ...
    )
```

Either `gate_used/` directory or `gate_hash.txt` is required.

---

## Verdict

7/7 R1 behaviors verified PASS in actual source. Proceed to P02.
