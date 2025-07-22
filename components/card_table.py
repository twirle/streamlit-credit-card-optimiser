from altair import Column
import streamlit as st
from services.data.card_loader import load_card_dataframes
import pandas as pd


def render_card_table():
    """
    Display tables of all credit cards, split into Cashback and Miles tabs, in an expander.
    Only unique cards (by Name, Issuer, Type) are shown (no tier duplicates).
    Columns: Name, Issuer, Type, Income Requirement, Categories
    """
    dfs = load_card_dataframes()
    df = dfs["Cards DataFrame"].copy()

    # Only keep the required columns, handle missing gracefully
    columns = ["Name", "Issuer", "Type", "Income Requirement", "Categories"]
    available_cols = [col for col in columns if col in df.columns]
    df = df[available_cols]

    # Drop duples
    df = df.drop_duplicates(subset=[col for col in [
                            "Name", "Issuer", "Type"] if col in df.columns], keep="first").reset_index(drop=True)

    # Format 'Income Requirement' as int with commas
    if "Income Requirement" in df.columns:
        df["Income Requirement"] = df["Income Requirement"].apply(
            lambda x: f"${int(x):,}" if pd.notnull(x) and x != '' else "-")

    # Format 'Categories' as comma-separated string
    if "Categories" in df.columns:
        df["Categories"] = df["Categories"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else str(x))

    cashback_df = df[df["Type"].str.lower(
    ) == "cashback"].reset_index(drop=True)

    miles_df = df[df["Type"].str.lower() == "miles"].reset_index(drop=True)

    st.markdown("**💳Current list of supported cards**:")
    cashback_tab, miles_tab = st.tabs(["Cashback Cards", "Miles Cards"])

    with cashback_tab:
        st.dataframe(cashback_df, use_container_width=True,
                     column_config={
                         "Name": st.column_config.Column(width="medium"),
                         "Issuer": st.column_config.Column(width="small"),
                         "Type": st.column_config.Column(width="small"),
                         "Income Requirement": st.column_config.Column(width="small"),
                         "Categories": st.column_config.Column(width="large"),
                     })

    with miles_tab:
        st.dataframe(miles_df, use_container_width=True,
                     column_config={
                         "Name": st.column_config.Column(width="medium"),
                         "Issuer": st.column_config.Column(width="small"),
                         "Type": st.column_config.Column(width="small"),
                         "Income Requirement": st.column_config.Column(width="small"),
                         "Categories": st.column_config.Column(width="large"),
                     })
