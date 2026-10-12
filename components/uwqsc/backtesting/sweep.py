"""
Runs every registered algorithm over a parameter grid and ranks the results.
"""

from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from uwqsc.algorithm_core.registry import create_algorithm, list_algorithms
from uwqsc.backtesting.snapshot_builder import SnapshotBuilder
from uwqsc.backtesting.store_backed_backtest import StoreBackedBacktest


def sweep(builder: SnapshotBuilder,
          tickers: List[str],
          start: Optional[date],
          end: Optional[date],
          capital: float,
          grid: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> pd.DataFrame:
    """
    Backtest each (algorithm, parameters) pair and rank by final equity.

    :param grid: algorithm key -> list of parameter overrides. Defaults to every registered
                 algorithm with its default parameters
    :returns: One row per run with algorithm, parameters, final_equity, total_return,
              max_drawdown, trade_count and error, best first. A run that raises is kept
              with its error message and no metrics, ranked last, so one broken strategy
              does not abort the sweep.
    """

    if grid is None:
        grid = {key: [{}] for key in list_algorithms()}

    rows = []
    for key, parameter_sets in grid.items():
        for overrides in parameter_sets:
            algorithm = create_algorithm(key, tickers, overrides)
            backtest = StoreBackedBacktest(algorithm, builder, capital, start, end, tickers)
            rows.append({"algorithm": key, "parameters": algorithm.parameters,
                         **_run_safely(backtest)})

    results = pd.DataFrame(
        rows,
        columns=["algorithm", "parameters", "final_equity", "total_return",
                 "max_drawdown", "trade_count", "error"]
    )
    return results.sort_values("final_equity", ascending=False, na_position="last",
                               ignore_index=True)


def _run_safely(backtest: StoreBackedBacktest) -> Dict[str, Any]:
    try:
        return {**backtest.run(), "error": None}
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return {"error": f"{type(exc).__name__}: {exc}"}
