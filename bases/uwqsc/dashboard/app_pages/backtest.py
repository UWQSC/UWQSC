"""
Backtest any registered algorithm on data stored in the local database.
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


with st.sidebar:
    st.header("Data", anchor=False)
    db_path = st.text_input("Database", value=DEFAULT_DB_PATH)
    ticker_text = st.text_input("Tickers", "AAPL, GOOGL, MSFT", help="Comma separated")
    tickers = [t.strip().upper() for t in ticker_text.split(",") if t.strip()]
    start_date = st.date_input("Start", value=date(2020, 1, 1))
    end_date = st.date_input("End", value=date(2022, 1, 1))

    if st.button("Sync market data", icon=":material/sync:", width="stretch"):
        market, _ = services(db_path)
        due = sorted(t for group in market.plan_sync(tickers, start_date, end_date).values()
                     for t in group)
        with st.spinner("Downloading missing bars..."):
            written = market.sync(tickers, start_date, end_date)
        failed = [t for t in due if written.get(t, 0) == 0]
        if not due:
            st.success("Already up to date.", icon=":material/check:")
        elif failed:
            st.warning(f"No new bars for {', '.join(failed)}. Either no trading day has closed "
                       "since the last sync, or the download failed (check the terminal for "
                       "yfinance errors).", icon=":material/warning:")
        else:
            st.success(f"Stored {sum(written.values())} new bars.", icon=":material/check:")
        st.json(written, expanded=False)

registered = list_algorithms()

with st.container(border=True):
    keys = list(registered)
    algo_key = st.selectbox("Algorithm", keys, index=keys.index("sma") if "sma" in keys else 0,
                            key="backtest_algo")
    with st.form("backtest", border=False):
        initial_capital = st.number_input("Initial capital ($)", min_value=100.0, value=2000.0)
        params_text = st.text_area(
            "Parameters (JSON)",
            json.dumps(registered[algo_key], indent=2),
            key=f"backtest_params_{algo_key}",
        )
        submitted = st.form_submit_button("Run backtest", type="primary",
                                          icon=":material/play_arrow:")

if submitted:
    try:
        parameters = json.loads(params_text)
    except json.JSONDecodeError as error:
        st.error(f"Parameters are not valid JSON: {error}", icon=":material/error:")
        st.stop()

    market, sentiment = services(db_path)
    algorithm = create_algorithm(algo_key, tickers, parameters)
    backtest = StoreBackedBacktest(
        algorithm, SnapshotBuilder(market, sentiment), initial_capital, start_date, end_date
    )
    with st.spinner("Running backtest..."):
        backtest.load_data()
        if backtest.data.empty:
            st.warning("No stored data for this range. Use **Sync market data** first.",
                       icon=":material/warning:")
            st.stop()
        try:
            metrics = backtest.run()
        except Exception as error:  # pylint: disable=broad-exception-caught
            st.error(f"`{algo_key}` failed during the backtest: {error!r}", icon=":material/error:")
            st.stop()
        st.session_state.backtest_result = {
            "metrics": metrics,
            "equity": backtest.portfolio.equity_series().rename("Equity"),
            "label": f"{algo_key} on {', '.join(tickers)}",
        }

result = st.session_state.get("backtest_result")
if result:
    metrics = result["metrics"]
    st.subheader(result["label"], anchor=False)
    with st.container(horizontal=True):
        st.metric("Final equity", f"${metrics['final_equity']:,.2f}", border=True)
        st.metric("Total return", f"{metrics['total_return']:.2%}", border=True)
        st.metric("Max drawdown", f"{metrics['max_drawdown']:.2%}", border=True)
    with st.container(border=True):
        st.markdown("**Equity curve**")
        st.line_chart(result["equity"], y_label="Equity ($)", alt="Portfolio equity over time")
