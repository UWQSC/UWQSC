import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sma_algorithm import SimpleMovingAverageImpl


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

# tab1, tab2 = st.tabs(["Stock Price Evolution", "Portfolio Simulation"])
st.write("Stock Price Evolution")
st.write(f"Stock Price Evolution for {company_name}")

    #Determines if each company has only 1 row of data in df
company_counts = df.groupby("comp_name").size()
single_row_companies = company_counts[company_counts == 1].index
is_single_row = company_name in single_row_companies

if df_company_mth.empty:
        st.warning("No stock data available for the selected date range.")
elif is_single_row:
    st.warning(f"Only one row of data is available for {company_name}, so no trend analysis can be performed.")
    plt.figure(figsize=(12, 6))
    plt.scatter(df_company_mth["month_year"], df_company_mth["prc"], color="blue", label="Stock Price")
    plt.xticks(df_company_mth["month_year"].unique(), rotation=45)
    plt.title(f"Stock Price for {company_name} (Only One Data Point Available)")
    plt.xlabel("Month & Year")
    plt.ylabel("Stock Price ($)")
    plt.legend()
    st.pyplot(plt)
else:
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df_company_mth, x="month_year", y="prc", label="Stock Price")
    plt.xticks(rotation=45)
    plt.title(f"Stock Price Evolution ({yr_option_start}-{month_option_start} to {yr_option_end}-{month_option_end})")
    plt.xlabel("Month & Year")
    plt.ylabel("Stock Price ($)")
    plt.legend()
    st.pyplot(plt)
   