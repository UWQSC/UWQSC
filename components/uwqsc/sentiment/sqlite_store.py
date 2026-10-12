"""
ISentimentStore backed by the shared SQLite database from uwqsc.storage.
"""

import sqlite3
from datetime import date
from typing import Any, List, Optional

import pandas as pd

from uwqsc.sentiment.interfaces import SENTIMENT_COLUMNS, ISentimentStore
from uwqsc.storage import connect, register_migration

register_migration("sentiment", 1, """
CREATE TABLE IF NOT EXISTS daily_sentiment (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    emotional REAL NOT NULL,
    logical REAL NOT NULL,
    volume INTEGER NOT NULL,
    PRIMARY KEY (symbol, date, source)
);
""")


class SQLiteSentimentStoreImpl(ISentimentStore):
    """
    Stores scores in "daily_sentiment". Dates are ISO strings.
    """

    def __init__(self, db_path: Optional[str] = None, conn: Optional[sqlite3.Connection] = None):
        """
        :param db_path: String. Database file, or ":memory:". Defaults to storage's path
        :param conn: Existing connection to reuse instead of opening one
        """

        self.conn = conn if conn is not None else connect(db_path)

    def upsert(self, scores: pd.DataFrame) -> int:
        if scores is None or scores.empty:
            return 0

        rows = [
            (
                row.ticker,
                pd.Timestamp(row.date).date().isoformat(),
                row.source,
                float(row.emotional),
                float(row.logical),
                int(row.volume),
            )
            for row in scores.itertuples(index=False)
        ]
        with self.conn:
            self.conn.executemany(
                "INSERT OR REPLACE INTO daily_sentiment "
                "(symbol, date, source, emotional, logical, volume) VALUES (?, ?, ?, ?, ?, ?)",
                rows
            )
        return len(rows)

    def get(self,
            tickers: List[str],
            start: Optional[date] = None,
            end: Optional[date] = None,
            source: Optional[str] = None) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame(columns=SENTIMENT_COLUMNS)

        query = (
            "SELECT symbol AS ticker, date, emotional, logical, volume, source "
            f"FROM daily_sentiment WHERE symbol IN ({','.join('?' * len(tickers))})"
        )
        params: List[Any] = list(tickers)
        if start is not None:
            query += " AND date >= ?"
            params.append(start.isoformat())
        if end is not None:
            query += " AND date <= ?"
            params.append(end.isoformat())
        if source is not None:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY date, symbol"

        scores = pd.read_sql_query(query, self.conn, params=params)
        scores["date"] = pd.to_datetime(scores["date"]).dt.date
        return scores[SENTIMENT_COLUMNS]

    def latest_date(self, ticker: str, source: Optional[str] = None) -> Optional[date]:
        query = "SELECT MAX(date) FROM daily_sentiment WHERE symbol = ?"
        params: List[Any] = [ticker]
        if source is not None:
            query += " AND source = ?"
            params.append(source)
        row = self.conn.execute(query, params).fetchone()
        return date.fromisoformat(row[0]) if row and row[0] else None
