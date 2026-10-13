"""
Shared loading and filtering for the hackathon dataset pages.

The parquet file is not committed; see the README for how to create it.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd
import streamlit as st

DATA_PATH = Path("data/hackathon_sample_v2.parquet")


@st.cache_data(max_entries=1, show_spinner="Loading hackathon dataset...")
def load_data() -> pd.DataFrame:
    """
    Load the hackathon parquet once per session server, with dates parsed and a month column.
    """

    df = pd.read_parquet(DATA_PATH)
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df["month_year"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


def require_data() -> pd.DataFrame:
    """
    Load the dataset, or explain how to get it and stop the page.
    """

    if not DATA_PATH.exists():
        st.info(
            f"`{DATA_PATH}` was not found. Download the CSV linked in the README into `data/` "
            "and convert it with `development/conv_to_parquet.py`.",
            icon=":material/database_off:",
        )
        st.stop()
    return load_data()


def select_company_range(df: pd.DataFrame) -> Tuple[str, pd.DataFrame]:
    """
    Company picker and month-range slider shared by the hackathon pages.

    :returns: (company name, that company's rows within the selected months)
    """

    with st.container(horizontal=True):
        company = st.selectbox("Company", sorted(df["comp_name"].dropna().unique()),
                               key="hackathon_company")
        df_company = df[df["comp_name"] == company].sort_values("date")
        months = sorted(df_company["month_year"].unique())
        if len(months) > 1:
            start, end = st.select_slider(
                "Months",
                options=months,
                value=(months[0], months[-1]),
                format_func=lambda m: pd.Timestamp(m).strftime("%b %Y"),
            )
        else:
            start = end = months[0]

    selected = df_company[df_company["month_year"].between(start, end)].copy()
    return company, selected
