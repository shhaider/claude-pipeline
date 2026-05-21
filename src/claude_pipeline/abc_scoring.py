"""Metric extraction for one variant's worktree + log.

The harness drives each (issue, variant) pair into a worktree. After the
variant finishes, we extract metrics from what it left on disk:

- diff stats vs the base branch
- count of top-level ``def`` lines in changed .py files (proxy for
  "exported functions" — the signal we discovered when issue #9's A variant
  was leaner but missed robustness — fewer exported helpers meant fewer
  separately-testable seams)
- PR URL + number from the raw log
- gate verdict from the run's gate log if present
- failure_categories from heuristic patterns in the log

All functions here are pure: they accept paths and return data structures.
The harness composes them into a RunRow.

Robustness note: every extractor catches its own exceptions and returns a
sentinel (None for ints, empty list for categories). A failed extraction
should not crash the harness — variant C in particular is allowed to leave
a broken worktree, and we still want to record the row.
"""

from __future__ import annotations

import logging
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


# Known failure-category tokens we scan logs for. Order matters: the first
# match wins per regex group. Keep these LOW-FALSE-POSITIVE — the harness
# stores them comma-joined into a single column.
FAILURE_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    (
        "unparseable-llm-output",
        re.compile(
            r"json\.JSONDecodeError|no balanced JSON|failed to parse JSON|"
            r"ClaudeError.*non-JSON|extract_json.*ValueError",
            re.IGNORECASE,
        ),
    ),
    (
        "missing-error-handling",
        re.compile(
            r"UnboundLocalError|AttributeError: 'NoneType'|"
            r"KeyError.*(?:plan|stage|contract|deliverable)",
            re.IGNORECASE,
        ),
    ),
    (
        "gate-blocked",
        re.compile(r"13_BLOCKED_HANDOFF|gate.*BLOCKED|gate verdict.*BLOCKED", re.IGNORECASE),
    ),
    (
        "tests-failed",
        re.compile(r"\d+\s+failed|FAILED \(failures=|tests failed", re.IGNORECASE),
    ),
    (
        "claude-timeout",
        re.compile(r"claude timed out after|claude stream timed out", re.IGNORECASE),
    ),
    (
        "subprocess-timeout",
        re.compile(r"TimeoutExpired|timeout --kill-after", re.IGNORECASE),
    ),
    (
        "no-pr-opened",
        re.compile(r"no PR was opened|pipeline completed but no PR", re.IGNORECASE),
    ),
)


@dataclass
class DiffStats:
    """Result of ``git diff --numstat`` summed across files."""

    additions: int
    deletions: int
    files: int
    changed_paths: list[str]


def diff_stats(worktree: Path, base_ref: str = "origin/main") -> DiffStats:
    """Run ``git diff --numstat`` against the base ref and total up.

    Falls back to ``HEAD~1`` if ``origin/main`` doesn't exist. If both fail,
    returns zeros. (A variant that never even cloned would produce zeros —
    correct.)
    """
    refs_to_try = [base_ref, "main", "HEAD~1"]
    for ref in refs_to_try:
        try:
            proc = subprocess.run(
                ["git", "diff", "--numstat", ref],
                cwd=str(worktree),
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode != 0:
                continue
            adds, dels, files, paths = 0, 0, 0, []
            for line in proc.stdout.splitlines():
                parts = line.split("\t")
                if len(parts) < 3:
                    continue
                a, d, path = parts[0], parts[1], parts[2]
                if a != "-":  # binary files report '-'
                    try:
                        adds += int(a)
                    except ValueError:
                        pass
                if d != "-":
                    try:
                        dels += int(d)
                    except ValueError:
                        pass
                files += 1
                paths.append(path)
            return DiffStats(additions=adds, deletions=dels, files=files, changed_paths=paths)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    return DiffStats(additions=0, deletions=0, files=0, changed_paths=[])


def count_exported_funcs(worktree: Path, changed_paths: list[str]) -> int:
    """Count top-level ``def `` lines in changed .py files.

    "Top-level" = the line starts with ``def `` (no leading whitespace).
    This is a robustness proxy: more top-level functions = more
    separately-testable seams. Issue #9 showed variant A's lean version
    inlined helpers, hiding the malformed-LLM-output handling that B and C
    had as separate functions.

    Only counts .py files. Returns 0 if no .py files were changed (correct).
    """
    count = 0
    for path in changed_paths:
        if not path.endswith(".py"):
            continue
        f = worktree / path
        if not f.exists():
            # File was deleted in the diff — skip.
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            log.warning("count_exported_funcs: could not read %s", f)
            continue
        for line in text.splitlines():
            if line.startswith("def "):
                count += 1
    return count


_PR_URL_RE = re.compile(r"https?://github\.com/[^\s/]+/[^\s/]+/pull/(\d+)")


def extract_pr_url(log_text: str) -> tuple[str | None, int | None]:
    """Scan a variant's combined stdout/stderr for the first PR URL.

    Returns (url, number) or (None, None). Picks the LAST occurrence — the
    variant may have referenced an issue earlier and then opened a PR; we
    want the opened one.
    """
    matches = list(_PR_URL_RE.finditer(log_text))
    if not matches:
        return (None, None)
    last = matches[-1]
    return (last.group(0), int(last.group(1)))


_GATE_VERDICT_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("PASS", re.compile(r"12_PASS_HANDOFF|gate.*verdict.*PASS|PASS_HANDOFF_COMPLETE", re.IGNORECASE)),
    ("FAIL", re.compile(r"gate.*verdict.*FAIL|10_GATE_VERDICT.*FAIL", re.IGNORECASE)),
    ("BLOCKED", re.compile(r"13_BLOCKED_HANDOFF|gate.*verdict.*BLOCKED", re.IGNORECASE)),
)


def extract_gate_verdict(log_text: str) -> str:
    """Extract gate verdict from log text. Returns 'PASS' | 'FAIL' |
    'BLOCKED' | 'UNKNOWN'.

    Search order matters: BLOCKED beats FAIL beats PASS. A run that hit
    BLOCKED late should not score as PASS even if PASS appeared earlier.
    """
    for verdict in ("BLOCKED", "FAIL", "PASS"):
        # find the pattern row that matches this verdict
        for label, pat in _GATE_VERDICT_PATTERNS:
            if label == verdict and pat.search(log_text):
                return verdict
    return "UNKNOWN"


_TEST_LINE_RES: tuple[re.Pattern, ...] = (
    # pytest:   "60 passed in 2.35s" or "1 failed, 59 passed in 2.40s"
    re.compile(r"(?:(\d+)\s+failed,\s+)?(\d+)\s+passed", re.IGNORECASE),
    # jest:     "Tests: 1 failed, 23 passed, 24 total"
    re.compile(r"Tests:.*?(\d+)\s+passed.*?(\d+)\s+total", re.IGNORECASE),
    # unittest: "OK" with "Ran N tests"
    re.compile(r"Ran\s+(\d+)\s+tests?\s+in", re.IGNORECASE),
)


def extract_test_counts(log_text: str) -> tuple[int | None, int | None]:
    """Best-effort parse of (pass_count, total_count) from log output.

    Tries pytest format first, then jest, then unittest. Returns (None,
    None) if nothing matched — better than a wrong number.
    """
    # pytest
    m = _TEST_LINE_RES[0].search(log_text)
    if m:
        failed = int(m.group(1) or 0)
        passed = int(m.group(2) or 0)
        return (passed, passed + failed)
    # jest
    m = _TEST_LINE_RES[1].search(log_text)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    # unittest — assumes all passed if "OK" appeared near the count line
    m = _TEST_LINE_RES[2].search(log_text)
    if m:
        total = int(m.group(1))
        ok_present = bool(re.search(r"\bOK\b", log_text))
        return (total if ok_present else None, total)
    return (None, None)


def detect_failure_categories(log_text: str) -> list[str]:
    """Return a list of failure-category tokens that match the log.

    Order matches FAILURE_PATTERNS declaration order (most-specific to
    most-generic). Deduplicates while preserving order.
    """
    seen: list[str] = []
    for token, pat in FAILURE_PATTERNS:
        if pat.search(log_text) and token not in seen:
            seen.append(token)
    return seen


def score_variant_run(
    worktree: Path,
    log_path: Path | None,
    base_ref: str = "origin/main",
) -> dict:
    """Compose all extractors into one dict that the harness can map onto
    a RunRow's optional fields.

    Returns a dict with keys: pr_url, pr_number, gate_verdict,
    test_pass_count, test_total_count, diff_additions, diff_deletions,
    diff_files, exported_func_count, failure_categories.
    """
    log_text = ""
    if log_path and log_path.exists():
        try:
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            log.warning("score_variant_run: log read failed: %s", e)

    pr_url, pr_number = extract_pr_url(log_text)
    gate_verdict = extract_gate_verdict(log_text)
    test_pass, test_total = extract_test_counts(log_text)
    failure_cats = detect_failure_categories(log_text)

    if worktree.exists() and (worktree / ".git").exists():
        ds = diff_stats(worktree, base_ref=base_ref)
        exp_funcs = count_exported_funcs(worktree, ds.changed_paths)
    else:
        ds = DiffStats(additions=0, deletions=0, files=0, changed_paths=[])
        exp_funcs = 0

    return {
        "pr_url": pr_url,
        "pr_number": pr_number,
        "gate_verdict": gate_verdict,
        "test_pass_count": test_pass,
        "test_total_count": test_total,
        "diff_additions": ds.additions,
        "diff_deletions": ds.deletions,
        "diff_files": ds.files,
        "exported_func_count": exp_funcs,
        "failure_categories": ",".join(failure_cats) if failure_cats else None,
    }
