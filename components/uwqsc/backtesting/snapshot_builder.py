"""
Assembles the per-date frames algorithms trade on from market data and, when asked,
sentiment.
"""

from datetime import date
from typing import FrozenSet, Iterable, Iterator, List, Optional

import pandas as pd

from uwqsc.market_data import MarketDataService
from uwqsc.sentiment import SentimentService

KNOWN_FEATURES: FrozenSet[str] = frozenset({"price", "sentiment"})


class SnapshotBuilder:
    """
    Joins stored data into one row per trading date. Sentiment rows are already aligned to
    the close they were known by, so they are joined on date with no shift.
    """

    def __init__(self, market: MarketDataService, sentiment: Optional[SentimentService] = None):
        self.market = market
        self.sentiment = sentiment

    def build(self,
              tickers: List[str],
              start: Optional[date] = None,
              end: Optional[date] = None,
              features: Iterable[str] = frozenset({"price"})) -> pd.DataFrame:
        """
        :param features: Feature names from IAlgorithm.REQUIRED_FEATURES
        :returns: DataFrame indexed by "Date" with "{t}_price", "{t}_volume" and, if requested,
                  "{t}_sent_emotional", "{t}_sent_logical", "{t}_sent_volume"
        """

        features = frozenset(features) | {"price"}
        unknown = features - KNOWN_FEATURES
        if unknown:
            raise ValueError(f"Unknown features {sorted(unknown)}; known: {sorted(KNOWN_FEATURES)}")
        if "sentiment" in features and self.sentiment is None:
            raise ValueError("Algorithm requires sentiment but no SentimentService was given")

        frame = self.market.load_wide(tickers, start, end)
        price_cols = [f"{t}_price" for t in tickers]
        # Carry a ticker's last price over days it has no bar (backward-looking only), then
        # drop leading dates before every ticker has traded.
        frame[price_cols] = frame[price_cols].ffill()
        frame = frame.dropna(subset=price_cols)

        if "sentiment" in features:
            sentiment = self.sentiment.load_wide(tickers, start, end)
            frame = frame.join(sentiment, how="left")
            for ticker in tickers:
                for field in ("emotional", "logical", "volume"):
                    column = f"{ticker}_sent_{field}"
                    if column not in frame:
                        frame[column] = 0.0
                    frame[column] = frame[column].fillna(0.0)

        return frame

    def iter_snapshots(self,
                       tickers: List[str],
                       start: Optional[date] = None,
                       end: Optional[date] = None,
                       features: Iterable[str] = frozenset({"price"})) -> Iterator[pd.DataFrame]:
        """
        :returns: Generator of 1-row DataFrames, one per date, matching what execute_trade gets
        """

        frame = self.build(tickers, start, end, features)
        for i in range(len(frame)):
            yield frame.iloc[[i]]
