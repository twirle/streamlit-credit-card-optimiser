import streamlit as st
import pandas as pd
import re
from ui_components import (
    display_miles_info,
    create_rewards_chart,
    display_results_table
)


def render_single_card_component(best_cards_summary_df, detailed_results_df, user_spending_data, miles_value_cents):
    st.header("📑 Top Single Card Recommendations")

    # Generate rewards comparison chart
    rewards_comparison_chart = create_rewards_chart(
        best_cards_summary_df, miles_value_cents)

    # Display top cards table
    display_results_table(best_cards_summary_df)

    left_col, right_col = st.columns([5, 2])

    with left_col:
        # Display rewards comparison chart
        if rewards_comparison_chart:
            st.plotly_chart(rewards_comparison_chart, use_container_width=True)

    # Best single card recommendation
    display_top_card_recommendation(best_cards_summary_df)

    # Detailed card analysis section
    render_detailed_card_breakdown(
        best_cards_summary_df, detailed_results_df, user_spending_data)


def display_top_card_recommendation(best_cards_summary_df):
    if len(best_cards_summary_df) > 0:
        top_recommended_card = best_cards_summary_df.iloc[0]
        cap_status_indicator = "🚫 Cap reached" if top_recommended_card[
            'Cap Reached'] else "✅ Under cap"

        st.success(f"""
        **💰 Best Single Card:**
        
        **{top_recommended_card['Card Name']}** ({top_recommended_card['Issuer']})
        
        **Categories:** {top_recommended_card['Categories']}
        
        **Monthly Value**: SGD {top_recommended_card['Monthly Reward']:.2f}
        
        {cap_status_indicator}
        """)


def render_detailed_card_breakdown(best_cards_summary_df, detailed_results_df, user_spending_data):
    st.header("🔍 Detailed Reward Analysis")

    # Card selection options
    show_limited_options = st.checkbox("Show only top 5 cards", value=True)

    if show_limited_options:
        available_cards_for_detail = best_cards_summary_df.head(5)[
            'Card Name'].tolist()
    else:
        available_cards_for_detail = best_cards_summary_df['Card Name'].tolist(
        )

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

        # Extract reward
        reward_match = re.search(r'=\s*(\d+\.\d+)', detail)
        reward = float(reward_match.group(1)) if reward_match else 0.0

        rows.append({
            "Category": category,
            "Amount": f"${amount}",
            "Rate": rate,
            "Reward": f"${reward:.2f}"
        })

    df = pd.DataFrame(rows)

    # Add total row if there are any rows
    if not df.empty:
        total_amount = sum(int(row["Amount"].replace("$", ""))
                           for _, row in df.iterrows())
        total_reward = sum(float(row["Reward"].replace("$", ""))
                           for _, row in df.iterrows())

        total_row = pd.DataFrame([{
            "Category": "Total",
            "Amount": f"${total_amount}",
            "Rate": "",
            "Reward": f"${total_reward:.2f}"
        }])

        df = pd.concat([df, total_row], ignore_index=True)

    return df


def display_card_calculation_details(best_tier_data, card_name, all_tiers_data, user_spending_data):
    calculation_details_column, card_metrics_column = st.columns([3, 1])

    with calculation_details_column:
        st.subheader(f"💳 {card_name}")
        st.write(f"**🎯 Categories:** {best_tier_data['Categories']}")

        # Show tier information if multiple tiers exist
        if len(all_tiers_data) > 1:
            st.info(
                f"**Optimal tier selected:** Min spend ${best_tier_data['Min Spend']} (out of {len(all_tiers_data)} tiers)")

        # Detailed spending breakdown table
        st.write("### 📊 Detailed Spending Breakdown")
        df = create_detailed_spending_table(
            card_name, best_tier_data['Details'])
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.write("No detailed breakdown available")

        # Show pre-cap amount if different from final
        if best_tier_data['Original Reward'] != best_tier_data['Monthly Reward']:
            st.write(
                f"**Total before cap:** ${best_tier_data['Original Reward']:.2f}")

        st.write(
            f"**Final monthly reward:** ${best_tier_data['Monthly Reward']:.2f}")

    with card_metrics_column:
        # Cap status analysis
        if pd.notna(best_tier_data['Cap']) and best_tier_data['Cap'] != 'No Cap':
            if best_tier_data['Cap Reached']:
                st.error(f"""
                **🚫 Cap Reached!**
                
                Monthly cap: ${best_tier_data['Cap']}
                
                Amount over cap: ${best_tier_data['Cap Difference']:.2f}
                
                You're losing ${best_tier_data['Cap Difference']:.2f}/month
                """)
            else:
                st.success(f"""
                **✅ Under Cap**
                
                Monthly cap: ${best_tier_data['Cap']}
                
                Room to earn: ${best_tier_data['Cap Difference']:.2f}
                """)
        else:
            st.info("**No Cap** - Unlimited earning potential!")

        if not best_tier_data['Min Spend Met']:
            st.warning(f"""
            **Minimum Spend Not Met ⚠️**
            
            Required: ${best_tier_data['Min Spend']}
            
            Your spend: ${user_spending_data['total']}
            
            Need ${best_tier_data['Min Spend'] - user_spending_data['total']} more
            """)
