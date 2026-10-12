from datetime import datetime

import streamlit as st

from uwqsc_backtesting_framework.src.sma_backtesting_framework import SMABacktestingFramework

st.title("Backtesting Framework")

if __name__ == "__main__":
    tickers = ["AAPL", "GOOGL", "MSFT"]
    initial_capital = 2000
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2022, 1, 1)

    framework = SMABacktestingFramework(
        tickers,
        initial_capital,
        start_date,
        end_date
    )

    framework.run()
