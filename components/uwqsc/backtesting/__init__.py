"""
Runs algorithms over stored data: snapshot assembly, portfolio accounting and sweeps.
"""

from uwqsc.backtesting.backtesting_framework_interface import IBacktestingFramework
from uwqsc.backtesting.portfolio import Portfolio
from uwqsc.backtesting.snapshot_builder import KNOWN_FEATURES, SnapshotBuilder
from uwqsc.backtesting.store_backed_backtest import StoreBackedBacktest
from uwqsc.backtesting.sweep import sweep

__all__ = [
    "IBacktestingFramework",
    "KNOWN_FEATURES",
    "Portfolio",
    "SnapshotBuilder",
    "StoreBackedBacktest",
    "sweep",
]
