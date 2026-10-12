"""
Backtesting Framework for Simple Moving Average
"""

import datetime
from typing import List

import yfinance as yf
import pandas as pd

from uwqsc_backtesting_framework.interfaces.backtesting_framework_interface import (
    IBacktestingFramework
)
from uwqsc_algorithmic_trading.src.algorithms.simple_moving_average_impl import (
    SimpleMovingAverageImpl
)


class SMABacktestingFramework(IBacktestingFramework):
    """
    Logic regarding analysis of Simple Moving Average trading strategy
    """

    def __init__(
            self,
            tickers: List[str],
            capital: int,
            start_date: datetime.datetime,
            end_date: datetime.datetime
    ):
        name = "Simple Moving Average Backtesting Framework"
        algorithm = SimpleMovingAverageImpl(
            tickers,
            parameters={'position_size': 0.1}
        )

        self.start_date = start_date
        self.end_date = end_date
        self.__raw_data__ = None

        super().__init__(name, capital, tickers, algorithm)

    def load_data(self):
        self.__raw_data__ = {}

        for ticker in self.tickers:
            data = yf.download(ticker, start=self.start_date, end=self.end_date)
            if not data.empty:
                self.__raw_data__[ticker] = data

        combined_data = pd.DataFrame()
        for ticker, data in self.__raw_data__.items():
            price_data = data.drop(["Close", "High", "Low", "Volume"], axis=1, level=0)
            price_data = pd.DataFrame(
                data=price_data.to_numpy().flatten(),
                index=data.index,
                columns=[f"{ticker}_price"]
            )
            combined_data = pd.concat([combined_data, price_data], axis=1)

        combined_data.index.name = "Date"
        self.data = combined_data
