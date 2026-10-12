import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from uwqsc_algorithmic_trading.src.algorithms.simple_moving_average_impl import SimpleMovingAverageImpl
from uwqsc_algorithmic_trading.interfaces.algorithms.algorithm_interface import IAlgorithm


#Loading parquet data file (converted from CSV)
@st.cache_data
def load_data():
    return pd.read_parquet('data/hackathon_sample_v2.parquet')
df = load_data()

st.write("Top 1000 stocks on NASDAQ")

company_name = st.selectbox('Select a Company: ', df['comp_name'].unique())
'You selected: ' , company_name

df_company = df[df["comp_name"] == company_name].copy() # Creates dataframe for selected company
df_company['date'] = pd.to_datetime(df_company['date'].astype(str), format='%Y%m%d')

#Dropdowns for year and month selections
st.write("Select your desired month range:")
yr_option_start = st.selectbox('Start Year: ', df_company['year'].unique())
month_option_start = st.selectbox('Start Month: ', list(range(1, 13)))
yr_option_end = st.selectbox('End Year: ', df_company['year'].unique())
month_option_end = st.selectbox('End Month: ', list(range(1, 13)))

#Conditional checks based on time period selection
if yr_option_start is None or yr_option_end is None:
    st.warning("Please choose a year for both the start and end")
    st.stop()
elif month_option_start is None or month_option_end is None:
    st.warning("Please choose a month for both the start and end")
    st.stop()
elif (yr_option_start, month_option_start) > (yr_option_end, month_option_end):
    st.warning("Please choose an earlier starting year/month or a later ending year/month")
    st.stop()

#Creating filtered dataframe to work with
elif yr_option_start == yr_option_end:
    df_company_mth = df_company[
        (df_company["year"] == yr_option_start) & 
        (df_company["month"] >= month_option_start) & 
        (df_company["month"] <= month_option_end)
    ].copy()
else:
    df_company_mth = df_company[
        (
            ((df_company["year"] == yr_option_start) & (df_company["month"] >= month_option_start)) |
            ((df_company["year"] > yr_option_start) & (df_company["year"] < yr_option_end)) |
            ((df_company["year"] == yr_option_end) & (df_company["month"] <= month_option_end))
        )
    ].copy()

df_company_mth["month_year"] = df_company_mth["date"].dt.to_period("M").dt.to_timestamp()

st.write("Portfolio Simulation with Your Own Custom Trading Strategy!")

if df_company_mth.empty:
    st.warning("No stock data available for the selected date range.")
else:
    strat_list = ["SMA", "Custom"]
    strat = st.selectbox('Select your strategy for backtesting: ', strat_list)

    if strat == "SMA":
        selected_ticker = df_company["stock_ticker"].iloc[0]
        selected_tickers = [selected_ticker]

        df_sma = df_company_mth[["date", "prc"]].copy()
        df_sma["stock_ticker"] = selected_ticker

        #Obtaining start/end dates from selected range
        start_date = df_company_mth["date"].min()
        end_date = df_company_mth["date"].max()

        initial_capital = st.number_input("Initial Capital ($)", min_value=1000, value=1_000_000, step=1000)

        #User selects SMA parameters
        short_window = st.slider("SMA Short Window (Months)", min_value=1, max_value=12, value=3)
        long_window = st.slider("SMA Long Window (Months)", min_value=3, max_value=24, value=6)

        #Run SMA backtest
        if st.button("Run SMA Backtest"):
            st.write(f"Running SMA Strategy for: {selected_ticker}")

            df_pivot = df_sma.pivot(index="date", columns="stock_ticker", values="prc")
            df_pivot.columns = [f"{ticker}_price" for ticker in df_pivot.columns]
            df_pivot.sort_index(inplace=True)

            strategy: IAlgorithm = SimpleMovingAverageImpl(
                tickers=selected_tickers,
                parameters={"position_size": 0.1, "short_window": short_window, "long_window": long_window}
            )

            capital = initial_capital
            portfolio = []

            for date, row in df_pivot.iterrows():
                current_data = pd.DataFrame([row])
                trades = strategy.execute_trade(capital, current_data)
                for ticker, change in trades.items():
                    capital += change
                portfolio.append((date, capital))

            # Display results
            portfolio_df = pd.DataFrame(portfolio, columns=["Date", "Capital"])
            portfolio_df.set_index("Date", inplace=True)

            st.subheader("Portfolio Value Over Time")
            st.line_chart(portfolio_df["Capital"])
            st.subheader("Final Capital")
            st.write(f"${capital:,.2f}")

    else:
        st.write("Your current company selection is ", company_name)
        st.write("Please change above selections if you would like to change company & time period")

        #Shortlist of indicators that work with given monthly data
        valid_indicators = [
            "ret_1_0", "ret_3_1", "ret_6_1", "ret_12_1", "stock_exret", "prc", "market_equity", "eps_actual", "be_me", "sale_bev", "ocf_me",
            "sale_gr1", "at_gr1", "betadown_252d", "corr_1260d", "ivol_capm_21d"
        ]
        
        #Selection of entry & exit indicators and choice for AND or OR operator for indicators
        entry_indicators = st.multiselect("Select Entry Indicators (Buy Signal):", valid_indicators)
        entry_condition_type = st.radio("Combine Entry Conditions With:", ["AND", "OR"])
        
        exit_indicators = st.multiselect("Select Exit Indicators (Sell Signal):", valid_indicators)
        exit_condition_type = st.radio("Combine Exit Conditions With:", ["AND", "OR"])
        
        #Set threshold values for each selected condition
        indicator_thresholds = {}

        for ind in entry_indicators:
            #In both entry & exit
            if ind in exit_indicators:
                indicator_thresholds[f"entry_{ind}"] = st.number_input(
                    f"Entry Threshold for {ind}:", min_value=-1000000000.0, max_value=1000000000.0, value=0.0
                )
                indicator_thresholds[f"exit_{ind}"] = st.number_input(
                    f"Exit Threshold for {ind}:", min_value=-1000000000.0, max_value=1000000000.0, value=0.0
                )

            #Only in entry
            else:
                indicator_thresholds[f"entry_{ind}"] = st.number_input(
                    f"Entry Threshold for {ind}:", min_value=-1000000000.0, max_value=1000000000.0, value=0.0
                )

        for ind in exit_indicators:
            #Only in exit
            if ind not in entry_indicators:
                indicator_thresholds[f"exit_{ind}"] = st.number_input(
                    f"Exit Threshold for {ind}:", min_value=-1000000000.0, max_value=1000000000.0, value=0.0
                )

        #Portfolio simulation parameters
        initial_capital = 1_000_000
        capital = initial_capital
        holdings = 0

        #Handles missing values in filtered dataset using forward & backward fill
        #Also fills remaining missing values with 0
        df_company_mth.ffill(inplace=True)
        df_company_mth.bfill(inplace=True)
        df_company_mth.fillna(0, inplace=True)

        df_company_mth["portfolio_value"] = np.nan

        #Apply entry conditions
        if entry_indicators:
            entry_conditions = []
        
            for ind in entry_indicators:
                if ind in df_company_mth.columns:
                    threshold_key = f"entry_{ind}"
                    if threshold_key in indicator_thresholds:
                        entry_conditions.append(df_company_mth[ind] > indicator_thresholds[threshold_key])
            
            if entry_condition_type == "AND":
                df_company_mth["entry_signal"] = np.logical_and.reduce(entry_conditions) if entry_conditions else False
            else:
                df_company_mth["entry_signal"] = np.logical_or.reduce(entry_conditions) if entry_conditions else False
            
        else:
            df_company_mth["entry_signal"] = False
        
        #Apply exit conditions
        if exit_indicators:
            exit_conditions = []

            for ind in exit_indicators:
                if ind in df_company_mth.columns:
                    threshold_key = f"exit_{ind}"
                    if threshold_key in indicator_thresholds:
                        exit_conditions.append(df_company_mth[ind] < indicator_thresholds[threshold_key])
            
            if exit_condition_type == "AND":
                df_company_mth["exit_signal"] = np.logical_and.reduce(exit_conditions) if exit_conditions else False
            else:
                df_company_mth["exit_signal"] = np.logical_or.reduce(exit_conditions) if exit_conditions else False
        
        else:
            df_company_mth["exit_signal"] = False

        #Portfolio simulation
        for index, row in df_company_mth.iterrows():
            if row["entry_signal"]:
                #Determine number of shares to buy
                shares = capital // row["prc"]
                
                if shares > 0:
                    #Makes adjustment to current holdings & capital
                    holdings += shares
                    capital -= shares * row["prc"]
                
                #Updates portfolio value after an entry signal is met
                df_company_mth.at[index, "portfolio_value"] = capital + (holdings * row["prc"])

            elif row["exit_signal"] and holdings > 0:
                #Sells all shares    
                capital += holdings * row["prc"]
                holdings = 0
            
                #Updates portfolio value after an exit signal is met
                df_company_mth.at[index, "portfolio_value"] = capital
        
            else:
                #Default update for portfolio value
                df_company_mth.at[index, "portfolio_value"] = capital + (holdings * row["prc"])
        
        #Portfolio performance visualization
        st.write("Portfolio Performance Over Time")
        plt.figure(figsize=(12, 6))
        plt.plot(df_company_mth["month_year"], df_company_mth["portfolio_value"], label="Portfolio Value", color="green")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value ($)")
        plt.title(f"Portfolio Simulation for {company_name}")
        plt.legend()
        st.pyplot(plt)