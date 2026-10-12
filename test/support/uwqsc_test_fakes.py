"""
Fakes shared by tests. No network.
"""

from datetime import date
from typing import Dict, List

import pandas as pd

from uwqsc.market_data import BAR_COLUMNS, IDataSource


class FakeDataSource(IDataSource):
    """
    Serves bars from a price table and records every fetch.
    """

    name = "fake"

    def __init__(self, prices: Dict[str, Dict[date, float]]):
        """
        :param prices: ticker -> {date: price}
        """

        self.prices = prices
        self.bar_calls: List[tuple] = []
        self.info_calls: List[str] = []

    def fetch_daily_bars(self, tickers, start, end):
        self.bar_calls.append((tuple(tickers), start, end))
        rows = []
        for ticker in tickers:
            for day, price in sorted(self.prices.get(ticker, {}).items()):
                if start <= day <= end:
                    rows.append((ticker, day, price, price, price, price, price, 100))
        return pd.DataFrame(rows, columns=BAR_COLUMNS)

    def fetch_ticker_info(self, ticker):
        self.info_calls.append(ticker)
        return {"name": f"{ticker} Inc", "exchange": "TEST", "sector": None,
                "industry": None, "currency": "USD"}


def business_days(start: date, end: date) -> List[date]:
    """
    :returns: Weekdays from start to end inclusive
    """

    return [d.date() for d in pd.bdate_range(start, end)]
