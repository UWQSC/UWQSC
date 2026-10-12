"""
Testing portfolio accounting, snapshot building, backtests and sweeps
"""

import unittest
from datetime import date

import pandas as pd

import uwqsc.algorithms  # pylint: disable=unused-import
from uwqsc.algorithm_core import IAlgorithm, IPreProcessData, StockPosition, create_algorithm
from uwqsc.backtesting import Portfolio, SnapshotBuilder, StoreBackedBacktest, sweep
from uwqsc.market_data import MarketDataService, SQLiteMarketDataStoreImpl
from uwqsc.sentiment import SENTIMENT_COLUMNS, SentimentService, SQLiteSentimentStoreImpl
from uwqsc.sentiment import NullSentimentSource
from uwqsc.storage import connect
from uwqsc_test_fakes import FakeDataSource, business_days


class PortfolioTest(unittest.TestCase):
    """
    This class is used to test cash/shares accounting
    """

    def test_buy_moves_cash_into_shares(self):
        """
        Testing that buying keeps equity unchanged at the same price
        """

        portfolio = Portfolio(1000)
        portfolio.apply({"AAPL": 100.0}, {"AAPL": 10.0})

        self.assertEqual(portfolio.cash, 900.0)
        self.assertEqual(portfolio.shares["AAPL"], 10.0)
        self.assertEqual(portfolio.equity({"AAPL": 10.0}), 1000.0)

    def test_price_moves_change_equity(self):
        """
        Testing that held shares are marked to market, and shorts lose when price rises
        """

        portfolio = Portfolio(1000)
        portfolio.apply({"AAPL": 100.0, "MSFT": -50.0}, {"AAPL": 10.0, "MSFT": 5.0})

        self.assertEqual(portfolio.equity({"AAPL": 12.0, "MSFT": 6.0}), 1000 + 20 - 10)

    def test_metrics_and_drawdown(self):
        """
        Testing total return and max drawdown from a hand-built 3-day series
        """

        portfolio = Portfolio(1000)
        portfolio.apply({"AAPL": 1000.0}, {"AAPL": 10.0})
        portfolio.mark("2024-01-02", {"AAPL": 10.0})
        portfolio.mark("2024-01-03", {"AAPL": 12.0})
        portfolio.mark("2024-01-04", {"AAPL": 9.0})

        metrics = portfolio.metrics()
        self.assertEqual(metrics["final_equity"], 900.0)
        self.assertAlmostEqual(metrics["total_return"], -0.1)
        self.assertAlmostEqual(metrics["max_drawdown"], 900 / 1200 - 1)
        self.assertEqual(metrics["trade_count"], 1)

    def test_missing_price_uses_last_seen(self):
        """
        Testing that NaN prices neither trade nor zero out holdings
        """

        portfolio = Portfolio(100)
        portfolio.apply({"AAPL": 50.0}, {"AAPL": 5.0})
        portfolio.mark("2024-01-02", {"AAPL": 5.0})
        portfolio.apply({"AAPL": 10.0}, {"AAPL": float("nan")})

        self.assertEqual(portfolio.mark("2024-01-03", {"AAPL": float("nan")}), 100.0)


class _AlwaysLong(IAlgorithm):
    class _Pass(IPreProcessData):
        def missing_values(self):
            pass

        def remove_duplicate_timestamps(self):
            pass

        def remove_outliers(self):
            pass

    REQUIRED_FEATURES = frozenset({"price", "sentiment"})

    def __init__(self, tickers, parameters=None):
        super().__init__("Always Long", tickers, self._Pass(), parameters)
        self.seen_columns = None

    def generate_signals(self, current_data):
        self.seen_columns = list(current_data.columns)
        self.__positions__ = {t: StockPosition.LONG for t in self.tickers}

    def calculate_position_size(self, ticker, price, portfolio_value):
        if self.__trade_count__ >= len(self.tickers):
            return 0.0
        return 0.5 * portfolio_value / price


class BacktestingTest(unittest.TestCase):
    """
    This class is used to test snapshot building, backtests and sweeps on fake data
    """

    def setUp(self):
        days = business_days(date(2024, 1, 1), date(2024, 3, 29))
        prices = {
            "AAPL": {d: 100.0 + i for i, d in enumerate(days)},
            "MSFT": {d: 200.0 - i * 0.5 for i, d in enumerate(days) if i >= 2},
        }
        conn = connect(":memory:")
        self.market = MarketDataService(FakeDataSource(prices),
                                        SQLiteMarketDataStoreImpl(conn=conn))
        self.market.sync(["AAPL", "MSFT"], date(2024, 1, 1), date(2024, 3, 29), refresh_info=False)
        self.sentiment_store = SQLiteSentimentStoreImpl(conn=conn)
        self.sentiment = SentimentService(NullSentimentSource(), self.sentiment_store)
        self.builder = SnapshotBuilder(self.market, self.sentiment)

    def test_price_only_build(self):
        """
        Testing that price-only builds skip sentiment and start once every ticker has traded
        """

        frame = self.builder.build(["AAPL", "MSFT"])

        self.assertFalse(any("_sent_" in c for c in frame.columns))
        self.assertEqual(frame.index[0], pd.Timestamp("2024-01-03"))

    def test_sentiment_joined_and_filled(self):
        """
        Testing that sentiment is joined on date and gaps become zero
        """

        self.sentiment_store.upsert(pd.DataFrame(
            [("AAPL", date(2024, 1, 4), 0.8, -0.2, 7, "x")], columns=SENTIMENT_COLUMNS
        ))
        frame = self.builder.build(["AAPL", "MSFT"], features={"sentiment"})

        self.assertEqual(frame.loc["2024-01-04", "AAPL_sent_emotional"], 0.8)
        self.assertEqual(frame.loc["2024-01-05", "AAPL_sent_emotional"], 0.0)
        self.assertEqual(frame.loc["2024-01-04", "MSFT_sent_volume"], 0.0)

    def test_feature_validation(self):
        """
        Testing unknown features and missing sentiment service are rejected
        """

        with self.assertRaises(ValueError):
            self.builder.build(["AAPL"], features={"fundamentals"})
        with self.assertRaises(ValueError):
            SnapshotBuilder(self.market).build(["AAPL"], features={"sentiment"})

    def test_iter_snapshots_one_row_each(self):
        """
        Testing that snapshots are single-row frames in date order
        """

        snapshots = list(self.builder.iter_snapshots(["AAPL"], date(2024, 1, 2), date(2024, 1, 5)))

        self.assertEqual(len(snapshots), 4)
        self.assertTrue(all(len(s) == 1 for s in snapshots))

    def test_backtest_builds_declared_features(self):
        """
        Testing that the backtest gives the algorithm the features it declares
        """

        algorithm = _AlwaysLong(["AAPL"])
        backtest = StoreBackedBacktest(algorithm, self.builder, 1000, date(2024, 1, 2))
        metrics = backtest.run()

        self.assertIn("AAPL_sent_emotional", algorithm.seen_columns)
        self.assertEqual(metrics["trade_count"], 1)
        # Half the capital bought AAPL at 101 on 2024-01-02; AAPL rises 1/day.
        last_price = 100.0 + 64
        self.assertAlmostEqual(metrics["final_equity"], 500 + 500 / 101 * last_price)

    def test_sma_backtest_runs(self):
        """
        Testing that the registered SMA runs end to end on stored data
        """

        algorithm = create_algorithm("sma", ["AAPL", "MSFT"],
                                     {"short_window": 3, "long_window": 10})
        metrics = StoreBackedBacktest(algorithm, self.builder, 10_000).run()

        self.assertEqual(set(metrics),
                         {"final_equity", "total_return", "max_drawdown", "trade_count"})
        self.assertLessEqual(metrics["max_drawdown"], 0)

    def test_sweep_ranks_runs(self):
        """
        Testing that sweep returns one row per run, best first, with failures last
        """

        results = sweep(self.builder, ["AAPL", "MSFT"], None, None, 10_000, {
            "sma": [{"short_window": 3, "long_window": 10}, {"short_window": 5, "long_window": 20}],
            "hmm": [{}],
        })

        self.assertEqual(len(results), 3)
        ok = results[results["error"].isna()]
        self.assertEqual(list(ok["algorithm"]), ["sma", "sma"])
        self.assertEqual(list(ok["final_equity"]), sorted(ok["final_equity"], reverse=True))
        # The committed HMM is a WIP stub that cannot run on snapshots yet.
        self.assertEqual(results.iloc[-1]["algorithm"], "hmm")
        self.assertIsNotNone(results.iloc[-1]["error"])


if __name__ == "__main__":
    unittest.main()
