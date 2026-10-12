"""
Versioned schema migrations. Each brick registers its own DDL under its own owner name, so
storage never needs to know which tables exist.
"""

import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Tuple

_MIGRATIONS: Dict[Tuple[str, int], str] = {}

_BOOKKEEPING = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    owner TEXT NOT NULL,
    version INTEGER NOT NULL,
    applied_at TEXT NOT NULL,
    PRIMARY KEY (owner, version)
)
"""


def register_migration(owner: str, version: int, sql: str) -> None:
    """
    Register a schema migration. Registering the same (owner, version) with identical SQL is a
    no-op, so modules can be re-imported safely.

    :param owner: String. Brick that owns the tables, e.g. "market_data"
    :param version: Integer. Increasing version per owner, starting at 1
    :param sql: String. One or more SQL statements
    """

    key = (owner, version)
    if key in _MIGRATIONS and _MIGRATIONS[key] != sql:
        raise ValueError(f"Migration {owner} v{version} is already registered with other SQL")
    _MIGRATIONS[key] = sql


def registered_migrations() -> List[Tuple[str, int]]:
    """
    :returns: Registered (owner, version) pairs in apply order
    """

    return sorted(_MIGRATIONS)


def apply_migrations(conn: sqlite3.Connection) -> List[Tuple[str, int]]:
    """
    Apply every registered migration that this database has not seen yet.

    :param conn: Open SQLite connection
    :returns: The (owner, version) pairs applied by this call
    """

    conn.execute(_BOOKKEEPING)
    done = set(conn.execute("SELECT owner, version FROM schema_migrations").fetchall())
    applied = []

    for owner, version in sorted(_MIGRATIONS):
        if (owner, version) in done:
            continue
        with conn:
            conn.executescript(_MIGRATIONS[(owner, version)])
            conn.execute(
                "INSERT INTO schema_migrations (owner, version, applied_at) VALUES (?, ?, ?)",
                (owner, version, datetime.now(timezone.utc).isoformat())
            )
        applied.append((owner, version))

    return applied
