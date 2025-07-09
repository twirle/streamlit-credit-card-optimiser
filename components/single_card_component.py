import streamlit as st
import pandas as pd
import re
from .ui_components import (
    display_miles_info,
    create_rewards_chart,
    display_results_table
)


def render_single_card_component(best_cards_summary_df, detailed_results_df, user_spending_data, miles_value_cents):
    st.header("📑 Top Single Card Recommendations")

    # Generate rewards comparison chart
    rewards_comparison_chart = create_rewards_chart(
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


def display_top_card_recommendation(best_cards_summary_df):
    """Display top card recommendation with enhanced metrics and layout"""
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


def render_detailed_card_breakdown(best_cards_summary_df, detailed_results_df, user_spending_data):
    st.header("🔍 Detailed Reward Analysis")

    # Card selection options
    show_limited_options = st.checkbox("Show only top 5 cards", value=True)

    if show_limited_options:
        available_cards_for_detail = best_cards_summary_df.head(5)[
            'Card Name'].tolist()
    else:
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

        # Find the best performing tier
        best_tier_for_card = selected_card_all_tiers.loc[
            selected_card_all_tiers['Monthly Reward'].idxmax()
        ]

        # Display detailed breakdown
        display_card_calculation_details(
            best_tier_for_card,
            selected_card_for_analysis,
            selected_card_all_tiers,
            user_spending_data
        )


def create_detailed_spending_table(card_name, details):
    rows = []
    for detail in details:
        if ':' not in detail:
            continue
        category_part, rest = detail.split(':', 1)
        category = category_part.strip()

        # Extract amount spent
        amount_match = re.search(r'\$(\d+)', detail)
        amount = int(amount_match.group(1)) if amount_match else 0

        # Extract cashback or mpd rate
        rate_match = re.search(r'×\s*(\d+(?:\.\d+)?)\s*(%| mpd)', detail)
        if rate_match:
            rate_value = rate_match.group(1)
            rate_unit = rate_match.group(2)
            rate = f"{rate_value}{rate_unit}"
        else:
            # Fallback: try without × symbol
            rate_match_fallback = re.search(
                r'(\d+(?:\.\d+)?)\s*(%| mpd)', detail)
            if rate_match_fallback:
                rate_value = rate_match_fallback.group(1)
                rate_unit = rate_match_fallback.group(2)
                rate = f"{rate_value}{rate_unit}"
            else:
                rate = ""

        # Extract reward - handle both cashback and miles formats
        # For cashback: "Dining: $500.00 × 5% = $25.00"
        # For miles: "Dining: $500.00 × 3 mpd = 1500 miles × $0.020 = $30.00"
        reward_match = re.search(r'=\s*\$(\d+\.\d+)$', detail)
        if reward_match:
            reward = float(reward_match.group(1))
        else:
            # Fallback: try to find any dollar amount at the end
            reward_match_fallback = re.search(r'\$(\d+\.\d+)$', detail)
            reward = float(reward_match_fallback.group(
                1)) if reward_match_fallback else 0.0

        rows.append({
            "Category": category,
            "Amount": f"${amount}",
            "Rate": rate,
            "Reward": f"${reward:.2f}"
        })

    df = pd.DataFrame(rows)

    # Add total row if there are any rows
    if not df.empty:
        # Extract numeric values from the formatted strings
        amounts = [int(amount_str.replace("$", ""))
                   for amount_str in df["Amount"]]
        rewards = [float(reward_str.replace("$", ""))
                   for reward_str in df["Reward"]]
        total_amount = sum(amounts)
        total_reward = sum(rewards)

        total_row = pd.DataFrame([{
            "Category": "Total",
            "Amount": f"${total_amount}",
            "Rate": "",
            "Reward": f"${total_reward:.2f}"
        }])

        df = pd.concat([df, total_row], ignore_index=True)

    return df


def display_card_calculation_details(best_tier_data, card_name, all_tiers_data, user_spending_data):
    """Display enhanced card calculation details with better layout"""

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

    # Detailed spending breakdown in expandable section
    with st.expander("📊 Detailed Spending Breakdown", expanded=True):
        df = create_detailed_spending_table(
            card_name, best_tier_data['Details'])
        if not df.empty:
            # Use styled dataframe
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.write("No detailed breakdown available")

        # Show pre-cap amount if different from final
        if best_tier_data['Original Reward'] != best_tier_data['Monthly Reward']:
            st.warning(
                f"**Total before cap:** ${best_tier_data['Original Reward']:.2f}")

    # Card metrics and status in sidebar-like layout
    st.markdown("### 📈 Card Analysis")

    col_metrics1, col_metrics2 = st.columns(2)

    with col_metrics1:
        # Cap status analysis
        cap_val = best_tier_data['Cap']
        cap_str = f"${cap_val:.2f}" if cap_val not in (
            None, 'No Cap', 'N/A') else "No Cap"
        cap_diff = best_tier_data['Cap Difference']
        cap_diff_str = f"${cap_diff:.2f}" if cap_diff is not None else "N/A"
        if cap_val not in (None, 'No Cap', 'N/A'):
            if best_tier_data['Cap Reached']:
                st.error(f"""
                **🚫 Cap Reached!**
                
                Monthly cap: {cap_str}
                
                Amount over cap: {cap_diff_str}
                
                You're losing {cap_diff_str}/month
                """)
            else:
                st.success(f""" 
                **✅ Under Cap**
                
                Monthly cap: {cap_str}
                
                Room to earn: {cap_diff_str}
                """)
        else:
            st.info("**No Cap** - Unlimited earning potential!")

    with col_metrics2:
        # Minimum spend analysis
        min_spend_val = best_tier_data['Min Spend']
        min_spend_str = f"${min_spend_val:.2f}" if min_spend_val not in (
            None, 'N/A') else "N/A"
        if not best_tier_data['Min Spend Met']:
            need_more = min_spend_val - \
                user_spending_data['total'] if min_spend_val not in (
                    None, 'N/A') else None
            need_more_str = f"${need_more:.2f}" if need_more is not None else "N/A"
            st.warning(f"""
            **Minimum Spend Not Met ⚠️**
            
            Required: {min_spend_str}
            
            Your spend: ${user_spending_data['total']}
            
            Need {need_more_str} more
            """)
        else:
            st.success("**✅ Minimum spend requirement met**")

    st.markdown("---")
