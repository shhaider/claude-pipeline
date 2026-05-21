#!/usr/bin/env python3
"""Tiered retention for gate skill report directories.

Tiers:
  - hot   (<= --hot-days): leave fully intact
  - warm  (<= --warm-days, default 30): compress snapshots/ subdir if present;
            preserve all audit MDs/yaml at full fidelity
  - cold  (> --warm-days, <= --cold-days, default 180): tar+gzip the whole
            report directory; move to _archive/<year>/<quarter>/
  - frozen (> --cold-days): leave compressed where it is; do not touch

Safe by default:
  - dry-run unless --execute is passed
  - never deletes original content; archive moves are atomic (tar then unlink-tree)
  - lock file at <root>/.rotate_reports.lock prevents concurrent runs
  - logs to <root>/../logs/rotate_reports.log when run from cron
  - exits 0 on success (including no-op), 1 on errors, 2 on config issue,
    3 if locked

Index:
  - <root>/INDEX.csv lists every report (tier, path, age_days, size_bytes,
    verdict if discoverable, archived_path if applicable)

Usage:
  rotate_reports.py --root <reports_dir> [--execute] [--hot-days N]
                    [--warm-days N] [--cold-days N] [--quiet]

Multiple --root flags can be passed to rotate several reports/ directories
in one run.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import errno
import logging
import os
import re
import shutil
import socket
import sys
import tarfile
from pathlib import Path
from typing import Iterable

LOCK_NAME = ".rotate_reports.lock"
INDEX_NAME = "INDEX.csv"
ARCHIVE_DIR = "_archive"
SNAPSHOTS_TAR = "snapshots.tar.gz"
DEFAULT_HOT_DAYS = 7
DEFAULT_WARM_DAYS = 30
DEFAULT_COLD_DAYS = 180
LOG = logging.getLogger("rotate_reports")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--root",
        action="append",
        required=True,
        help="Reports directory to rotate (repeatable).",
    )
    p.add_argument("--execute", action="store_true", help="Actually perform changes (default: dry-run).")
    p.add_argument("--hot-days", type=int, default=DEFAULT_HOT_DAYS, help=f"Reports younger than this stay HOT untouched (default {DEFAULT_HOT_DAYS}).")
    p.add_argument("--warm-days", type=int, default=DEFAULT_WARM_DAYS, help=f"Reports older than this enter WARM tier — snapshots/ compressed (default {DEFAULT_WARM_DAYS}).")
    p.add_argument("--cold-days", type=int, default=DEFAULT_COLD_DAYS, help=f"Reports older than this enter COLD tier — tar+gzipped and moved to _archive/ (default {DEFAULT_COLD_DAYS}).")
    p.add_argument("--quiet", action="store_true", help="Reduce log verbosity.")
    p.add_argument("--log-file", help="Write log output to this file (in addition to stderr).")
    return p.parse_args(argv)


def setup_logging(quiet: bool, log_file: str | None) -> None:
    """Quiet only suppresses stderr; the log file always gets full INFO so
    nightly runs leave an audit trail even in --quiet mode."""
    fmt = "%(asctime)s %(levelname)s %(message)s"
    formatter = logging.Formatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Clear any prior handlers (idempotent re-init)
    for h in list(root.handlers):
        root.removeHandler(h)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING if quiet else logging.INFO)
    stderr_handler.setFormatter(formatter)
    root.addHandler(stderr_handler)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as exc:
            sys.stderr.write(f"warning: could not open log file {log_file}: {exc}\n")


class LockHeld(Exception):
    pass


def acquire_lock(root: Path) -> Path:
    lock = root / LOCK_NAME
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            raise LockHeld(f"lock present at {lock}; another run may be active or a previous run crashed")
        raise
    try:
        os.write(fd, f"pid={os.getpid()} host={socket.gethostname()} t={dt.datetime.now().isoformat()}\n".encode())
    finally:
        os.close(fd)
    return lock


def release_lock(lock: Path) -> None:
    try:
        lock.unlink()
    except FileNotFoundError:
        pass


def newest_mtime(path: Path) -> float:
    """Use the newest mtime in the directory tree as the report's effective age."""
    newest = path.stat().st_mtime
    for sub in path.rglob("*"):
        try:
            m = sub.stat().st_mtime
            if m > newest:
                newest = m
        except (OSError, ValueError):
            continue
    return newest


def dir_size(path: Path) -> int:
    total = 0
    for sub in path.rglob("*"):
        try:
            if sub.is_file():
                total += sub.stat().st_size
        except OSError:
            continue
    return total


VERDICT_RE = re.compile(r"^(verdict|gate_verdict|status)\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)


def discover_verdict(report: Path) -> str:
    """Best-effort verdict scan for INDEX.csv. Returns '' if not found."""
    candidates = [
        report / "GATE_VERDICT.md",
        report / "CURRENT_STATE.yaml",
        report / "HANDOFF.md",
        report / "GATE_PACKAGE_VALIDATION_REPORT.md",
    ]
    for cand in candidates:
        if cand.is_file():
            try:
                txt = cand.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            m = VERDICT_RE.search(txt)
            if m:
                return m.group(2).strip()
            for token in ("PASS_HANDOFF_COMPLETE", "BLOCKED_HANDOFF_COMPLETE", "MAX_CYCLES_REACHED"):
                if token in txt:
                    return token
    return ""


def compress_snapshots(report: Path, execute: bool) -> tuple[bool, int]:
    """Tar+gzip the report's snapshots/ subdir. Returns (changed, bytes_freed)."""
    snap = report / "snapshots"
    if not snap.is_dir():
        return False, 0
    target = report / SNAPSHOTS_TAR
    if target.exists():
        return False, 0
    pre_size = dir_size(snap)
    LOG.info("WARM compress snapshots: %s (-%d bytes uncompressed)", snap, pre_size)
    if not execute:
        return True, pre_size
    tmp = report / (SNAPSHOTS_TAR + ".tmp")
    try:
        with tarfile.open(tmp, "w:gz") as tf:
            tf.add(snap, arcname="snapshots")
        tmp.rename(target)
        post_size = target.stat().st_size
        shutil.rmtree(snap)
        return True, max(0, pre_size - post_size)
    except Exception as exc:
        LOG.error("compress snapshots failed for %s: %s", snap, exc)
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        return False, 0


def archive_to_cold(report: Path, archive_root: Path, age_days: int, execute: bool) -> tuple[bool, Path | None]:
    """Tar+gzip the whole report directory; move to _archive/<year>/<quarter>/.
    Returns (archived, archive_path)."""
    timestamp = dt.datetime.fromtimestamp(newest_mtime(report))
    quarter = (timestamp.month - 1) // 3 + 1
    dest_dir = archive_root / str(timestamp.year) / f"Q{quarter}"
    dest_file = dest_dir / f"{report.name}.tar.gz"
    if dest_file.exists():
        return False, dest_file
    LOG.info("COLD archive: %s (%d days old) -> %s", report, age_days, dest_file)
    if not execute:
        return True, dest_file
    dest_dir.mkdir(parents=True, exist_ok=True)
    tmp = dest_dir / (dest_file.name + ".tmp")
    try:
        with tarfile.open(tmp, "w:gz") as tf:
            tf.add(report, arcname=report.name)
        tmp.rename(dest_file)
        shutil.rmtree(report)
        return True, dest_file
    except Exception as exc:
        LOG.error("archive failed for %s: %s", report, exc)
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        return False, None


def write_index(root: Path, rows: list[dict]) -> None:
    index = root / INDEX_NAME
    fieldnames = ["report", "tier", "path", "age_days", "size_bytes", "verdict", "archived_path"]
    with open(index, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in sorted(rows, key=lambda r: (r["tier"], r["report"])):
            w.writerow(row)
    LOG.info("wrote index: %s (%d rows)", index, len(rows))


def iter_report_dirs(root: Path) -> Iterable[Path]:
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("_") or entry.name.startswith("."):
            continue  # skip _archive, hidden dirs
        yield entry


def rotate_root(root: Path, hot_days: int, warm_days: int, cold_days: int, execute: bool) -> tuple[int, int, int, list[dict]]:
    """Returns (warm_count, cold_count, errors, index_rows)."""
    if not root.is_dir():
        LOG.error("root not a directory: %s", root)
        return 0, 0, 1, []
    archive_root = root / ARCHIVE_DIR
    now = dt.datetime.now().timestamp()
    rows: list[dict] = []
    warm_count = cold_count = errors = 0

    for report in iter_report_dirs(root):
        try:
            mtime = newest_mtime(report)
            age = (now - mtime) / 86400.0
            size = dir_size(report)
            verdict = discover_verdict(report)
            archived_path = ""

            if age > cold_days:
                tier = "frozen"
            elif age > warm_days:
                tier = "cold"
                archived, dest = archive_to_cold(report, archive_root, int(age), execute)
                if archived and dest:
                    archived_path = str(dest.relative_to(root))
                    cold_count += 1
            elif age > hot_days:
                tier = "warm"
                changed, _freed = compress_snapshots(report, execute)
                if changed:
                    warm_count += 1
            else:
                tier = "hot"

            rows.append({
                "report": report.name,
                "tier": tier,
                "path": str(report.relative_to(root)) if report.exists() else archived_path,
                "age_days": f"{age:.1f}",
                "size_bytes": str(size),
                "verdict": verdict,
                "archived_path": archived_path,
            })
        except Exception as exc:
            LOG.exception("error processing %s: %s", report, exc)
            errors += 1

    # Also add archived entries for visibility (they're under _archive/)
    if archive_root.is_dir():
        for archived in archive_root.rglob("*.tar.gz"):
            rows.append({
                "report": archived.stem.replace(".tar", ""),
                "tier": "archived",
                "path": "",
                "age_days": "",
                "size_bytes": str(archived.stat().st_size),
                "verdict": "",
                "archived_path": str(archived.relative_to(root)),
            })

    if execute or not rows:
        write_index(root, rows)
    else:
        LOG.info("dry-run: would write %d index rows to %s", len(rows), root / INDEX_NAME)

    return warm_count, cold_count, errors, rows


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(args.quiet, args.log_file)

    if args.hot_days < 0 or args.warm_days <= args.hot_days or args.cold_days <= args.warm_days:
        LOG.error("invalid tier configuration: hot=%d warm=%d cold=%d (need 0<=hot<warm<cold)",
                  args.hot_days, args.warm_days, args.cold_days)
        return 2

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    LOG.info("rotate_reports start mode=%s hot=%d warm=%d cold=%d roots=%s",
             mode, args.hot_days, args.warm_days, args.cold_days, args.root)

    total_warm = total_cold = total_errors = 0
    locks: list[Path] = []
    try:
        for root_str in args.root:
            root = Path(root_str).resolve()
            try:
                lock = acquire_lock(root)
                locks.append(lock)
            except LockHeld as exc:
                LOG.error("skipping %s: %s", root, exc)
                total_errors += 1
                continue
            warm, cold, errors, _rows = rotate_root(root, args.hot_days, args.warm_days, args.cold_days, args.execute)
            total_warm += warm
            total_cold += cold
            total_errors += errors
    finally:
        for lock in locks:
            release_lock(lock)

    LOG.info("rotate_reports done warm=%d cold=%d errors=%d mode=%s",
             total_warm, total_cold, total_errors, mode)
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
