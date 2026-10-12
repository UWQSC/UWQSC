"""
Backtest that reads its market (and sentiment) data from the local database.
"""

from datetime import date
from typing import List, Optional

from uwqsc.algorithm_core.algorithm_interface import IAlgorithm
from uwqsc.backtesting.backtesting_framework_interface import IBacktestingFramework
from uwqsc.backtesting.snapshot_builder import SnapshotBuilder


class StoreBackedBacktest(IBacktestingFramework):
    """
    Runs any IAlgorithm over stored data, building exactly the features it declares.
    """

    def __init__(self,
                 algorithm: IAlgorithm,
                 builder: SnapshotBuilder,
                 capital: float,
                 start: Optional[date] = None,
                 end: Optional[date] = None,
                 tickers: Optional[List[str]] = None):
        tickers = tickers or list(algorithm.tickers)
        super().__init__(f"{algorithm.name} Backtest", capital, tickers, algorithm)
        self.builder = builder
        self.start = start
        self.end = end

    def load_data(self):
        self.data = self.builder.build(
            self.tickers,
            self.start,
            self.end,
            features=self.algorithm.REQUIRED_FEATURES
        )
