"""Tests for the ABC harness SQLite schema and DAO.

These tests are hermetic: each one uses ``tmp_path`` for the DB file so
concurrent test runs cannot collide. The schema is meant to be idempotent
so we verify ``init_db`` runs twice without error.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from claude_pipeline.abc_db import (
    RunRow,
    fetch_all_rounds,
    fetch_runs,
    init_db,
    insert_run,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Path to a fresh DB file. init_db will create the parent dir."""
    return tmp_path / "runs" / "abc-scores.db"


def _example_row(round_name: str = "round-1", variant: str = "A", issue: int = 100) -> RunRow:
    """Realistic RunRow for tests. Tweak via kwargs."""
    return RunRow(
        round=round_name,
        ts="2026-05-21T12:00:00Z",
        repo="shhaider/claude-pipeline",
        issue_number=issue,
        tier=2,
        variant=variant,
        pr_url=f"https://github.com/shhaider/claude-pipeline/pull/{issue+500}",
        pr_number=issue + 500,
        cost_usd=0.42,
        duration_s=180.0,
        gate_verdict="PASS",
        test_pass_count=60,
        test_total_count=60,
        diff_additions=42,
        diff_deletions=10,
        diff_files=3,
        exported_func_count=7,
        failure_categories=None,
        raw_log_path="/tmp/run.log",
    )


# --------------------------------------------------------------------------- #
# init_db
# --------------------------------------------------------------------------- #


def test_init_db_creates_table(db_path: Path) -> None:
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='runs'"
        )
        assert cur.fetchone() is not None
    finally:
        conn.close()


def test_init_db_is_idempotent(db_path: Path) -> None:
    """Calling init_db twice must not error or destroy data."""
    init_db(db_path)
    insert_run(db_path, _example_row())
    init_db(db_path)  # should not drop the row
    assert len(fetch_runs(db_path, "round-1")) == 1


def test_init_db_creates_parent_dir(tmp_path: Path) -> None:
    """init_db must mkdir the parent if missing."""
    nested = tmp_path / "deeply" / "nested" / "path" / "abc.db"
    init_db(nested)
    assert nested.exists()


def test_runs_has_expected_columns(db_path: Path) -> None:
    """Schema must include every column the harness writes."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute("PRAGMA table_info(runs)")
        cols = {r[1] for r in cur.fetchall()}
    finally:
        conn.close()
    required = {
        "run_id", "round", "ts", "repo", "issue_number", "tier", "variant",
        "pr_url", "pr_number", "cost_usd", "duration_s", "gate_verdict",
        "test_pass_count", "test_total_count", "diff_additions",
        "diff_deletions", "diff_files", "exported_func_count",
        "failure_categories", "raw_log_path",
    }
    assert required <= cols, f"missing: {required - cols}"


# --------------------------------------------------------------------------- #
# insert_run
# --------------------------------------------------------------------------- #


def test_insert_run_returns_id(db_path: Path) -> None:
    init_db(db_path)
    rid = insert_run(db_path, _example_row())
    assert rid >= 1


def test_insert_run_assigns_increasing_ids(db_path: Path) -> None:
    """run_id is AUTOINCREMENT so each insert gets a higher id."""
    init_db(db_path)
    ids = [
        insert_run(db_path, _example_row(variant=v))
        for v in ("A", "B", "C")
    ]
    assert ids == sorted(ids) and len(set(ids)) == 3


def test_insert_run_round_trips_all_fields(db_path: Path) -> None:
    """Every field on the row survives a round trip."""
    init_db(db_path)
    row = _example_row()
    rid = insert_run(db_path, row)
    fetched = fetch_runs(db_path, "round-1")
    assert len(fetched) == 1
    r = fetched[0]
    assert r["run_id"] == rid
    assert r["round"] == row.round
    assert r["ts"] == row.ts
    assert r["repo"] == row.repo
    assert r["issue_number"] == row.issue_number
    assert r["tier"] == row.tier
    assert r["variant"] == row.variant
    assert r["pr_url"] == row.pr_url
    assert r["pr_number"] == row.pr_number
    assert r["cost_usd"] == pytest.approx(row.cost_usd)
    assert r["duration_s"] == pytest.approx(row.duration_s)
    assert r["gate_verdict"] == row.gate_verdict
    assert r["test_pass_count"] == row.test_pass_count
    assert r["test_total_count"] == row.test_total_count
    assert r["diff_additions"] == row.diff_additions
    assert r["diff_deletions"] == row.diff_deletions
    assert r["diff_files"] == row.diff_files
    assert r["exported_func_count"] == row.exported_func_count
    assert r["failure_categories"] is None
    assert r["raw_log_path"] == row.raw_log_path


def test_insert_run_handles_optional_nulls(db_path: Path) -> None:
    """A variant that crashed before scoring should still insert."""
    init_db(db_path)
    crashed = RunRow(
        round="round-1",
        ts="2026-05-21T12:00:00Z",
        repo="shhaider/claude-pipeline",
        issue_number=99,
        tier=1,
        variant="A",
        # All optional fields default to None
    )
    rid = insert_run(db_path, crashed)
    fetched = fetch_runs(db_path, "round-1")
    assert fetched[0]["run_id"] == rid
    assert fetched[0]["pr_url"] is None
    assert fetched[0]["gate_verdict"] is None
    assert fetched[0]["cost_usd"] is None


# --------------------------------------------------------------------------- #
# fetch_runs / fetch_all_rounds
# --------------------------------------------------------------------------- #


def test_fetch_runs_filters_by_round(db_path: Path) -> None:
    init_db(db_path)
    insert_run(db_path, _example_row(round_name="round-1", variant="A"))
    insert_run(db_path, _example_row(round_name="round-2", variant="A"))
    insert_run(db_path, _example_row(round_name="round-1", variant="B"))

    r1 = fetch_runs(db_path, "round-1")
    r2 = fetch_runs(db_path, "round-2")
    assert len(r1) == 2
    assert len(r2) == 1
    assert {r["variant"] for r in r1} == {"A", "B"}


def test_fetch_runs_returns_insertion_order(db_path: Path) -> None:
    """Rows for one round come back in insertion order (run_id ASC)."""
    init_db(db_path)
    for v in ("A", "B", "C"):
        insert_run(db_path, _example_row(variant=v))
    fetched = fetch_runs(db_path, "round-1")
    assert [r["variant"] for r in fetched] == ["A", "B", "C"]


def test_fetch_runs_unknown_round_returns_empty(db_path: Path) -> None:
    init_db(db_path)
    insert_run(db_path, _example_row())
    assert fetch_runs(db_path, "does-not-exist") == []


def test_fetch_all_rounds_unique_and_ordered(db_path: Path) -> None:
    init_db(db_path)
    insert_run(db_path, _example_row(round_name="round-1"))
    insert_run(db_path, _example_row(round_name="round-2"))
    insert_run(db_path, _example_row(round_name="round-1", variant="B"))
    assert fetch_all_rounds(db_path) == ["round-1", "round-2"]
