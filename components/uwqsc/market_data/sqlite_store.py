"""
IMarketDataStore backed by the shared SQLite database from uwqsc.storage.
"""

import sqlite3
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from uwqsc.market_data.interfaces import BAR_COLUMNS, TICKER_INFO_FIELDS, IMarketDataStore
from uwqsc.storage import connect, register_migration

register_migration("market_data", 1, """
CREATE TABLE IF NOT EXISTS tickers (
    symbol TEXT PRIMARY KEY,
    name TEXT,
    exchange TEXT,
    sector TEXT,
    industry TEXT,
    currency TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS daily_bars (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    source TEXT,
    PRIMARY KEY (symbol, date)
);
""")


class SQLiteMarketDataStoreImpl(IMarketDataStore):
    """
    Stores bars in "daily_bars" and metadata in "tickers". Dates are ISO strings.
    """

    def __init__(self, db_path: Optional[str] = None, conn: Optional[sqlite3.Connection] = None):
        """
        :param db_path: String. Database file, or ":memory:". Defaults to storage's path
        :param conn: Existing connection to reuse instead of opening one
        """

        self.conn = conn if conn is not None else connect(db_path)

    def upsert_daily_bars(self, bars: pd.DataFrame, source: str) -> int:
        if bars is None or bars.empty:
            return 0

        rows = [
            (
                row.ticker,
                _to_date(row.date).isoformat(),
                _none_if_nan(row.open),
                _none_if_nan(row.high),
                _none_if_nan(row.low),
                _none_if_nan(row.close),
                _none_if_nan(row.adj_close),
                None if _none_if_nan(row.volume) is None else int(row.volume),
                source,
            )
            for row in bars.itertuples(index=False)
        ]
        with self.conn:
            self.conn.executemany(
                "INSERT OR REPLACE INTO daily_bars "
                "(symbol, date, open, high, low, close, adj_close, volume, source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows
            )
        return len(rows)

    def get_daily_bars(self,
                       tickers: List[str],
                       start: Optional[date] = None,
                       end: Optional[date] = None) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame(columns=BAR_COLUMNS)

        query = (
            "SELECT symbol AS ticker, date, open, high, low, close, adj_close, volume "
            f"FROM daily_bars WHERE symbol IN ({','.join('?' * len(tickers))})"
        )
        params: List[Any] = list(tickers)
        if start is not None:
            query += " AND date >= ?"
            params.append(_to_date(start).isoformat())
        if end is not None:
            query += " AND date <= ?"
            params.append(_to_date(end).isoformat())
        query += " ORDER BY date, symbol"

        bars = pd.read_sql_query(query, self.conn, params=params)
        bars["date"] = pd.to_datetime(bars["date"]).dt.date
        return bars[BAR_COLUMNS]

    def latest_date(self, ticker: str) -> Optional[date]:
        row = self.conn.execute(
            "SELECT MAX(date) FROM daily_bars WHERE symbol = ?", (ticker,)
        ).fetchone()
        return date.fromisoformat(row[0]) if row and row[0] else None

    def upsert_ticker_info(self, ticker: str, info: Dict[str, Any]) -> None:
        values = [info.get(field) for field in TICKER_INFO_FIELDS]
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO tickers "
                "(symbol, name, exchange, sector, industry, currency, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [ticker, *values, datetime.now(timezone.utc).isoformat()]
            )

    def get_ticker_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT name, exchange, sector, industry, currency, updated_at "
            "FROM tickers WHERE symbol = ?", (ticker,)
        ).fetchone()
        if row is None:
            return None
        return dict(zip([*TICKER_INFO_FIELDS, "updated_at"], row))

    def list_tickers(self) -> List[str]:
        rows = self.conn.execute(
            "SELECT symbol FROM tickers UNION SELECT DISTINCT symbol FROM daily_bars ORDER BY 1"
        ).fetchall()
        return [r[0] for r in rows]


def _to_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def _none_if_nan(value: Any) -> Any:
    return None if value is None or pd.isna(value) else float(value)
