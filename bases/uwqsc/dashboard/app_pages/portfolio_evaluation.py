"""
Portfolio simulation on the hackathon dataset: the registered SMA strategy, or a custom
indicator-threshold strategy.
"""

import numpy as np
import pandas as pd
import streamlit as st

from uwqsc import algorithms  # noqa: F401  # pylint: disable=unused-import
from uwqsc.algorithm_core import create_algorithm
from uwqsc.backtesting import Portfolio
from uwqsc.dashboard.hackathon import require_data, select_company_range

# Indicators that work with the dataset's monthly rows
VALID_INDICATORS = [
    "ret_1_0", "ret_3_1", "ret_6_1", "ret_12_1", "stock_exret", "prc", "market_equity",
    "eps_actual", "be_me", "sale_bev", "ocf_me", "sale_gr1", "at_gr1", "betadown_252d",
    "corr_1260d", "ivol_capm_21d",
]
THRESHOLD_LIMIT = 1_000_000_000.0


def combine(conditions, mode: str):
    """
    AND/OR a list of boolean Series; False when there are none.
    """

    if not conditions:
        return False
    reducer = np.logical_and if mode == "AND" else np.logical_or
    return reducer.reduce(conditions)


def threshold_input(label: str, key: str) -> float:
    """
    Number input for one indicator threshold.
    """

    return st.number_input(label, min_value=-THRESHOLD_LIMIT, max_value=THRESHOLD_LIMIT,
                           value=0.0, key=key)


df = require_data()
st.caption("Top 1000 stocks on NASDAQ")
company, df_range = select_company_range(df)

if df_range.empty:
    st.warning("No stock data available for the selected months.", icon=":material/warning:")
    st.stop()

strategy = st.segmented_control("Strategy", ["SMA", "Custom"], default="SMA",
                                key="portfolio_strategy")

if strategy == "SMA":
    ticker = df_range["stock_ticker"].iloc[0]

    with st.form("sma_backtest"):
        initial_capital = st.number_input("Initial capital ($)", min_value=1000,
                                          value=1_000_000, step=1000)
        with st.container(horizontal=True):
            short_window = st.slider("Short window (months)", min_value=1, max_value=12, value=3)
            long_window = st.slider("Long window (months)", min_value=3, max_value=24, value=6)
        submitted = st.form_submit_button("Run SMA backtest", type="primary",
                                          icon=":material/play_arrow:")

    if submitted:
        prices = (df_range.set_index("date")[["prc"]]
                  .rename(columns={"prc": f"{ticker}_price"})
                  .sort_index())
        algorithm = create_algorithm(
            "sma", [ticker],
            {"position_size": 0.1, "short_window": short_window, "long_window": long_window},
        )
        portfolio = Portfolio(initial_capital)
        for when, row in prices.iterrows():
            current = {ticker: float(row[f"{ticker}_price"])}
            trades = algorithm.execute_trade(portfolio.equity(current), pd.DataFrame([row]))
            portfolio.apply(trades, current)
            portfolio.mark(when, current)

        metrics = portfolio.metrics()
        with st.container(horizontal=True):
            st.metric("Final equity", f"${metrics['final_equity']:,.2f}", border=True)
            st.metric("Total return", f"{metrics['total_return']:.2%}", border=True)
            st.metric("Max drawdown", f"{metrics['max_drawdown']:.2%}", border=True)
        with st.container(border=True):
            st.markdown(f"**Portfolio value, SMA on {ticker}**")
            st.line_chart(portfolio.equity_series().rename("Equity"), y_label="Equity ($)",
                          alt=f"Portfolio equity of the SMA strategy on {ticker}")

elif strategy == "Custom":
    with st.container(border=True):
        st.markdown("**Entry (buy) conditions**: indicator above threshold")
        entry_indicators = st.multiselect("Entry indicators", VALID_INDICATORS)
        entry_mode = st.segmented_control("Combine entry conditions with", ["AND", "OR"],
                                          default="AND", key="entry_mode")
        entry_thresholds = {
            ind: threshold_input(f"Entry threshold for {ind}", f"entry_{ind}")
            for ind in entry_indicators
        }

    with st.container(border=True):
        st.markdown("**Exit (sell) conditions**: indicator below threshold")
        exit_indicators = st.multiselect("Exit indicators", VALID_INDICATORS)
        exit_mode = st.segmented_control("Combine exit conditions with", ["AND", "OR"],
                                         default="AND", key="exit_mode")
        exit_thresholds = {
            ind: threshold_input(f"Exit threshold for {ind}", f"exit_{ind}")
            for ind in exit_indicators
        }

    data = df_range.ffill().bfill().fillna(0)
    data["entry_signal"] = combine(
        [data[ind] > value for ind, value in entry_thresholds.items() if ind in data], entry_mode
    )
    data["exit_signal"] = combine(
        [data[ind] < value for ind, value in exit_thresholds.items() if ind in data], exit_mode
    )

    # All-in on entry, all-out on exit, starting from $1M
    capital, holdings = 1_000_000.0, 0.0
    values = []
    for row in data.itertuples():
        if row.entry_signal:
            shares = capital // row.prc if row.prc > 0 else 0
            holdings += shares
            capital -= shares * row.prc
        elif row.exit_signal and holdings > 0:
            capital += holdings * row.prc
            holdings = 0
        values.append(capital + holdings * row.prc)

    data["Portfolio value ($)"] = values
    with st.container(border=True):
        st.markdown(f"**Portfolio simulation for {company}**")
        st.line_chart(data, x="month_year", y="Portfolio value ($)", x_label="Month",
                      alt=f"Custom strategy portfolio value for {company}")
