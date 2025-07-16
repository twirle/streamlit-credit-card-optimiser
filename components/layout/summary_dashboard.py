"""
Summary Dashboard Component

This module handles the summary dashboard layout including
key metrics, insights, and spending breakdown.
"""

import streamlit as st
import pandas as pd
from ..charts.rewards_chart import create_spending_breakdown_chart


def display_miles_info(miles_value_cents: float):
    """
    Display miles valuation information

    Args:
        miles_value_cents: Miles value in cents
    """
    return st.info(f"""
    **Miles Valuation Guide:**
    • Economy flights: 1.5-2.5¢
    • Business class: 3-6¢  
    • First class: 6-8¢+
    • Currently using: **{miles_value_cents:.1f}¢** per mile
    """)


def create_summary_metrics(user_spending_data: dict, best_cards_summary_df: pd.DataFrame, combinations_df: pd.DataFrame | None = None):
    """
    Create summary metrics section with single card and multi-card strategy comparison

    Args:
        user_spending_data: Dictionary with spending data
        best_cards_summary_df: DataFrame with best cards
        combinations_df: DataFrame with combination results (optional)
    """
    # Determine if we have combination data
    has_combinations = combinations_df is not None and not combinations_df.empty

    if has_combinations:
        # Show both single and multi-card metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Monthly Spending",
                f"${user_spending_data['total']:,}",
                help="Your total monthly spending across all categories"
            )

        with col2:
            if len(best_cards_summary_df) > 0:
                best_single_reward = best_cards_summary_df.iloc[0]['Monthly Reward']
                best_combination_reward = combinations_df.iloc[0]['Monthly Reward']
                improvement = best_combination_reward - best_single_reward

                st.metric(
                    "Best Strategy Reward",
                    f"${best_combination_reward:.2f}",
                    delta=f"+${improvement:.2f}" if improvement > 0 else f"${improvement:.2f}",
                    delta_color="normal" if improvement > 0 else "inverse",
                    help="Best monthly reward (single card vs multi-card strategy)"
                )
            else:
                st.metric("Best Strategy Reward", "$0.00")

        with col3:
            if len(best_cards_summary_df) > 0:
                best_annual = combinations_df.iloc[0]['Monthly Reward'] * 12
                st.metric(
                    "Best Annual Reward",
                    f"${best_annual:.2f}",
                    help="Annual reward from the best strategy"
                )
            else:
                st.metric("Best Annual Reward", "$0.00")

        with col4:
            if len(best_cards_summary_df) > 0 and user_spending_data['total'] > 0:
                reward_rate = (
                    combinations_df.iloc[0]['Monthly Reward'] / user_spending_data['total']) * 100
                st.metric(
                    "Reward Rate",
                    f"{reward_rate:.1f}%",
                    help="Reward as percentage of total spending"
                )
            else:
                st.metric("Reward Rate", "0.0%")

        # Add strategy comparison section
        st.markdown("### 🎯 **Strategy Comparison**")
        strategy_col1, strategy_col2 = st.columns(2)

        with strategy_col1:
            if len(best_cards_summary_df) > 0:
                best_single_reward = best_cards_summary_df.iloc[0]['Monthly Reward']
                best_single_name = best_cards_summary_df.iloc[0]['Card Name']
                st.info(f"""
                **💳 Best Single Card:**
                **{best_single_name}**

                Monthly: ${best_single_reward:.2f}

                Annual: ${best_single_reward * 12:.2f}
                """)

        with strategy_col2:
            if has_combinations:
                best_combination = combinations_df.iloc[0]
                best_combination_reward = best_combination['Monthly Reward']
                improvement = best_combination_reward - best_single_reward

                if improvement > 0:
                    st.success(f"""
                    **🔗 Best Multi-Card Strategy:**
                    **{best_combination['Card Name']}**

                    Monthly: $ {best_combination_reward:.2f}

                    Annual: $ {best_combination_reward * 12:.2f}

                    **Improvement: +${improvement:.2f}/month**
                    """)
                else:
                    st.info(f"""
                    **🔗 Multi-Card Strategy:**
                    **{best_combination['Card Name']}**

                    Monthly: ${best_combination_reward:.2f}

                    Annual: ${best_combination_reward * 12:.2f}
                    
                    **Single card is better**
                    """)

    else:
        # Show only single card metrics (original behavior)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Monthly Spending",
                f"${user_spending_data['total']:,}",
                help="Your total monthly spending across all categories"
            )

        with col2:
            if len(best_cards_summary_df) > 0:
                best_reward = best_cards_summary_df.iloc[0]['Monthly Reward']
                st.metric(
                    "Best Monthly Reward",
                    f"${best_reward:.2f}",
                    help="Highest monthly reward from any single card"
                )
            else:
                st.metric("Best Monthly Reward", "$0.00")

        with col3:
            if len(best_cards_summary_df) > 0:
                best_annual = best_cards_summary_df.iloc[0]['Monthly Reward'] * 12
                st.metric(
                    "Best Annual Reward",
                    f"${best_annual:.2f}",
                    help="Annual reward from the best single card"
                )
            else:
                st.metric("Best Annual Reward", "$0.00")

        with col4:
            if len(best_cards_summary_df) > 0 and user_spending_data['total'] > 0:
                reward_rate = (
                    best_cards_summary_df.iloc[0]['Monthly Reward'] / user_spending_data['total']) * 100
                st.metric(
                    "Reward Rate",
                    f"{reward_rate:.1f}%",
                    help="Reward as percentage of total spending"
                )
            else:
                st.metric("Reward Rate", "0.0%")


def create_spending_insights(user_spending_data: dict, best_cards_summary_df: pd.DataFrame, miles_value_cents: float):
    """
    Create spending insights section

    Args:
        user_spending_data: Dictionary with spending data
        best_cards_summary_df: DataFrame with best cards
        miles_value_cents: Miles value in cents
    """
    st.markdown("### 💡 **Key Insights**")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        # Top spending category
        spending_categories = {
            'Dining': user_spending_data['dining'],
            'Groceries': user_spending_data['groceries'],
            'Petrol': user_spending_data['petrol'],
            'Transport': user_spending_data['transport'],
            'Streaming': user_spending_data['streaming'],
            'Entertainment': user_spending_data['entertainment'],
            'Utilities': user_spending_data['utilities'],
            'Online': user_spending_data['online'],
            'Travel': user_spending_data['travel'],
            'Overseas': user_spending_data['overseas'],
            'Retail': user_spending_data['retail'],
            'Departmental': user_spending_data['departmental'],
            'Other': user_spending_data['other']
        }

        # Filter out zero spending categories
        spending_categories = {k: v for k,
                               v in spending_categories.items() if v > 0}

        if spending_categories:
            top_category = max(spending_categories.keys(),
                               key=lambda k: spending_categories[k])
            top_amount = spending_categories[top_category]
            st.info(f"**Highest spending:** {top_category} (${top_amount:,})")

        # Spending level insight
        total_spending = user_spending_data['total']
        if total_spending < 800:
            st.warning(
                "**Low spender:** Consider cards with no minimum spend requirements")
        elif total_spending < 1500:
            st.info("**Medium spender:** You can access most card tiers")
        else:
            st.success(
                "**High spender:** You can maximize rewards with premium cards")

    with insights_col2:
        # Miles valuation insight
        if miles_value_cents <= 2.5:
            st.info("**Miles value:** Economy flights range - good for budget travel")
        elif miles_value_cents <= 6.0:
            st.info("**Miles value:** Business class range - premium travel benefits")
        else:
            st.info("**Miles value:** First class range - luxury travel rewards")

        # Card type recommendation
        if not best_cards_summary_df.empty:
            best_card_type = best_cards_summary_df.iloc[0]['Card Type']
            if best_card_type == 'Miles':
                st.info('✈️ You are likely to benefit most from a miles card.')
            else:
                st.info('💵 You are likely to benefit most from a cashback card.')


def create_summary_dashboard(user_spending_data: dict, best_cards_summary_df: pd.DataFrame, miles_value_cents: float, combinations_df: pd.DataFrame | None = None):
    """
    Create a summary dashboard with key metrics and insights

    Args:
        user_spending_data: Dictionary with spending data
        best_cards_summary_df: DataFrame with best cards
        miles_value_cents: Miles value in cents
        combinations_df: DataFrame with combination results (optional)
    """
    st.markdown("### 📊 **Spending & Rewards Summary**")

    # Key metrics in a grid layout
    create_summary_metrics(
        user_spending_data, best_cards_summary_df, combinations_df)

    # Spending breakdown chart in expandable
    with st.expander("💰 Spending Breakdown", expanded=False):
        # Insights section
        create_spending_insights(
            user_spending_data, best_cards_summary_df, miles_value_cents)

        # Create spending breakdown chart
        spending_chart = create_spending_breakdown_chart(user_spending_data)
        if spending_chart:
            st.plotly_chart(spending_chart, use_container_width=True)
        else:
            st.info("No spending data available to display.")
