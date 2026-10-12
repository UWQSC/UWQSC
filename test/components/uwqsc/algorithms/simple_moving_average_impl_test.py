"""
Testing the Simple Moving Average Algorithm
"""

import datetime as dt
import unittest

import numpy as np
import pandas as pd

from uwqsc_algorithmic_trading.interfaces.algorithms.algorithm_interface import StockPosition
from uwqsc_algorithmic_trading.src.algorithms.simple_moving_average_impl import (
    SimpleMovingAverageImpl
)


class SimpleMovingAverageImplTest(unittest.TestCase):
    """
    This class is used to test each component of Simple Moving Average Algorithm
    """

    def setUp(self):
        self.tickers = ["AAPL", "GOOGL"]
        self.parameters = {"position_size": 0.1}
        self.algorithm = SimpleMovingAverageImpl(self.tickers, self.parameters)
        self.algorithm.__positions__ = {ticker: StockPosition.HOLD for ticker in self.tickers}
        self.algorithm.__trade_count__ = 0

    def test_generate_signals_with_not_executing(self):
        """
        Testing that the signals are generated correctly when the algorithm was not executing
        """

        data = pd.DataFrame({
            "AAPL_short": [100, 105],
            "AAPL_long": [102, 103],
            "GOOGL_short": [1500, 1495],
            "GOOGL_long": [1498, 1497]
        })

        self.algorithm.executing = False
        self.algorithm.generate_signals(data)
        self.assertTrue(isinstance(self.algorithm.__positions__["AAPL"], StockPosition))
        self.assertTrue(isinstance(self.algorithm.__positions__["GOOGL"], StockPosition))

    def test_generate_signals_with_already_executing(self):
        """
        Testing that the signals are generated correctly when the algorithm was already executing
        """

        previous_data = pd.DataFrame({
            "AAPL_short": [100],
            "AAPL_long": [102],
            "GOOGL_short": [1500],
            "GOOGL_long": [1498]
        })
        self.algorithm.generate_signals(previous_data)

        current_data = pd.DataFrame({
            "AAPL_short": [105],
            "AAPL_long": [103],
            "GOOGL_short": [1495],
            "GOOGL_long": [1497]
        })
        self.algorithm.generate_signals(current_data)

        self.assertEqual(self.algorithm.__positions__["AAPL"], StockPosition.LONG)
        self.assertEqual(self.algorithm.__positions__["GOOGL"], StockPosition.SHORT)

    def test_calculate_position_size_with_hold(self):
        """
        Testing that the position size is calculated correctly.
        It should return 0 on hold
        """

        price = 100
        portfolio_value = 10000
        ticker = "AAPL"

        self.algorithm.__positions__[ticker] = StockPosition.HOLD
        position_size = self.algorithm.calculate_position_size(ticker, price, portfolio_value)
        self.assertEqual(position_size, 0)

    def test_calculate_position_size_with_short(self):
        """
        Testing that the position size is calculated correctly.
        It should return a -ve value on short
        """

        price = 100
        portfolio_value = 10000
        ticker = "AAPL"

        self.algorithm.__positions__[ticker] = StockPosition.SHORT
        position_size = self.algorithm.calculate_position_size(ticker, price, portfolio_value)
        expected_size = -1 * (self.parameters["position_size"] * portfolio_value) / price
        self.assertEqual(position_size, expected_size)

    def test_calculate_position_size_with_long(self):
        """
        Testing that the position size is calculated correctly.
        It should return a +ve value on short
        """

        price = 100
        portfolio_value = 10000
        ticker = "AAPL"

        self.algorithm.__positions__[ticker] = StockPosition.LONG
        position_size = self.algorithm.calculate_position_size(ticker, price, portfolio_value)
        expected_size = (self.parameters["position_size"] * portfolio_value) / price
        self.assertEqual(position_size, expected_size)

    def test_execute_trade_without_past_history(self):
        """
        Testing that the algorithm can execute trades without any previous data
        """

        capital = 10000
        index = pd.date_range(start='2023-01-01', periods=1, freq='D')
        current_data = pd.DataFrame(index=index, data={
            "AAPL_price": np.random.uniform(100, 200, size=1),
            "GOOGL_price": np.random.uniform(1500, 2000, size=1)
        })
        portfolio = self.algorithm.execute_trade(capital, current_data)

        self.assertTrue(ticker in portfolio for ticker in self.tickers)
        self.assertTrue(isinstance(portfolio[ticker], int) for ticker in self.tickers)

    def test_execute_trade_with_past_history(self):
        """
        Testing that the algorithm can execute trades with previous data
        """

        capital = 10000
        past_index = pd.date_range(start='2023-01-01', periods=300, freq='D')
        past_data = pd.DataFrame(index=past_index, data={
            "AAPL_price": np.random.uniform(100, 200, size=300),
            "GOOGL_price": np.random.uniform(1500, 2000, size=300)
        })

        current_index = pd.date_range(start='2025-01-27', periods=1, freq='D')
        current_data = pd.DataFrame(index=current_index, data={
            "AAPL_price": np.random.uniform(100, 200, size=1),
            "GOOGL_price": np.random.uniform(1500, 2000, size=1)
        })

        self.algorithm.__data_processor__.__data_history__ = past_data
        portfolio = self.algorithm.execute_trade(capital, current_data)

        self.assertTrue(ticker in portfolio for ticker in self.tickers)
        self.assertTrue(isinstance(portfolio[ticker], int) for ticker in self.tickers)

    def test_execute_trade_over_a_range(self):
        """
        Testing that the algorithm can execute trades continuously
        """

        capital = 10000
        portfolio = None
        start_date = dt.datetime(2005, 0o1, 27)

        for days in range(300):
            current_index = pd.date_range(
                start=start_date + dt.timedelta(days),
                periods=1,
                freq='D'
            )
            current_data = pd.DataFrame(index=current_index, data={
                "AAPL_price": np.random.uniform(100, 200, size=1),
                "GOOGL_price": np.random.uniform(1500, 2000, size=1)
            })
            portfolio = self.algorithm.execute_trade(capital, current_data)

        self.assertTrue(ticker in portfolio for ticker in self.tickers)
        self.assertTrue(isinstance(portfolio[ticker], int) for ticker in self.tickers)
