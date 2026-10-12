"""
Cash-and-shares accounting for a backtest.
"""

import math
from typing import Dict, List, Mapping, Tuple

import pandas as pd


class Portfolio:
    """
    Tracks cash, shares held per ticker and the equity curve.

    IAlgorithm.execute_trade returns, per ticker, the cash value of the trade
    (shares * price): positive buys or covers, negative sells or shorts. Buying
    moves cash into shares; equity only changes when prices move.
    """

    def __init__(self, cash: float):
        """
        :param cash: Float. Starting cash
        """

        self.initial_cash = float(cash)
        self.cash = float(cash)
        self.shares: Dict[str, float] = {}
        self.last_prices: Dict[str, float] = {}
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        self.trade_count = 0

    def apply(self, costs: Mapping[str, float], prices: Mapping[str, float]) -> None:
        """
        Apply one step of trades.

        :param costs: ticker -> trade value (shares * price) from execute_trade
        :param prices: ticker -> price the trade executed at
        """

        for ticker, cost in costs.items():
            price = prices.get(ticker)
            if not _usable(cost) or cost == 0 or not _usable(price) or price <= 0:
                continue
            self.cash -= cost
            self.shares[ticker] = self.shares.get(ticker, 0.0) + cost / price
            self.trade_count += 1

    def equity(self, prices: Mapping[str, float]) -> float:
        """
        :param prices: ticker -> latest price. Missing or NaN prices fall back to the last seen
        :returns: cash + value of all held shares
        """

        for ticker, price in prices.items():
            if _usable(price):
                self.last_prices[ticker] = float(price)

        held = sum(
            qty * self.last_prices.get(ticker, 0.0) for ticker, qty in self.shares.items()
        )
        return self.cash + held

    def mark(self, when, prices: Mapping[str, float]) -> float:
        """
        Record equity for a point in time.

        :param when: Timestamp (or any label) for the equity curve
        :param prices: ticker -> latest price
        :returns: The recorded equity
        """

        value = self.equity(prices)
        self.equity_curve.append((pd.Timestamp(when), value))
        return value

    def equity_series(self) -> pd.Series:
        """
        :returns: Equity curve as a Series indexed by timestamp
        """

        if not self.equity_curve:
            return pd.Series(dtype=float, name="equity")
        index, values = zip(*self.equity_curve)
        return pd.Series(values, index=pd.DatetimeIndex(index, name="Date"), name="equity")

    def metrics(self) -> Dict[str, float]:
        """
        :returns: final_equity, total_return (fraction), max_drawdown (fraction, <= 0)
                  and trade_count
        """

        curve = self.equity_series()
        final = float(curve.iloc[-1]) if not curve.empty else self.initial_cash
        drawdown = 0.0
        if not curve.empty:
            drawdown = float((curve / curve.cummax() - 1).min())

        return {
            "final_equity": final,
            "total_return": final / self.initial_cash - 1 if self.initial_cash else 0.0,
            "max_drawdown": drawdown,
            "trade_count": self.trade_count,
        }


def _usable(value) -> bool:
    return value is not None and not (isinstance(value, float) and math.isnan(value))
