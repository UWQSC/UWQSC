"""
Streamlit dashboard: backtest any registered algorithm on data stored in the local database.

Run with: uv run streamlit run bases/uwqsc/dashboard/app.py
"""

import json
from datetime import date

import streamlit as st

# Importing the strategies registers them with the algorithm registry.
from uwqsc import algorithms  # noqa: F401  # pylint: disable=unused-import
from uwqsc.algorithm_core import create_algorithm, list_algorithms
from uwqsc.backtesting import SnapshotBuilder, StoreBackedBacktest
from uwqsc.market_data import MarketDataService, SQLiteMarketDataStoreImpl, YFinanceDataSourceImpl
from uwqsc.sentiment import NullSentimentSource, SentimentService, SQLiteSentimentStoreImpl
from uwqsc.storage import DEFAULT_DB_PATH, connect


def services(path: str):
    """
    Open the database and build the data services.
    """

    conn = connect(path)
    return (
        MarketDataService(YFinanceDataSourceImpl(), SQLiteMarketDataStoreImpl(conn=conn)),
        SentimentService(NullSentimentSource(), SQLiteSentimentStoreImpl(conn=conn)),
    )


st.title("Backtesting Framework")

db_path = st.sidebar.text_input("Database", value=DEFAULT_DB_PATH)
ticker_text = st.sidebar.text_input("Tickers", "AAPL, GOOGL, MSFT")
tickers = [t.strip().upper() for t in ticker_text.split(",") if t.strip()]
start_date = st.sidebar.date_input("Start", value=date(2020, 1, 1))
end_date = st.sidebar.date_input("End", value=date(2022, 1, 1))
initial_capital = st.sidebar.number_input("Initial capital ($)", min_value=100.0, value=2000.0)

market, sentiment = services(db_path)

if st.sidebar.button("Sync market data"):
    with st.spinner("Downloading missing bars..."):
        written = market.sync(tickers, start_date, end_date)
    st.sidebar.write(written)

registered = list_algorithms()
algo_key = st.selectbox("Algorithm", list(registered))
params_text = st.text_area("Parameters (JSON)", json.dumps(registered[algo_key], indent=2))

if st.button("Run backtest"):
    try:
        parameters = json.loads(params_text)
    except json.JSONDecodeError as error:
        st.error(f"Parameters are not valid JSON: {error}")
        st.stop()

    algorithm = create_algorithm(algo_key, tickers, parameters)
    backtest = StoreBackedBacktest(
        algorithm, SnapshotBuilder(market, sentiment), initial_capital, start_date, end_date
    )
    backtest.load_data()
    if backtest.data.empty:
        st.warning("No stored data for this range. Use 'Sync market data' first.")
        st.stop()

    metrics = backtest.run()
    cols = st.columns(3)
    cols[0].metric("Final equity", f"${metrics['final_equity']:,.2f}")
    cols[1].metric("Total return", f"{metrics['total_return']:.2%}")
    cols[2].metric("Max drawdown", f"{metrics['max_drawdown']:.2%}")
    st.subheader("Equity curve")
    st.line_chart(backtest.portfolio.equity_series())
