"""
Interface for a Backtesting Framework Algorithm
"""

from abc import ABC, abstractmethod
from typing import Dict, List

import pandas as pd

from uwqsc.algorithm_core.algorithm_interface import IAlgorithm
from uwqsc.backtesting.portfolio import Portfolio


class IBacktestingFramework(ABC):
    """
    Interface for a Backtesting Framework Algorithm
    """

    def __init__(self,
                 name: str,
                 capital: float,
                 tickers: List[str],
                 algorithm: IAlgorithm):
        self.name = name
        self.capital = capital
        self.tickers = tickers
        self.algorithm = algorithm
        self.data = None
        self.portfolio = Portfolio(capital)

    @abstractmethod
    def load_data(self):
        """
        Loads the data for running the algorithm into self.data: one row per date with at
        least "{ticker}_price" for every ticker.
        """

    def run(self) -> Dict[str, float]:
        """
        Runs the trades over the loaded data, one market snapshot at a time.

        :returns: Portfolio metrics (final_equity, total_return, max_drawdown, trade_count)
        """

        self.load_data()
        self.portfolio = Portfolio(self.capital)

        for index, current_data in self.data.iterrows():
            current_data = pd.DataFrame(current_data).T
            prices = {t: float(current_data[f"{t}_price"].iloc[-1]) for t in self.tickers}

            equity = self.portfolio.equity(prices)
            cost_per_ticker = self.algorithm.execute_trade(equity, current_data)

            self.portfolio.apply(cost_per_ticker, prices)
            self.portfolio.mark(index, prices)

        metrics = self.portfolio.metrics()
        print(f"[{self.name}] Final equity: {metrics['final_equity']:.2f}")
        return metrics
