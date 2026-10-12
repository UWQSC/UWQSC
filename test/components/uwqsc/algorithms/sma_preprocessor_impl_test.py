"""
Testing the Simple Moving Average Preprocessor
"""

import unittest

import datetime as dt
import numpy as np
import pandas as pd

from uwqsc_algorithmic_trading.src.preprocessing.sma_preprocessor_impl import SMAPreProcessorImpl


class SMAPreprocessorImplTest(unittest.TestCase):
    """
    This class is used to test each component of Simple Moving Average's preprocessor
    """

    def setUp(self):
        self.tickers = ["AAPL", "GOOGL"]
        self.short_window = 50
        self.long_window = 200

        self.preprocessor = SMAPreProcessorImpl(self.tickers,
                                                self.short_window,
                                                self.long_window)

        history_index = pd.date_range(start='2005-01-27', periods=300, freq='D')
        history_data = pd.DataFrame(index=history_index, data={
            f"{ticker}_price": np.random.uniform(100, 200, size=300)
            for ticker in self.tickers
        })

        current_index = pd.date_range(start='2025-01-27', periods=1, freq='D')
        current_data = pd.DataFrame(index=current_index, data={
            f"{ticker}_price": np.random.uniform(100, 200, size=1)
            for ticker in self.tickers
        })

        self.preprocessor.__processed_data__ = current_data
        self.preprocessor.__data_history__ = history_data

    def test_remove_outliers_removes_outliers(self):
        """
        Testing that outliers are removed
        """

        changed_dates_values = {
            dt.datetime(1900, 0o1, 0o1): 99999,
            dt.datetime(2100, 0o1, 0o1): -99999
        }

        for ticker in self.tickers:
            for date_value in changed_dates_values.items():
                self.preprocessor.__data_history__.loc[
                    date_value[0],
                    f"{ticker}_price"
                ] = date_value[1]
        original_size = len(self.preprocessor.__processed_data__)

        self.preprocessor.remove_outliers()

        for ticker in self.tickers:
            for date in changed_dates_values:
                self.assertEqual(
                    self.preprocessor.__processed_data__.get([ticker, date]),
                    None
                )

        self.assertLessEqual(len(self.preprocessor.__processed_data__), original_size)

    def test_generate_short_long_window(self):
        """
        Testing that we generate correct short and long averages
        """

        self.preprocessor.generate_short_long_window()

        history = pd.concat(
            [self.preprocessor.__data_history__, self.preprocessor.__processed_data__]
        )

        for ticker in self.tickers:
            last_50_rolling_mean = history[f"{ticker}_price"].iloc[-50:].mean()
            last_200_rolling_mean = history[f"{ticker}_price"].iloc[-200:].mean()

            self.assertEqual(
                self.preprocessor.__processed_data__[f"{ticker}_short"].iloc[-1],
                last_50_rolling_mean
            )
            self.assertEqual(
                self.preprocessor.__processed_data__[f"{ticker}_long"].iloc[-1],
                last_200_rolling_mean
            )
