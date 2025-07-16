"""
Filters Component

This module handles all filtering functionality including card type filters
and other user selection controls.
"""

import streamlit as st
import pandas as pd


def create_card_type_filter(df: pd.DataFrame) -> list:
    """
    Create filters for card types
    
    Args:
        df: DataFrame containing card data
        
    Returns:
        List of selected card types
    """
    filter_option = st.sidebar.selectbox(
        "Select Card Type:",
        options=["All Cards", "Miles Only", "Cashback Only"],
        index=0
    )

    if filter_option == "All Cards":
        # Handle both column naming conventions
        if 'Card Type' in df.columns:
            card_types = df['Card Type'].unique().tolist()
        elif 'card_type' in df.columns:
            card_types = df['card_type'].unique().tolist()
        else:
            card_types = ["Miles", "Cashback"]
    elif filter_option == "Miles Only":
        card_types = ["Miles"]
    else:  # "Cashback Only"
        card_types = ["Cashback"]

    return card_types


def create_filters(df: pd.DataFrame) -> list:
    """
    Create all filters for the application
    
    Args:
        df: DataFrame containing card data
        
    Returns:
        List of selected card types
    """
    return create_card_type_filter(df) 