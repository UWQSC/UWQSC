"""
Wires an IDataSource to an IMarketDataStore: incremental syncing and loading in the
column layout algorithms expect.
"""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd

from uwqsc.market_data.interfaces import IDataSource, IMarketDataStore

TICKER_INFO_MAX_AGE = timedelta(days=7)

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Keeps the store up to date from the source and serves wide per-ticker frames.
    """

    def __init__(self, source: IDataSource, store: IMarketDataStore):
        self.source = source
        self.store = store

    def plan_sync(self, tickers: List[str], start: date, end: date) -> Dict[date, List[str]]:
        """
        Work out what an incremental sync must fetch. Tickers already stored up to "end" are
        skipped; the rest start the day after their latest stored bar (or at "start").

        :returns: fetch start date mapped to the tickers that share it
        """

        groups: Dict[date, List[str]] = defaultdict(list)
        for ticker in tickers:
            latest = self.store.latest_date(ticker)
            fetch_start = start if latest is None else max(start, latest + timedelta(days=1))
            if fetch_start <= end:
                groups[fetch_start].append(ticker)
        return dict(groups)

    def sync(self,
             tickers: List[str],
             start: date,
             end: Optional[date] = None,
             refresh_info: bool = True) -> Dict[str, int]:
        """
        Fetch only bars that are missing after each ticker's latest stored date, then store them.

        :param tickers: Ticker symbols
        :param start: Earliest date wanted
        :param end: Last date wanted (inclusive). Defaults to today
        :param refresh_info: Also refresh ticker metadata older than TICKER_INFO_MAX_AGE
        :returns: Number of bars written per ticker
        """

        end = end or date.today()
        written = {ticker: 0 for ticker in tickers}
        source_name = getattr(self.source, "name", type(self.source).__name__)

        for fetch_start, group in sorted(self.plan_sync(tickers, start, end).items()):
            bars = self.source.fetch_daily_bars(group, fetch_start, end)
            if bars.empty:
                continue
            self.store.upsert_daily_bars(bars, source_name)
            for ticker, count in bars.groupby("ticker").size().items():
                written[ticker] = int(count)

        if refresh_info:
            for ticker in tickers:
                if not self._info_is_stale(ticker):
                    continue
                # Metadata is best-effort: a failed lookup must not undo a successful bar sync.
                try:
                    info = self.source.fetch_ticker_info(ticker)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logger.warning("Could not refresh info for %s: %s", ticker, exc)
                    continue
                self.store.upsert_ticker_info(ticker, info)

        return written

    def _info_is_stale(self, ticker: str) -> bool:
        info = self.store.get_ticker_info(ticker)
        if info is None or not info.get("updated_at"):
            return True
        updated = datetime.fromisoformat(info["updated_at"])
        return datetime.now(timezone.utc) - updated > TICKER_INFO_MAX_AGE

    def load_wide(self,
                  tickers: List[str],
                  start: Optional[date] = None,
                  end: Optional[date] = None,
                  price_field: str = "adj_close") -> pd.DataFrame:
        """
        Load stored bars as one row per date with "{ticker}_price" and "{ticker}_volume" columns.

        :param price_field: Bar column used for "{ticker}_price"
        :returns: DataFrame indexed by "Date" (pandas Timestamps)
        """

        bars = self.store.get_daily_bars(tickers, start, end)
        columns = [f"{t}_{kind}" for t in tickers for kind in ("price", "volume")]
        if bars.empty:
            return pd.DataFrame(columns=columns, dtype=float,
                                index=pd.DatetimeIndex([], name="Date"))

        bars = bars.assign(date=pd.to_datetime(bars["date"]))
        wide = bars.pivot(index="date", columns="ticker", values=[price_field, "volume"])
        result = pd.DataFrame(index=wide.index)
        for ticker in tickers:
            for kind, field in (("price", price_field), ("volume", "volume")):
                key = (field, ticker)
                result[f"{ticker}_{kind}"] = (
                    wide[key].astype(float) if key in wide.columns else float("nan")
                )
        result.index.name = "Date"
        return result.sort_index()
