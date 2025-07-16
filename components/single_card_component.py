"""
Refactored Single Card Component

This module provides the single card analysis functionality using
the new modular component structure.
"""

import streamlit as st
import pandas as pd

from .charts import create_rewards_comparison_chart
from .tables import display_results_table
from .cards import (
    display_top_card_recommendation,
    render_detailed_card_breakdown
)


def render_single_card_component(best_cards_summary_df: pd.DataFrame, detailed_results_df: pd.DataFrame,
                                 user_spending_data: dict, miles_value_cents: float):
    """
    Render the single card analysis component

    Args:
        best_cards_summary_df: DataFrame with best cards
        detailed_results_df: DataFrame with detailed results
        user_spending_data: Dictionary with user spending data
        miles_value_cents: Miles value in cents
    """
    st.subheader("📑 Top Single Card Recommendations")

    # Generate rewards comparison chart
    rewards_comparison_chart = create_rewards_comparison_chart(
        best_cards_summary_df, miles_value_cents)

    # Display top cards table - use detailed_results_df for pagination
    display_results_table(detailed_results_df)

    # Display rewards comparison chart
    if rewards_comparison_chart:
        st.plotly_chart(rewards_comparison_chart, use_container_width=True)

    # Best single card recommendation
    display_top_card_recommendation(best_cards_summary_df)

    # Detailed card analysis section
    render_detailed_card_breakdown(
        best_cards_summary_df, detailed_results_df, user_spending_data)
