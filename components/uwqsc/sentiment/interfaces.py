"""
Interfaces for crowd sentiment about a ticker.

Each daily score has two views of the crowd:
- emotional: mood and hype, mostly from social and retail sources, in [-1, 1].
- logical: the reasoned or fundamental tone of news and analysts, in [-1, 1].

"date" is the trading day by whose 16:00 America/New_York close the scored items were
published (see uwqsc.sentiment.bucketing). This keeps backtests free of look-ahead.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from pandas import DataFrame

from uwqsc.common import INTERFACE_NOT_IMPLEMENTED_ERROR

SENTIMENT_COLUMNS = ["ticker", "date", "emotional", "logical", "volume", "source"]


@dataclass(frozen=True)
class SentimentScore:
    """
    Aggregated sentiment for one ticker on one trading day.
    """

    ticker: str
    date: date
    emotional: float
    logical: float
    volume: int
    source: str

    def __post_init__(self):
        for field_name in ("emotional", "logical"):
            value = getattr(self, field_name)
            if not -1.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be in [-1, 1], got {value}")
        if self.volume < 0:
            raise ValueError(f"volume must be >= 0, got {self.volume}")


class ISentimentSource(ABC):
    """
    A provider of daily, close-aligned sentiment scores.
    """

    name: str = "unknown"

    @abstractmethod
    def fetch_daily_sentiment(self, tickers: List[str], start: date, end: date) -> DataFrame:
        """
        :param tickers: Ticker symbols
        :param start: First trading date (inclusive)
        :param end: Last trading date (inclusive)
        :returns: Long DataFrame with SENTIMENT_COLUMNS, one row per (ticker, trading date)
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR


class ISentimentStore(ABC):
    """
    Persistent storage for daily sentiment scores.
    """

    @abstractmethod
    def upsert(self, scores: DataFrame) -> int:
        """
        Insert or replace scores keyed by (ticker, date, source).

        :param scores: Long DataFrame with SENTIMENT_COLUMNS
        :returns: Number of rows written
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get(self,
            tickers: List[str],
            start: Optional[date] = None,
            end: Optional[date] = None,
            source: Optional[str] = None) -> DataFrame:
        """
        :returns: Long DataFrame with SENTIMENT_COLUMNS, sorted by date then ticker
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def latest_date(self, ticker: str, source: Optional[str] = None) -> Optional[date]:
        """
        :returns: Most recent stored date for the ticker (optionally for one source), or None
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR
