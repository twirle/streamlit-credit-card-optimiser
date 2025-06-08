import streamlit as st
import pandas as pd


@st.cache_data
def load_data():
    """Load credit card data from CSV"""
    df = pd.read_csv('credit_cards.csv')
    return df


def get_card_categories(card_row):
    """Get categories from the Categories column in CSV"""
    categories = card_row.get('Categories', '')
    if pd.notna(categories) and categories:
        return [cat.strip() for cat in categories.split(',')]
    return ['General']
