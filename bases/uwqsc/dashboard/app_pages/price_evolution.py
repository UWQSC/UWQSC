"""
Monthly price history for one company in the hackathon dataset (top 1000 NASDAQ stocks).
"""

import streamlit as st

from uwqsc.dashboard.hackathon import require_data, select_company_range

df = require_data()
st.caption("Top 1000 stocks on NASDAQ")

company, df_range = select_company_range(df)

if df_range.empty:
    st.warning("No stock data available for the selected months.", icon=":material/warning:")
    st.stop()

prices = df_range[["month_year", "prc"]].rename(columns={"month_year": "Month", "prc": "Price ($)"})

with st.container(border=True):
    st.markdown(f"**Price evolution for {company}**")
    if len(prices) == 1:
        st.caption("Only one data point is available, so no trend can be shown.")
        st.scatter_chart(prices, x="Month", y="Price ($)", alt=f"Single price point for {company}")
    else:
        st.line_chart(prices, x="Month", y="Price ($)", alt=f"Monthly stock price of {company}")
