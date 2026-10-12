"""
Before running the Simple Moving Average Algorithm, we must prepare the data for it.
This file contains the logic behind preprocessing data specifically for Simple Moving Average.
"""

from typing import List

import pandas as pd

from uwqsc_algorithmic_trading.interfaces.preprocessing.preprocessor_interface \
    import IPreProcessData


class SMAPreProcessorImpl(IPreProcessData):
    """
    Data preprocessor for the Simple Moving Average algorithm.
    """

    def __init__(self,
                 tickers: List[str],
                 short_window: int = 50,
                 long_window: int = 200):
        """
        Initialize the SMA preprocessor.

        :param tickers: List of ticker symbols
        :param short_window: Integer representing a Short-term moving average window in days
        :param long_window: Integer representing a Long-term moving average window in days
        """

        self.tickers = tickers
        self.short_window = short_window
        self.long_window = long_window
        super().__init__()

    def missing_values(self):
        pass

    def remove_duplicate_timestamps(self):
        pass

    def remove_outliers(self, rolling_window=20):
        length_of_history: int = 0

        if self.__data_history__ is not None:
            length_of_history = len(self.__data_history__)

        rolling_window = min(rolling_window, length_of_history)

        if self.__data_history__ is not None and self.__processed_data__ is not None:
            for ticker in self.tickers:
                price_col = f"{ticker}_price"

                rolling_mean = self.__data_history__[price_col].rolling(rolling_window).mean()
                rolling_std = self.__data_history__[price_col].rolling(rolling_window).std()

                z_scores = (self.__data_history__[price_col] - rolling_mean) / rolling_std
                mask = abs(z_scores) > 3

                self.__data_history__ = self.__data_history__[~mask]

        self.generate_short_long_window()

    def generate_short_long_window(self) -> None:
        """
        Simple Moving Average uses short and long-term average windows for calculation.
        We calculate them here for each stock.
        """

        length_of_history: int = 0

        if self.__data_history__ is not None:
            length_of_history = len(self.__data_history__)

        current_short_window = min(self.short_window, length_of_history)
        current_long_window = min(self.long_window, length_of_history)

        for ticker in self.tickers:
            price_col = f"{ticker}_price"

            history = pd.concat([self.__data_history__, self.__processed_data__])

            self.__processed_data__[f"{ticker}_short"] = (
                history[price_col].iloc[-current_short_window:].mean()
            )

            self.__processed_data__[f"{ticker}_long"] = (
                history[price_col].iloc[-current_long_window:].mean()
            )
