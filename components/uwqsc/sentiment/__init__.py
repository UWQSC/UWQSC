"""
Crowd sentiment per ticker (emotional and logical views), aligned to market closes.
Only a neutral placeholder source exists today; real feeds implement ISentimentSource.
"""

from uwqsc.sentiment.bucketing import as_of_trading_date, is_trading_day, next_trading_day
from uwqsc.sentiment.interfaces import (
    SENTIMENT_COLUMNS,
    ISentimentSource,
    ISentimentStore,
    SentimentScore,
)
from uwqsc.sentiment.null_source import NullSentimentSource
from uwqsc.sentiment.service import SentimentService
from uwqsc.sentiment.sqlite_store import SQLiteSentimentStoreImpl

__all__ = [
    "SENTIMENT_COLUMNS",
    "ISentimentSource",
    "ISentimentStore",
    "NullSentimentSource",
    "SQLiteSentimentStoreImpl",
    "SentimentScore",
    "SentimentService",
    "as_of_trading_date",
    "is_trading_day",
    "next_trading_day",
]
