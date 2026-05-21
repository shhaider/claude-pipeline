"""SQLite schema + DAO for the ABC harness.

One table: ``runs``. Each (round, issue_number, variant) tuple produces one
row, capturing PR URL, cost, duration, gate verdict, test counts, diff stats,
exported-function count, failure categories, and a path to the raw log.

The harness writes rows immediately on completion of each variant — partial
rounds are valid (e.g. variant A crashed; B and C still have rows).

The schema is created on demand by ``init_db``. Schema changes are additive
only: append columns at the end of the CREATE TABLE statement. Don't reorder
or rename — downstream scorecards rely on column names.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterator

log = logging.getLogger(__name__)


SCHEMA_SQL: str = """
CREATE TABLE IF NOT EXISTS runs (
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,
  round TEXT NOT NULL,
  ts TEXT NOT NULL,
  repo TEXT NOT NULL,
  issue_number INTEGER NOT NULL,
  tier INTEGER NOT NULL,
  variant TEXT NOT NULL,
  pr_url TEXT,
  pr_number INTEGER,
  cost_usd REAL,
  duration_s REAL,
  gate_verdict TEXT,
  test_pass_count INTEGER,
  test_total_count INTEGER,
  diff_additions INTEGER,
  diff_deletions INTEGER,
  diff_files INTEGER,
  exported_func_count INTEGER,
  failure_categories TEXT,
  raw_log_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_runs_round ON runs(round);
CREATE INDEX IF NOT EXISTS idx_runs_round_variant ON runs(round, variant);
CREATE INDEX IF NOT EXISTS idx_runs_round_tier ON runs(round, tier);
"""


# Columns in the order they appear in the schema.  Used by ``insert_run`` to
# build the INSERT statement and by ``fetch_runs`` consumers to know what
# they're getting back.
_RUN_COLS: tuple[str, ...] = (
    "round",
    "ts",
    "repo",
    "issue_number",
    "tier",
    "variant",
    "pr_url",
    "pr_number",
    "cost_usd",
    "duration_s",
    "gate_verdict",
    "test_pass_count",
    "test_total_count",
    "diff_additions",
    "diff_deletions",
    "diff_files",
    "exported_func_count",
    "failure_categories",
    "raw_log_path",
)


@dataclass
class RunRow:
    """One persisted ABC run.

    Mirrors the ``runs`` table 1:1 except ``run_id`` which the DB assigns.
    All optional metric fields default to ``None`` so a partial run (e.g.
    variant crashed before tests) still produces a valid row.
    """

    round: str
    ts: str
    repo: str
    issue_number: int
    tier: int
    variant: str
    pr_url: str | None = None
    pr_number: int | None = None
    cost_usd: float | None = None
    duration_s: float | None = None
    gate_verdict: str | None = None
    test_pass_count: int | None = None
    test_total_count: int | None = None
    diff_additions: int | None = None
    diff_deletions: int | None = None
    diff_files: int | None = None
    exported_func_count: int | None = None
    failure_categories: str | None = None
    raw_log_path: str | None = None
    run_id: int | None = field(default=None)  # set by DB on INSERT

    def to_db_tuple(self) -> tuple:
        """Tuple in column-order for the INSERT statement."""
        d = asdict(self)
        return tuple(d[c] for c in _RUN_COLS)


@contextmanager
def connect(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    """Context-managed sqlite connection. Caller is responsible for commit.

    Path's parent dir is created if missing — the harness writes into a runs/
    subtree that may not exist yet.
    """
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path | str) -> None:
    """Create the schema if it doesn't exist. Idempotent."""
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        log.info("abc_db: initialized at %s", db_path)


def insert_run(db_path: Path | str, row: RunRow) -> int:
    """Insert one run row. Returns the assigned ``run_id``."""
    placeholders = ",".join("?" for _ in _RUN_COLS)
    cols = ",".join(_RUN_COLS)
    sql = f"INSERT INTO runs ({cols}) VALUES ({placeholders})"
    with connect(db_path) as conn:
        cur = conn.execute(sql, row.to_db_tuple())
        conn.commit()
        rid = int(cur.lastrowid)
        row.run_id = rid
        log.info(
            "abc_db: inserted run_id=%d round=%s issue=%d variant=%s gate=%s",
            rid,
            row.round,
            row.issue_number,
            row.variant,
            row.gate_verdict,
        )
        return rid


def fetch_runs(db_path: Path | str, round_name: str) -> list[dict]:
    """Return all rows for one round as plain dicts (in insertion order)."""
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT * FROM runs WHERE round = ? ORDER BY run_id ASC",
            (round_name,),
        )
        return [dict(r) for r in cur.fetchall()]


def fetch_all_rounds(db_path: Path | str) -> list[str]:
    """Distinct round names in the DB, in insertion order."""
    with connect(db_path) as conn:
        cur = conn.execute(
            "SELECT round, MIN(run_id) AS first_id FROM runs "
            "GROUP BY round ORDER BY first_id ASC"
        )
        return [r["round"] for r in cur.fetchall()]
