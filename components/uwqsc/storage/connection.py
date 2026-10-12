"""
Opens connections to the shared SQLite database.
"""

import os
import sqlite3
from typing import Optional

from uwqsc.storage.config import DEFAULT_DB_PATH
from uwqsc.storage.migrations import apply_migrations


def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Open the database, creating its directory if needed, and apply pending migrations.

    :param db_path: String. File path, or ":memory:". Defaults to DEFAULT_DB_PATH
    :returns: Open SQLite connection
    """

    db_path = db_path or DEFAULT_DB_PATH

    if db_path != ":memory:":
        directory = os.path.dirname(os.path.abspath(db_path))
        os.makedirs(directory, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    if db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")

    apply_migrations(conn)
    return conn
