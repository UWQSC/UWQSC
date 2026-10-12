import numpy as np
import pandas as pd
import random
import streamlit as st
from typing import Dict, List, Any

class StockPosition:
    SHORT = -1
    HOLD = 0
    LONG = 1

class SimpleMovingAverageImpl:
    """
    Working logic for Simple Moving Average (SMA) algorithm.
    """

    def __init__(self,
                 tickers: List[str],
                 data: pd.DataFrame,
                 parameters: Dict[str, Any] = None):
        self.name = "Simple Moving Average"
        self.tickers = tickers
        self.parameters = parameters or {"position_size": 0.1, "short_window": 3, "long_window": 6}
        self.__positions__ = {ticker: StockPosition.HOLD for ticker in tickers}
        self.__data__ = data.copy()
        self.__trade_count__ = 0

        # Precompute SMA values ONCE for the entire dataset
        short_window = self.parameters["short_window"]
        long_window = self.parameters["long_window"]

        self.__data__["sma_short"] = self.__data__["prc"].rolling(window=short_window, min_periods=1).mean()
        self.__data__["sma_long"] = self.__data__["prc"].rolling(window=long_window, min_periods=1).mean()

    def generate_signals(self):
        """
        Generate trading signals based on computed SMA.
        """
        for ticker in self.tickers:
            ticker_data = self.__data__[self.__data__["stock_ticker"] == ticker].copy()

            if ticker_data.empty or len(ticker_data) < 2:
                self.__positions__[ticker] = StockPosition.HOLD
                continue

            # Use user-defined or default for both windows   
            short_window = self.parameters.get("short_window", 3)
            long_window = self.parameters.get("long_window", 6)

            ticker_data['sma_short'] = ticker_data["prc"].rolling(window=short_window, min_periods=1).mean()
            ticker_data['sma_long'] = ticker_data["prc"].rolling(window=long_window, min_periods=1).mean()

            if len(ticker_data) < long_window:
                self.__positions__[ticker] = StockPosition.HOLD
                continue

            latest_short = ticker_data['sma_short'].iloc[-1]
            latest_long = ticker_data['sma_long'].iloc[-1]
            prev_short = ticker_data['sma_short'].iloc[-2]
            prev_long = ticker_data['sma_long'].iloc[-2]

            if prev_short <= prev_long and latest_short > latest_long:
                self.__positions__[ticker] = StockPosition.LONG

            elif prev_short >= prev_long and latest_short < latest_long:
                self.__positions__[ticker] = StockPosition.SHORT

            else:
                self.__positions__[ticker] = StockPosition.HOLD


    def execute_trades(self, capital: float) -> pd.DataFrame:
        self.__data__["date"] = pd.to_datetime(self.__data__["date"], errors="coerce")

        portfolio = pd.DataFrame(index=self.__data__["date"].unique())
        
        # Sort dates to maintain proper order
        portfolio = portfolio.sort_index()
        portfolio["capital"] = float(capital)
        
        # Generate trading signals
        self.generate_signals()

        # Precompute grouped data
        grouped_data_by_date = {date: df for date, df in self.__data__.groupby("date")}

        for i, date in enumerate(portfolio.index):
            if i > 0:
                portfolio.loc[date, "capital"] = float(portfolio.loc[portfolio.index[i - 1], "capital"])

            month_data = grouped_data_by_date.get(date, pd.DataFrame())

            if month_data.empty:
                continue

            for ticker in self.tickers:
                ticker_data = month_data[month_data["stock_ticker"] == ticker]
                if ticker_data.empty:
                    continue

                current_price = float(ticker_data["prc"].values[0])
                current_portfolio_value = float(portfolio.loc[date, "capital"])
                position_size = min(
                    self.parameters["position_size"] * current_portfolio_value / max(current_price, 1e-6), 
                    current_portfolio_value / max(current_price, 1e-6)
                )

                cost = position_size * current_price

                if self.__positions__[ticker] == StockPosition.LONG:
                    portfolio.loc[date, 'capital'] -= min(cost, portfolio.loc[date, 'capital'])
                    self.__trade_count__ += 1

                elif self.__positions__[ticker] == StockPosition.SHORT:
                    portfolio.loc[date, 'capital'] += cost
                    self.__trade_count__ += 1

        return portfolio


    def calculate_metrics(self, portfolio: pd.DataFrame) -> Dict[str, float]:
        """
        Compute portfolio performance metrics.
        """
        if portfolio.empty or len(portfolio) < 2:
            print("Warning: Portfolio has insufficient data for calculation.")
            return {
                "Total Return": "N/A",
                "Annual Return": "N/A",
                "Sharpe Ratio": "N/A",
                "Max Drawdown": "N/A",
                "Win Rate": "N/A"
            }
        else:
            portfolio["monthly_return"] = portfolio["capital"].pct_change()

            total_return = (portfolio["capital"].iloc[-1] / portfolio["capital"].iloc[0]) - 1
            annual_return = (1 + total_return) ** (12 / len(portfolio)) - 1
            sharpe_ratio = np.nan if portfolio['monthly_return'].std() == 0 else portfolio['monthly_return'].mean() / portfolio['monthly_return'].std() * np.sqrt(12)

            cumulative_returns = (1 + portfolio["monthly_return"]).cumprod()
            drawdown = (cumulative_returns / cumulative_returns.cummax()) - 1
            max_drawdown = drawdown.min()

            win_rate = sum(portfolio["monthly_return"] > 0) / len(portfolio["monthly_return"])

            return {
                "Total Return": f"{total_return * 100:.2f}%",
                "Annual Return": f"{annual_return * 100:.2f}%",
                "Sharpe Ratio": sharpe_ratio,
                "Max Drawdown": max_drawdown,
                'Trade Count': self.__trade_count__,
                "Win Rate": f"{win_rate * 100:.2f}%"
            }
