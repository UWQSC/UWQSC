"""
Owns the single SQLite database shared by the data bricks: its location, connections and
per-brick schema migrations.
"""

from uwqsc.storage.config import DEFAULT_DB_PATH
from uwqsc.storage.connection import connect
from uwqsc.storage.migrations import (
    apply_migrations,
    register_migration,
    registered_migrations,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "apply_migrations",
    "connect",
    "register_migration",
    "registered_migrations",
]
