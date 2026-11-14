"""SQLite data-access helpers.

All SQL in the app funnels through this module and app/models.py. SQLite is the
dev engine; the production target is PostgreSQL. Keeping SQL isolated here makes
that swap a localized change rather than a rewrite.

The connection is stored on Flask's `g` so each request gets one connection that
is committed/closed at teardown. For the in-memory test database we keep a single
shared connection for the app's lifetime (a fresh ``:memory:`` connection would
otherwise see an empty schema).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g

# For :memory: we must reuse one connection process-wide, else each open() is a
# brand-new empty database. Keyed by db path so tests stay isolated per app.
_SHARED_MEMORY_CONNS: dict[str, sqlite3.Connection] = {}


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_db() -> sqlite3.Connection:
    db_path = current_app.config["DB_PATH"]
    if db_path == ":memory:":
        key = current_app.config.get("_MEM_KEY", "default")
        conn = _SHARED_MEMORY_CONNS.get(key)
        if conn is None:
            conn = _connect(db_path)
            _SHARED_MEMORY_CONNS[key] = conn
        return conn

    if "db" not in g:
        g.db = _connect(db_path)
    return g.db


def close_db(exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        if exc is None:
            db.commit()
        else:
            db.rollback()
        db.close()


def init_db(app) -> None:
    """Create the schema if it is missing."""
    schema = (Path(app.root_path).parent / "schema.sql").read_text()
    with app.app_context():
        db = get_db()
        db.executescript(schema)
        # Tiny migration: databases created before target_url existed.
        cols = {r["name"] for r in db.execute("PRAGMA table_info(challenges)")}
        if "target_url" not in cols:
            db.execute("ALTER TABLE challenges ADD COLUMN target_url TEXT")
        db.commit()


def reset_memory_db(key: str = "default") -> None:
    """Drop a shared in-memory connection (used between test apps)."""
    conn = _SHARED_MEMORY_CONNS.pop(key, None)
    if conn is not None:
        conn.close()
