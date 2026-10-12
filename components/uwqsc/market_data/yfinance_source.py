"""
IDataSource backed by Yahoo Finance through the yfinance package.
"""

from datetime import date, timedelta
from typing import Any, Dict, List

import pandas as pd

from uwqsc.market_data.interfaces import BAR_COLUMNS, IDataSource

_YF_COLUMNS = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
}


class YFinanceDataSourceImpl(IDataSource):
    """
    Downloads daily bars and metadata from Yahoo Finance. yfinance is imported lazily so that
    importing this module never needs the network or the package.
    """

    name = "yfinance"

    def fetch_daily_bars(self, tickers: List[str], start: date, end: date) -> pd.DataFrame:
        import yfinance as yf  # pylint: disable=import-outside-toplevel

        if not tickers:
            return pd.DataFrame(columns=BAR_COLUMNS)

        # yfinance treats "end" as exclusive.
        raw = yf.download(
            tickers,
            start=start,
            end=end + timedelta(days=1),
            interval="1d",
            auto_adjust=False,
            group_by="ticker",
            progress=False,
            threads=True,
        )
        return self.reshape_download(raw, tickers)

    @staticmethod
    def reshape_download(raw: pd.DataFrame, tickers: List[str]) -> pd.DataFrame:
        """
        Turn yfinance's wide (ticker, field) column layout into long BAR_COLUMNS rows.

        :param raw: DataFrame returned by yf.download(..., group_by="ticker")
        :param tickers: Tickers that were requested
        :returns: Long DataFrame with BAR_COLUMNS
        """

        if raw is None or raw.empty:
            return pd.DataFrame(columns=BAR_COLUMNS)

        frames = []
        for ticker in tickers:
            if isinstance(raw.columns, pd.MultiIndex):
                if ticker not in raw.columns.get_level_values(0):
                    continue
                part = raw[ticker]
            else:
                part = raw

            part = part.rename(columns=_YF_COLUMNS)
            part = part[[c for c in _YF_COLUMNS.values() if c in part.columns]]
            part = part.dropna(how="all")
            if part.empty:
                continue

            part = part.reset_index()
            part = part.rename(columns={part.columns[0]: "date"})
            part["date"] = pd.to_datetime(part["date"]).dt.date
            part["ticker"] = ticker
            frames.append(part.reindex(columns=BAR_COLUMNS))

        if not frames:
            return pd.DataFrame(columns=BAR_COLUMNS)

        return pd.concat(frames, ignore_index=True)

    def fetch_ticker_info(self, ticker: str) -> Dict[str, Any]:
        import yfinance as yf  # pylint: disable=import-outside-toplevel

        info = yf.Ticker(ticker).info or {}
        return {
            "name": info.get("longName") or info.get("shortName"),
            "exchange": info.get("exchange"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency"),
        }
