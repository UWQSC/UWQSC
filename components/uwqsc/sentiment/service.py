"""
Wires an ISentimentSource to an ISentimentStore: incremental syncing and loading in the
column layout algorithms expect.
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from uwqsc.sentiment.interfaces import ISentimentSource, ISentimentStore

SENTIMENT_FIELDS = ("emotional", "logical", "volume")


class SentimentService:
    """
    Keeps stored sentiment up to date and serves wide per-ticker frames.
    """

    def __init__(self, source: ISentimentSource, store: ISentimentStore):
        self.source = source
        self.store = store

    def plan_sync(self, tickers: List[str], start: date, end: date) -> Dict[date, List[str]]:
        """
        Same incremental rule as market data: fetch from the day after the latest stored date
        for this source, and skip tickers that are already up to date.

        :returns: fetch start date mapped to the tickers that share it
        """

        groups: Dict[date, List[str]] = defaultdict(list)
        for ticker in tickers:
            latest = self.store.latest_date(ticker, self.source.name)
            fetch_start = start if latest is None else max(start, latest + timedelta(days=1))
            if fetch_start <= end:
                groups[fetch_start].append(ticker)
        return dict(groups)

    def sync(self, tickers: List[str], start: date, end: Optional[date] = None) -> Dict[str, int]:
        """
        Fetch and store only missing days.

        :returns: Number of rows written per ticker
        """

        end = end or date.today()
        written = {ticker: 0 for ticker in tickers}

        for fetch_start, group in sorted(self.plan_sync(tickers, start, end).items()):
            scores = self.source.fetch_daily_sentiment(group, fetch_start, end)
            if scores.empty:
                continue
            self.store.upsert(scores)
            for ticker, count in scores.groupby("ticker").size().items():
                written[ticker] = int(count)

        return written

    def load_wide(self,
                  tickers: List[str],
                  start: Optional[date] = None,
                  end: Optional[date] = None,
                  source: Optional[str] = None) -> pd.DataFrame:
        """
        Load stored sentiment as one row per date with "{ticker}_sent_emotional",
        "{ticker}_sent_logical" and "{ticker}_sent_volume" columns. When several sources cover
        the same day, scores are volume-weighted and volumes summed.

        :returns: DataFrame indexed by "Date" (pandas Timestamps)
        """

        scores = self.store.get(tickers, start, end, source)
        columns = [f"{t}_sent_{f}" for t in tickers for f in SENTIMENT_FIELDS]
        if scores.empty:
            return pd.DataFrame(columns=columns, dtype=float,
                                index=pd.DatetimeIndex([], name="Date"))

        scores = scores.assign(date=pd.to_datetime(scores["date"]))
        weight = scores["volume"].clip(lower=1)
        scores = scores.assign(
            emotional_w=scores["emotional"] * weight,
            logical_w=scores["logical"] * weight,
            weight=weight,
        )
        daily = scores.groupby(["date", "ticker"]).agg(
            emotional_w=("emotional_w", "sum"),
            logical_w=("logical_w", "sum"),
            weight=("weight", "sum"),
            volume=("volume", "sum"),
        )
        daily["emotional"] = daily["emotional_w"] / daily["weight"]
        daily["logical"] = daily["logical_w"] / daily["weight"]

        wide = daily[list(SENTIMENT_FIELDS)].unstack("ticker")
        result = pd.DataFrame(index=wide.index)
        for ticker in tickers:
            for field in SENTIMENT_FIELDS:
                key = (field, ticker)
                result[f"{ticker}_sent_{field}"] = (
                    wide[key].astype(float) if key in wide.columns else float("nan")
                )
        result.index.name = "Date"
        return result.sort_index()
