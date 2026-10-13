"""
Streamlit dashboard entry point.

Run with: uv run streamlit run bases/uwqsc/dashboard/app.py
"""

import streamlit as st

st.set_page_config(page_title="UWQSC", page_icon=":material/query_stats:", layout="wide")

page = st.navigation(
    {
        "Backtesting": [
            st.Page("app_pages/backtest.py", title="Backtest", icon=":material/monitoring:",
                    default=True),
        ],
        "Hackathon dataset": [
            st.Page("app_pages/price_evolution.py", title="Price evolution",
                    icon=":material/show_chart:"),
            st.Page("app_pages/portfolio_evaluation.py", title="Portfolio simulation",
                    icon=":material/account_balance_wallet:"),
        ],
    },
    position="top",
)

st.title(page.title, anchor=False)

page.run()
