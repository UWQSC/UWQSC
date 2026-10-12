"""
Implementation of the Simple Moving Average (SMA) algorithm.
"""

import random
from typing import Dict, List, Any

import pandas as pd

from uwqsc_algorithmic_trading.interfaces.algorithms.algorithm_interface \
    import IAlgorithm, StockPosition
from uwqsc_algorithmic_trading.src.preprocessing.sma_preprocessor_impl import SMAPreProcessorImpl


class SimpleMovingAverageImpl(IAlgorithm):
    """
    Working logic for Simple Moving Average (SMA) algorithm.
    """

    def __init__(self,
                 tickers: List[str],
                 parameters: Dict[str, Any] = None):
        name = "Simple Moving Average"
        data_processor = SMAPreProcessorImpl(tickers)

        self.__current_short__: Dict[str, int] = {}
        self.__current_long__: Dict[str, int] = {}
        self.__previous_short__: Dict[str, int] = {}
        self.__previous_long__: Dict[str, int] = {}

        super().__init__(name, tickers, data_processor, parameters)

    def generate_signals(self, current_data: pd.DataFrame):
        if not self.executing:
            for ticker in self.tickers:
                short_col = f"{ticker}_short"
                long_col = f"{ticker}_long"

                self.__current_short__[ticker] = current_data[short_col].iloc[-1]
                self.__current_long__[ticker] = current_data[long_col].iloc[-1]

                self.__positions__[ticker] = random.choice(list(StockPosition))
            self.executing = True
        else:
            for ticker in self.tickers:
                short_col = f"{ticker}_short"
                long_col = f"{ticker}_long"

                self.__previous_short__[ticker] = self.__current_short__[ticker]
                self.__previous_long__[ticker] = self.__current_long__[ticker]
                self.__current_short__[ticker] = current_data[short_col].iloc[-1]
                self.__current_long__[ticker] = current_data[long_col].iloc[-1]

                if (self.__previous_short__[ticker] <= self.__previous_long__[ticker] and
                        self.__current_short__[ticker] > self.__current_long__[ticker]):
                    self.__positions__[ticker] = StockPosition.LONG
                elif (self.__previous_short__[ticker] > self.__previous_long__[ticker] and
                        self.__current_short__[ticker] <= self.__current_long__[ticker]):
                    self.__positions__[ticker] = StockPosition.SHORT
                else:
                    self.__positions__[ticker] = StockPosition.HOLD

    def calculate_position_size(self, ticker: str, price: float, portfolio_value: float) -> float:
        base_position_size: float = self.parameters['position_size'] * portfolio_value
        position_size: float = 0.0

        if self.__positions__[ticker] == StockPosition.LONG:
            position_size = base_position_size / price
        elif self.__positions__[ticker] == StockPosition.SHORT:
            position_size = -1 * (base_position_size / price)

        return position_size
