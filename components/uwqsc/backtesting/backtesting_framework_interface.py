"""
Interface for a Backtesting Framework Algorithm
"""

from abc import ABC, abstractmethod
from typing import List

import pandas as pd

from uwqsc_algorithmic_trading.interfaces.algorithms.algorithm_interface import IAlgorithm


class IBacktestingFramework(ABC):
    """
    Interface for a Backtesting Framework Algorithm
    """

    def __init__(self,
                 name: str,
                 capital: int,
                 tickers: List[str],
                 algorithm: IAlgorithm):
        self.name = name
        self.capital = capital
        self.tickers = tickers
        self.algorithm = algorithm
        self.data = None

    @abstractmethod
    def load_data(self):
        """
        Loads the data for running the algorithm
        """

    def run(self):
        """
        Runs the trades over the loaded data
        """

        self.load_data()

        for index, current_data in self.data.iterrows():
            current_data = pd.DataFrame(current_data).T
            cost_per_ticker = self.algorithm.execute_trade(self.capital, current_data)

            for ticker in self.tickers:
                self.capital += cost_per_ticker[ticker]

        print(f"[{self.name}] Final capital with: {self.capital}")
