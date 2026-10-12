"""
This file stores bare-bones information required for any Stock Prediction Algorithm to follow.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from pandas import DataFrame

from uwqsc_algorithmic_trading.interfaces.preprocessing.preprocessor_interface \
    import IPreProcessData
from uwqsc_algorithmic_trading.src.common.config import INTERFACE_NOT_IMPLEMENTED_ERROR


class StockPosition(Enum):
    """
    Enumeration class made to store the information about stock positions.
    Normally, the market can be defined as Bullish, Bearish or Trailing Sideways.
    Similarly, a person's stock position can be defined with hold, short, long, etc.
    """

    SHORT = -1
    HOLD = 0
    LONG = 1


class IAlgorithm(ABC):
    """
    Essential functions shared by all algorithmic trading algorithms.
    """

    def __init__(self,
                 name: str,
                 tickers: List[str],
                 data_processor: IPreProcessData,
                 parameters: Dict[str, Any] = None):
        """
        Initialize a trading algorithm.

        :param name: String. Algorithm name
        :param tickers: List. List of tickers to trade
        :param data_processor: IPreProcessData. Preprocessor instance for algorithm-specific data
        :param parameters: Dictionary. Algorithm-specific parameters
        """

        self.name = name
        self.tickers = tickers
        self.__data_processor__ = data_processor
        self.parameters = parameters or {}
        self.__positions__ = {ticker: StockPosition.HOLD for ticker in tickers}
        self.metrics = {}
        self.__data__: Optional[DataFrame] = None
        self.executing: bool = False
        self.__trade_count__: int = 0

    @abstractmethod
    def generate_signals(self, current_data: DataFrame):
        """
        Generate trading signals based on processed market data.

        :param current_data: DataFrame represents the current processed market data

        :side-effect: Changes positions of the algorithm.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    @abstractmethod
    def calculate_position_size(self,
                                ticker: str,
                                price: float,
                                portfolio_value: float) -> float:
        """
        Calculate position size for a trade.

        :param ticker: String that represents trading symbol
        :param price: Float that represents current price
        :param portfolio_value: Float that represents current portfolio value

        :returns: Size of the position to be played.
        """

        raise INTERFACE_NOT_IMPLEMENTED_ERROR

    def execute_trade(self, capital: float, current_data: DataFrame) -> Dict:
        """
        Execute a single trade for the list of tickers provided.

        :param capital: The integer value of cash allocated to the algorithm
        :param current_data: DataFrame represents the current processed market data

        :returns: DataFrame with portfolio performance
        """

        current_data = self.prepare_data(current_data)
        self.generate_signals(current_data)
        cost_per_ticker: Dict = {}

        for ticker in self.tickers:
            price_col = f"{ticker}_price"
            current_price: float = current_data[price_col].iloc[-1]

            position_size = self.calculate_position_size(
                ticker,
                current_price,
                capital
            )

            cost = position_size * current_price
            cost_per_ticker[ticker] = cost

            if cost != 0:
                self.__trade_count__ += 1

        return cost_per_ticker

    def prepare_data(self, current_data: DataFrame) -> DataFrame:
        """
        Prepare data for the algorithm using the linked data processor.
        """

        return self.__data_processor__.process_data(current_data)
