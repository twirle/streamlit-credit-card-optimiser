import streamlit as st
from services.data.card_loader import load_card_dataframes

st.set_page_config(page_title="DataFrames Viewer", layout="wide")
st.title("🔍 DataFrames Viewer")

# Load all card-related DataFrames
card_dfs = load_card_dataframes()

for name, df in card_dfs.items():
    st.subheader(f"{name}")
    st.dataframe(df, use_container_width=True, hide_index=False)
