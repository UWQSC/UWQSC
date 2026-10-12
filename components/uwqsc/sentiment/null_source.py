"""
Placeholder sentiment source that reports a neutral crowd. Used until a real feed and model
exist, and in tests.
"""

from datetime import date, timedelta
from typing import List

import pandas as pd

from uwqsc.sentiment.bucketing import is_trading_day
from uwqsc.sentiment.interfaces import SENTIMENT_COLUMNS, ISentimentSource


class NullSentimentSource(ISentimentSource):
    """
    Returns emotional = logical = 0 with volume 0 for every ticker and trading day.
    """

    name = "null"

    def fetch_daily_sentiment(self, tickers: List[str], start: date, end: date) -> pd.DataFrame:
        rows = []
        day = start
        while day <= end:
            if is_trading_day(day):
                rows.extend((ticker, day, 0.0, 0.0, 0, self.name) for ticker in tickers)
            day += timedelta(days=1)
        return pd.DataFrame(rows, columns=SENTIMENT_COLUMNS)
