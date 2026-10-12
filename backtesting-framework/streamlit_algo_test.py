import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sma_algorithm import SimpleMovingAverageImpl


# Load dataset
@st.cache_data
def load_data():
    df = pd.read_parquet("data/hackathon_sample_v2.parquet")
    
    # Reduce dataset size for performance optimization
    return df.sample(n=50_000, random_state=42)  # Use 50K rows instead of 300K for testing

df = load_data()

# Streamlit interface
st.title("Algorithmic Trading Strategy Tester")
st.write("Select stocks and run backtesting on SMA and other algorithms.")

# User selects tickers
available_tickers = sorted(df["stock_ticker"].dropna().unique())
selected_tickers = st.multiselect("Select Tickers for Testing:", available_tickers)

# Portfolio simulation settings
initial_capital = st.number_input("Initial Capital ($)", min_value=1000, value=1_000_000, step=1000)

# User selects SMA parameters
short_window = st.slider("SMA Short Window (Months)", min_value=1, max_value=12, value=3)
long_window = st.slider("SMA Long Window (Months)", min_value=3, max_value=24, value=6)

# Run SMA backtest
if st.button("Run SMA Backtest") and selected_tickers:
    st.write(f"Running SMA Strategy for: {', '.join(selected_tickers)}")

    sma_algo = SimpleMovingAverageImpl(
        tickers=selected_tickers,
        data=df,
        parameters={"position_size": 0.1, "short_window": short_window, "long_window": long_window}
    )

    sma_portfolio = sma_algo.execute_trades(capital=initial_capital)
    metrics = sma_algo.calculate_metrics(sma_portfolio)

    st.subheader("SMA Portfolio Performance Metrics")
    for key, value in metrics.items():
        st.write(f"**{key}:** {value}")

    st.subheader("Portfolio Value Over Time")
    st.line_chart(sma_portfolio["capital"])
