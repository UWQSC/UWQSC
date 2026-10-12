"""
Interfaces for fetching and storing daily market data. Implementations can be swapped for
fakes in tests or other providers later.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional

from pandas import DataFrame

from uwqsc.common import INTERFACE_NOT_IMPLEMENTED_ERROR

BAR_COLUMNS = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]
TICKER_INFO_FIELDS = ["name", "exchange", "sector", "industry", "currency"]


class IDataSource(ABC):
    """
    A provider of daily bars and ticker metadata.
    """

    @abstractmethod
    def fetch_daily_bars(self, tickers: List[str], start: date, end: date) -> DataFrame:
        """
        Fetch daily OHLCV bars.

        :param tickers: List of ticker symbols
        :param start: First date to fetch (inclusive)
        :param end: Last date to fetch (inclusive)
        :returns: Long DataFrame with BAR_COLUMNS; "date" holds datetime.date values
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def fetch_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch descriptive metadata for a ticker.

        :param ticker: Ticker symbol
        :returns: Dictionary with TICKER_INFO_FIELDS keys (values may be None)
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR


class IMarketDataStore(ABC):
    """
    Persistent storage for daily bars and ticker metadata.
    """

    @abstractmethod
    def upsert_daily_bars(self, bars: DataFrame, source: str) -> int:
        """
        Insert or replace bars keyed by (ticker, date).

        :param bars: Long DataFrame with BAR_COLUMNS
        :param source: Name of the provider the bars came from
        :returns: Number of rows written
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_daily_bars(self,
                       tickers: List[str],
                       start: Optional[date] = None,
                       end: Optional[date] = None) -> DataFrame:
        """
        :returns: Long DataFrame with BAR_COLUMNS, sorted by date then ticker
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def latest_date(self, ticker: str) -> Optional[date]:
        """
        :returns: Most recent stored bar date for the ticker, or None if it has no bars
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def upsert_ticker_info(self, ticker: str, info: Dict[str, Any]) -> None:
        """
        Insert or replace metadata for a ticker, stamping the update time.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def get_ticker_info(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        :returns: Stored metadata plus "updated_at" (ISO string), or None
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def list_tickers(self) -> List[str]:
        """
        :returns: Every ticker that has bars or metadata stored
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR
