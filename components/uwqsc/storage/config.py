"""
Location of the shared SQLite database.
"""

import os

DEFAULT_DB_PATH: str = os.environ.get(
    "UWQSC_DB_PATH",
    os.path.join(os.path.expanduser("~"), ".uwqsc", "uwqsc.sqlite")
)
