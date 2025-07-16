"""
Refactored Combination Card Component

This module provides the multi-card combination analysis functionality using
the new modular component structure.
"""

import streamlit as st
import pandas as pd

from services.rewards_service import get_rewards_service
from .charts import create_strategy_comparison_chart
from .tables import (
    display_combination_results_table,
    display_spending_allocation_table,
    create_detailed_spending_table
)


def render_combination_component(selected_cards_df: pd.DataFrame, best_single_cards_df: pd.DataFrame,
                                 card_results_df: pd.DataFrame, user_spending_data: dict,
                                 miles_to_sgd_rate: float, miles_value_cents: float):
    """
    Render the combination analysis component

    Args:
        selected_cards_df: DataFrame with selected cards
        best_single_cards_df: DataFrame with best single cards
        card_results_df: DataFrame with card results
        user_spending_data: Dictionary with user spending data
        miles_to_sgd_rate: Miles to SGD conversion rate
        miles_value_cents: Miles value in cents
    """
    st.subheader("🔗 Optimize with Multi-Card Strategy")
    st.write(
        "Find the best two-card combination to maximize rewards while avoiding caps.")

    # Get rewards service
    rewards_service = get_rewards_service()

    # Calculate card combinations
    card_combinations_results = rewards_service.find_best_card_combinations(
        selected_cards_df, user_spending_data, miles_to_sgd_rate, card_results_df
    )

    if card_combinations_results:
        # Organize combination data
        combinations_summary_df = pd.DataFrame(card_combinations_results)
        combinations_summary_df = combinations_summary_df.sort_values(
            'Monthly Reward', ascending=False)

        # Get best single card for comparison
        best_single_card_reward = best_single_cards_df.iloc[0]['Monthly Reward']
        best_single_card_name = best_single_cards_df.iloc[0]['Card Name']

        # Display combination results
        display_combination_strategies(
            combinations_summary_df,
            best_single_card_reward,
            best_single_card_name,
            miles_value_cents
        )

        # Show detailed combination breakdown
        render_combination_details(
            combinations_summary_df,
            selected_cards_df,
            user_spending_data,
            miles_to_sgd_rate,
            best_single_card_reward
        )

    else:
        st.info("No beneficial two-card combinations found for your spending pattern.")
        st.write(
            f"**Best single card:** {best_single_cards_df.iloc[0]['Card Name']} - ${best_single_cards_df.iloc[0]['Monthly Reward']:.2f}/month")


def display_combination_strategies(combinations_df: pd.DataFrame, best_single_reward: float,
                                   best_single_name: str, miles_value_cents: float):
    """
    Display combination strategies with comparison to best single card

    Args:
        combinations_df: DataFrame with combinations
        best_single_reward: Best single card reward
        best_single_name: Name of best single card
        miles_value_cents: Miles value in cents
    """
    # Always show all combinations in a scrollable table
    display_combination_results_table(combinations_df, best_single_reward)

    st.text('a')

    # Comparison chart (show top 10)
    if len(combinations_df) > 0:
        strategy_comparison_chart = create_strategy_comparison_chart(
            combinations_df, best_single_reward, best_single_name
        )
        st.plotly_chart(strategy_comparison_chart, use_container_width=True)

    # Display optimization results
    display_optimization_summary(
        combinations_df, best_single_reward, best_single_name)


def display_optimization_summary(combinations_df: pd.DataFrame, best_single_reward: float, best_single_name: str):
    """
    Display optimization summary

    Args:
        combinations_df: DataFrame with combinations
        best_single_reward: Best single card reward
        best_single_name: Name of best single card
    """
    if len(combinations_df) > 0:
        optimal_combination = combinations_df.iloc[0]
        reward_improvement = optimal_combination['Monthly Reward'] - \
            best_single_reward

        if reward_improvement > 0:
            st.success(f"""
            **💰 Optimal Strategy: {optimal_combination['Card Name']}**
            
             **Monthly Reward**: ${optimal_combination['Monthly Reward']:.2f}
            
            **Improvement**: +${reward_improvement:.2f}/month vs best single card
            
            **Annual Benefit**: +${reward_improvement * 12:.2f}/year
            """)
        else:
            st.info(f"""
            **🎯 Best Single Card is Still Optimal**
            
            **{best_single_name}** at ${best_single_reward:.2f}/month
            
            No significant benefit from combinations with your spending pattern.
            """)


def render_combination_details(combinations_df: pd.DataFrame, selected_cards_df: pd.DataFrame,
                               user_spending_data: dict, miles_to_sgd_rate: float, best_single_reward: float):
    """
    Render detailed combination analysis

    Args:
        combinations_df: DataFrame with combinations
        selected_cards_df: DataFrame with selected cards
        user_spending_data: Dictionary with user spending data
        miles_to_sgd_rate: Miles to SGD conversion rate
        best_single_reward: Best single card reward
    """
    st.subheader("🔍 Detailed Multi-Card Rewards Analysis")

    # Show all combinations
    available_combinations_for_detail = combinations_df['Card Name'].tolist()

    selected_combination_name = st.selectbox(
        "Select a combination to analyze:",
        options=available_combinations_for_detail,
        index=0,
        help="Select a combination to view detailed reward calculation breakdown"
    )

    if selected_combination_name:
        selected_combination_data = combinations_df[
            combinations_df['Card Name'] == selected_combination_name
        ].iloc[0]

        display_combination_breakdown(
            selected_combination_data,
            selected_combination_name,
            selected_cards_df,
            user_spending_data,
            miles_to_sgd_rate,
            best_single_reward
        )


def display_combination_breakdown(combination_data: pd.Series, combination_name: str,
                                  selected_cards_df: pd.DataFrame, user_spending_data: dict,
                                  miles_to_sgd_rate: float, best_single_reward: float):
    """
    Display detailed combination breakdown

    Args:
        combination_data: Series with combination data
        combination_name: Name of the combination
        selected_cards_df: DataFrame with selected cards
        user_spending_data: Dictionary with user spending data
        miles_to_sgd_rate: Miles to SGD conversion rate
        best_single_reward: Best single card reward
    """
    # Get rewards service
    rewards_service = get_rewards_service()

    breakdown_details_column, combination_metrics_column = st.columns([3, 1])

    with breakdown_details_column:
        st.subheader(f"💳 {combination_name}")
        st.write(f"**🎯 Categories:** {combination_data['Categories']}")

        # Parse combination to get individual cards
        individual_card_names = combination_name.split(' + ')

        if len(individual_card_names) == 2:
            # Get card data and calculate detailed breakdown
            first_card_data = selected_cards_df[selected_cards_df['Card Name']
                                                == individual_card_names[0]].iloc[0]
            second_card_data = selected_cards_df[selected_cards_df['Card Name']
                                                 == individual_card_names[1]].iloc[0]

            detailed_combination_result = rewards_service.combine_two_cards_rewards(
                first_card_data.to_dict(), second_card_data.to_dict(
                ), user_spending_data, miles_to_sgd_rate
            )

            # Enhanced displays
            display_spending_allocation_table(
                detailed_combination_result['allocation'], individual_card_names, selected_cards_df)

            display_detailed_breakdown_expandable(
                detailed_combination_result['allocation'],
                individual_card_names,
                detailed_combination_result
            )

    with combination_metrics_column:
        monthly, annual = st.columns(2)
        with monthly:
            st.metric(
                label="Total Monthly Reward",
                value=f"${combination_data['Monthly Reward']:.2f}"
            )
        with annual:
            st.metric(
                label="Total Annual Reward",
                value=f"${combination_data['Monthly Reward'] * 12:.2f}"
            )

        # Compare with best single card
        reward_improvement = combination_data['Monthly Reward'] - \
            best_single_reward
        if reward_improvement > 0:
            st.success(f"""
            **Better than Single Card! ✅**
            
            Best single: ${best_single_reward:.2f}
            
            Improvement: +${reward_improvement:.2f}/month
            
            Annual benefit: +${reward_improvement * 12:.2f}/year
            """)
        else:
            st.info(f"""
            **Single Card Better**
            
            Best single: ${best_single_reward:.2f}
            
            Difference: ${reward_improvement:.2f}/month
            """)

        st.info("**No Caps Reached** - Combination optimized to avoid caps!")


def display_detailed_breakdown_expandable(allocation_data: dict, card_names: list, detailed_result: dict):
    """
    Display detailed breakdown using containers instead of columns

    Args:
        allocation_data: Dictionary with allocation data
        card_names: List of card names
        detailed_result: Dictionary with detailed results
    """
    with st.expander("📋 Detailed Spending Breakdown", expanded=False):

        # Display breakdown for each card
        for card_name, card_data in allocation_data.items():
            with st.container():
                st.write(f"**{card_name} Breakdown**")
                if card_data['details']:
                    df = create_detailed_spending_table(
                        card_name, card_data['details'])
                    if not df.empty:
                        st.dataframe(df, use_container_width=True,
                                     hide_index=True)
                    else:
                        st.write("No spending details available for this card")
                else:
                    st.write("No spending details available for this card")

            st.markdown("---")
