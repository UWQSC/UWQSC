"""
Testing the SQLite market data store and the incremental sync service
"""

import unittest
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from uwqsc.market_data import (
    BAR_COLUMNS,
    MarketDataService,
    SQLiteMarketDataStoreImpl,
    YFinanceDataSourceImpl,
)
from uwqsc_test_fakes import FakeDataSource, business_days


def _bars(ticker, prices):
    return pd.DataFrame(
        [(ticker, d, p, p, p, p, p, 10) for d, p in prices.items()], columns=BAR_COLUMNS
    )


class SQLiteMarketDataStoreTest(unittest.TestCase):
    """
    This class is used to test storing and reading bars and metadata
    """

    def setUp(self):
        self.store = SQLiteMarketDataStoreImpl(":memory:")

    def test_upsert_is_idempotent(self):
        """
        Testing that writing the same bars twice keeps one row per date and updates values
        """

        self.store.upsert_daily_bars(_bars("AAPL", {date(2024, 1, 2): 1.0}), "t")
        self.store.upsert_daily_bars(_bars("AAPL", {date(2024, 1, 2): 2.0}), "t")

        bars = self.store.get_daily_bars(["AAPL"])
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars.iloc[0]["adj_close"], 2.0)

    def test_date_filters_and_latest_date(self):
        """
        Testing start/end filtering and latest_date
        """

        days = business_days(date(2024, 1, 1), date(2024, 1, 31))
        self.store.upsert_daily_bars(_bars("AAPL", {d: 1.0 for d in days}), "t")

        bars = self.store.get_daily_bars(["AAPL"], date(2024, 1, 10), date(2024, 1, 12))
        self.assertEqual(list(bars["date"]),
                         [date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12)])
        self.assertEqual(self.store.latest_date("AAPL"), date(2024, 1, 31))
        self.assertIsNone(self.store.latest_date("MSFT"))

    def test_ticker_info_roundtrip(self):
        """
        Testing that metadata is stored with an update time and tickers are listed
        """

        self.store.upsert_ticker_info("AAPL", {"name": "Apple", "currency": "USD"})
        info = self.store.get_ticker_info("AAPL")

        self.assertEqual(info["name"], "Apple")
        self.assertIsNone(info["sector"])
        self.assertIsNotNone(info["updated_at"])
        self.assertEqual(self.store.list_tickers(), ["AAPL"])


class MarketDataServiceTest(unittest.TestCase):
    """
    This class is used to test incremental syncing and the wide layout
    """

    def setUp(self):
        days = business_days(date(2024, 1, 1), date(2024, 3, 29))
        self.source = FakeDataSource({
            "AAPL": {d: 100.0 + i for i, d in enumerate(days)},
            "MSFT": {d: 200.0 + i for i, d in enumerate(days)},
        })
        self.store = SQLiteMarketDataStoreImpl(":memory:")
        self.service = MarketDataService(self.source, self.store)

    def test_second_sync_fetches_only_new_dates(self):
        """
        Testing that a re-sync starts the day after the latest stored bar
        """

        self.service.sync(["AAPL", "MSFT"], date(2024, 1, 1), date(2024, 1, 31))
        self.service.sync(["AAPL", "MSFT"], date(2024, 1, 1), date(2024, 2, 29))

        self.assertEqual(self.source.bar_calls[-1],
                         (("AAPL", "MSFT"), date(2024, 2, 1), date(2024, 2, 29)))
        self.assertEqual(len(self.store.get_daily_bars(["AAPL"])), 23 + 21)

    def test_up_to_date_tickers_are_skipped(self):
        """
        Testing that nothing is fetched when every ticker already covers the range
        """

        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 31))
        calls = len(self.source.bar_calls)
        written = self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual(len(self.source.bar_calls), calls)
        self.assertEqual(written, {"AAPL": 0})

    def test_tickers_grouped_by_fetch_start(self):
        """
        Testing that a new ticker is fetched from "start" while an old one resumes
        """

        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 31))
        plan = self.service.plan_sync(["AAPL", "MSFT"], date(2024, 1, 1), date(2024, 2, 9))

        self.assertEqual(plan, {date(2024, 2, 1): ["AAPL"], date(2024, 1, 1): ["MSFT"]})

    def test_ticker_info_refreshed_only_when_stale(self):
        """
        Testing that metadata is fetched once, then again only after it ages out
        """

        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 5))
        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 5))
        self.assertEqual(self.source.info_calls, ["AAPL"])

        stale = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        self.store.conn.execute("UPDATE tickers SET updated_at = ?", (stale,))
        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 5))
        self.assertEqual(self.source.info_calls, ["AAPL", "AAPL"])

    def test_ticker_info_failure_keeps_bars(self):
        """
        Testing that a failing metadata lookup is logged and the bars are still stored
        """

        def broken(ticker):
            raise ConnectionError(f"no route for {ticker}")

        self.source.fetch_ticker_info = broken
        with self.assertLogs("uwqsc.market_data.service", level="WARNING"):
            written = self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 5))

        self.assertEqual(written, {"AAPL": 5})
        self.assertIsNone(self.store.get_ticker_info("AAPL"))

    def test_weekend_only_window_is_skipped(self):
        """
        Testing that a re-sync whose only missing days are a weekend fetches nothing
        """

        self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 5))
        calls = len(self.source.bar_calls)

        written = self.service.sync(["AAPL"], date(2024, 1, 1), date(2024, 1, 7),
                                    refresh_info=False)

        self.assertEqual(written, {"AAPL": 0})
        self.assertEqual(len(self.source.bar_calls), calls)

    def test_empty_download_is_logged(self):
        """
        Testing that a fetch returning no bars (e.g. a failed download) logs a warning
        """

        with self.assertLogs("uwqsc.market_data.service", level="WARNING") as logs:
            written = self.service.sync(["NOPE"], date(2024, 1, 1), date(2024, 1, 5),
                                        refresh_info=False)

        self.assertEqual(written, {"NOPE": 0})
        self.assertIn("returned no bars for NOPE", logs.output[0])

    def test_load_wide_columns(self):
        """
        Testing the {ticker}_price / {ticker}_volume layout algorithms expect
        """

        self.service.sync(["AAPL", "MSFT"], date(2024, 1, 1), date(2024, 1, 5))
        wide = self.service.load_wide(["AAPL", "MSFT"])

        self.assertEqual(list(wide.columns),
                         ["AAPL_price", "AAPL_volume", "MSFT_price", "MSFT_volume"])
        self.assertEqual(len(wide), 5)
        self.assertEqual(wide.index.name, "Date")
        self.assertEqual(wide["MSFT_price"].iloc[0], 200.0)


class YFinanceReshapeTest(unittest.TestCase):
    """
    This class is used to test reshaping yfinance output without the network
    """

    def test_reshape_multiindex(self):
        """
        Testing that the (ticker, field) layout becomes long BAR_COLUMNS rows
        """

        index = pd.DatetimeIndex(["2024-01-02", "2024-01-03"], name="Date")
        fields = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        columns = pd.MultiIndex.from_product([["AAPL", "MSFT"], fields])
        raw = pd.DataFrame(1.0, index=index, columns=columns)
        raw[("MSFT", "Adj Close")] = [None, 5.0]
        raw.loc[index[0], "MSFT"] = None

        long = YFinanceDataSourceImpl.reshape_download(raw, ["AAPL", "MSFT"])

        self.assertEqual(list(long.columns), BAR_COLUMNS)
        self.assertEqual(len(long), 3)
        self.assertEqual(long[long["ticker"] == "MSFT"]["date"].tolist(), [date(2024, 1, 3)])


if __name__ == "__main__":
    unittest.main()
