"""SQLite access and schema for the closed-test QA companion.

WRITTEN TO FILL A GAP, 2026-09-20
---------------------------------
`routes.py` and `core.py` were committed; this module and the package
`__init__` were not, so `app.py` could not import `create_app` and the
application had never started. Nothing here was invented freely: every table
and column below is taken from the SQL that `routes.py` already executes, and
the two UNIQUE constraints are required by code that is already written --

    sessions   ON a duplicate the route flashes "A session is already
               recorded for that date; one evidence row per day is allowed",
               which only ever fires if UNIQUE(tester_id, session_date) exists.
    feedback   the insert uses ON CONFLICT(tester_id, checkpoint) DO UPDATE,
               which is a syntax error at runtime without a matching unique
               index. Feedback is therefore upserted, not duplicated, so a
               tester revising their day-4 note replaces it.

Row factory is sqlite3.Row because every consumer subscripts by name
(`tester['start_date']`) and `export_json` calls `dict(row)`.
"""
from __future__ import annotations

import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS testers (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name     TEXT    NOT NULL,
    google_account   TEXT    NOT NULL,
    country          TEXT    NOT NULL,
    device_model     TEXT    NOT NULL,
    android_version  TEXT    NOT NULL,
    start_date       TEXT    NOT NULL,
    consent_at       TEXT,
    -- Recorded at enrolment, editable afterwards from the status form.
    -- compute_metrics() treats opted_in as a precondition of completeness,
    -- so it defaults to 1: consent_at is written in the same INSERT.
    opted_in         INTEGER NOT NULL DEFAULT 1,
    active           INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    tester_id        INTEGER NOT NULL REFERENCES testers(id) ON DELETE CASCADE,
    session_date     TEXT    NOT NULL,
    duration_minutes INTEGER NOT NULL,
    features_used    TEXT    NOT NULL,
    notes            TEXT    NOT NULL DEFAULT '',
    UNIQUE (tester_id, session_date)
);

CREATE TABLE IF NOT EXISTS issues (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tester_id    INTEGER NOT NULL REFERENCES testers(id) ON DELETE CASCADE,
    reported_on  TEXT    NOT NULL,
    severity     TEXT    NOT NULL,
    title        TEXT    NOT NULL,
    steps        TEXT    NOT NULL,
    expected     TEXT    NOT NULL,
    actual       TEXT    NOT NULL,
    reproducible TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tester_id    INTEGER NOT NULL REFERENCES testers(id) ON DELETE CASCADE,
    checkpoint   TEXT    NOT NULL,
    submitted_on TEXT    NOT NULL,
    summary      TEXT    NOT NULL,
    confusing    TEXT    NOT NULL DEFAULT '',
    bugs         TEXT    NOT NULL DEFAULT '',
    UNIQUE (tester_id, checkpoint)
);

CREATE INDEX IF NOT EXISTS ix_sessions_tester ON sessions (tester_id);
CREATE INDEX IF NOT EXISTS ix_issues_tester   ON issues   (tester_id);
CREATE INDEX IF NOT EXISTS ix_feedback_tester ON feedback (tester_id);
"""


def get_db() -> sqlite3.Connection:
    """The request-scoped connection, opened on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        # Off by default in SQLite, and the schema declares cascades that are
        # silently ignored without it.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app) -> None:
    """Create any missing tables. Safe to call on every start.

    Every statement is CREATE ... IF NOT EXISTS, so this neither drops data
    nor fails on an existing database. It runs at application start rather
    than behind a CLI command because this app is launched by a systemd unit
    that runs no migration step.
    """
    with sqlite3.connect(app.config["DATABASE"]) as conn:
        conn.executescript(SCHEMA)


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
