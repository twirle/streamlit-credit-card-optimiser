"""
Card Recommendation Component

This module handles card recommendation display including
top card recommendations and detailed analysis.
"""

import streamlit as st
import pandas as pd
from typing import List
import numpy as np

from ..tables import create_detailed_spending_table


def display_detailed_spending_breakdown_simple(details: List[str], card_name: str):
    """
    Display detailed spending breakdown in an expandable container with simple table

    Args:
        details: List of detail strings from reward calculation
        card_name: Name of the card
    """
    if not details:
        st.info("No detailed breakdown available for this card.")
        return

    with st.expander("📋 Detailed Spending Breakdown", expanded=False):
        st.write(f"**{card_name} Breakdown**")

        # Create the detailed spending table using the existing function
        df = create_detailed_spending_table(card_name, details)

        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.write("No spending details available for this card")


def display_top_card_recommendation(best_cards_summary_df: pd.DataFrame):
    """
    Display top card recommendation with enhanced metrics and layout

    Args:
        best_cards_summary_df: DataFrame with best cards
    """
    if len(best_cards_summary_df) > 0:
        top_recommended_card = best_cards_summary_df.iloc[0]

        # Create a container for the recommendation
        with st.container():
            st.markdown("---")
            st.subheader("🏆 **Best Single Card Recommendation**")

            # Use columns for better layout
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"""
                **💳 {top_recommended_card['Card Name']}**  
                **🏦 {top_recommended_card['Issuer']}**
                
                **🎯 Categories:** {top_recommended_card['Categories']}
                """)

            with col2:
                # Monthly reward metric
                st.metric(
                    label="Monthly Reward",
                    value=f"${top_recommended_card['Monthly Reward']:.2f}",
                    delta=None
                )

            with col3:
                # Annual reward metric
                annual_reward = top_recommended_card['Monthly Reward'] * 12
                st.metric(
                    label="Annual Reward",
                    value=f"${annual_reward:.2f}",
                    delta=None
                )

            # Cap status with better styling
            if top_recommended_card['Cap Reached']:
                st.error(
                    "🚫 **Cap Reached** - You're hitting the monthly spending limit")
            else:
                st.success("✅ **Under Cap** - You have room to earn more")

            st.markdown("---")


def display_card_calculation_details(best_tier_data: pd.Series, card_name: str, all_tiers_data: pd.DataFrame, user_spending_data: dict):
    """
    Display enhanced card calculation details with better layout

    Args:
        best_tier_data: Series with best tier data
        card_name: Name of the card
        all_tiers_data: DataFrame with all tiers for the card
        user_spending_data: Dictionary with user spending data
    """
    # Header with card info
    st.markdown("---")
    st.subheader(f"💳 {card_name}")

    # Card overview in columns
    col_overview1, col_overview2, col_overview3 = st.columns([2, 1, 1])

    with col_overview1:
        st.markdown(f"**🏦 Issuer:** {best_tier_data['Issuer']}")
        st.markdown(f"**🎯 Categories:** {best_tier_data['Categories']}")

        # Show tier information if multiple tiers exist
        if len(all_tiers_data) > 1:
            min_spend_val = best_tier_data['Min Spend']
            min_spend_str = f"${min_spend_val:.2f}" if min_spend_val not in (
                None, 'N/A') else "N/A"
            st.info(
                f"**Optimal tier selected:** Min spend {min_spend_str} (out of {len(all_tiers_data)} tiers)")

    with col_overview2:
        st.metric(
            "Monthly Reward",
            f"${best_tier_data['Monthly Reward']:.2f}",
            delta=None
        )

    with col_overview3:
        annual_reward = best_tier_data['Monthly Reward'] * 12
        st.metric(
            "Annual Reward",
            f"${annual_reward:.2f}",
            delta=None
        )

    # Display detailed spending breakdown
    details = best_tier_data.get('Details', None)
    # Robustly convert details to a list of strings
    if details is not None:
        if isinstance(details, (pd.Series, np.ndarray)):
            details = details.tolist()
        if isinstance(details, str):
            details = [details]
        if isinstance(details, list) and len(details) > 0:
            display_detailed_spending_breakdown_simple(details, card_name)
    st.markdown("---")


def render_detailed_card_breakdown(best_cards_summary_df: pd.DataFrame, detailed_results_df: pd.DataFrame, user_spending_data: dict):
    """
    Render detailed card breakdown section

    Args:
        best_cards_summary_df: DataFrame with best cards
        detailed_results_df: DataFrame with detailed results
        user_spending_data: Dictionary with user spending data
    """
    st.subheader("🔍 Detailed Reward Analysis")

    # Show all unique card names from detailed_results_df
    available_cards_for_detail = detailed_results_df['Card Name'].unique(
    ).tolist()

    selected_card_for_analysis = st.selectbox(
        "Select a card to see detailed calculation:",
        options=available_cards_for_detail,
        index=0,
        help="Select a card to view detailed reward calculation breakdown"
    )

    if selected_card_for_analysis:
        # Get all tiers for the selected card
        selected_card_all_tiers = detailed_results_df[
            detailed_results_df['Card Name'] == selected_card_for_analysis
        ]
        # Ensure it's a DataFrame
        if isinstance(selected_card_all_tiers, pd.Series):
            selected_card_all_tiers = selected_card_all_tiers.to_frame().T

        # Find the best performing tier
        if not selected_card_all_tiers.empty:
            idx = selected_card_all_tiers['Monthly Reward'].astype(
                float).idxmax()
            best_tier_for_card = selected_card_all_tiers.loc[idx]
            # Display detailed breakdown
            display_card_calculation_details(
                best_tier_for_card,
                selected_card_for_analysis,
                selected_card_all_tiers,
                user_spending_data
            )
