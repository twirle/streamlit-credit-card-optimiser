import streamlit as st
import pandas as pd
from ui_components import (
    create_spending_pie_chart,
    display_miles_info,
    create_rewards_chart,
    display_results_table
)


def render_single_card_component(best_cards_summary_df, detailed_results_df, user_spending_data, miles_value_cents):
    """Render the single card analysis component"""

    # Main content layout with meaningful column names
    cards_results_column, spending_summary_column = st.columns([2, 1])

    with cards_results_column:
        st.header("🥇 Top Single Card Recommendations")

        # Display top cards table
        display_results_table(best_cards_summary_df)

        # Rewards comparison chart
        rewards_comparison_chart = create_rewards_chart(
            best_cards_summary_df, miles_value_cents)
        if rewards_comparison_chart:
            st.plotly_chart(rewards_comparison_chart, use_container_width=True)

    with spending_summary_column:
        st.header("📈 Your Spending Profile")

        # Spending breakdown pie chart
        spending_pie_chart = create_spending_pie_chart(user_spending_data)
        if spending_pie_chart:
            st.plotly_chart(spending_pie_chart, use_container_width=True)

        # Miles valuation info
        display_miles_info(miles_value_cents)

        # Best single card recommendation
        display_top_card_recommendation(best_cards_summary_df)

    # Detailed card analysis section
    _render_detailed_card_breakdown(
        best_cards_summary_df, detailed_results_df, user_spending_data)


def display_top_card_recommendation(best_cards_summary_df):
    """Display the top recommended single card"""
    if len(best_cards_summary_df) > 0:
        top_recommended_card = best_cards_summary_df.iloc[0]
        cap_status_indicator = "⚠️ Cap reached" if top_recommended_card[
            'Cap Reached'] else "✅ Under cap"

        st.success(f"""
        **🎯 Best Single Card:**
        
        **{top_recommended_card['Card Name']}** ({top_recommended_card['Issuer']})
        
        🎯 **Categories:** {top_recommended_card['Categories']}
        
        💰 Monthly Value: SGD {top_recommended_card['Monthly Reward']:.2f}
        
        {cap_status_indicator}
        """)


def _render_detailed_card_breakdown(best_cards_summary_df, detailed_results_df, user_spending_data):
    """Render the detailed card calculation breakdown section"""
    st.header("🔍 Detailed Reward Calculations")

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


def display_card_calculation_details(best_tier_data, card_name, all_tiers_data, user_spending_data):
    """Display detailed calculation breakdown for a specific card"""
    calculation_details_column, card_metrics_column = st.columns([3, 1])

    with calculation_details_column:
        st.subheader(f"💳 {card_name}")
        st.write(f"**🎯 Categories:** {best_tier_data['Categories']}")

        # Show tier information if multiple tiers exist
        if len(all_tiers_data) > 1:
            st.info(
                f"**Optimal tier selected:** Min spend ${best_tier_data['Min Spend']} (out of {len(all_tiers_data)} tiers)")

        # Display calculation steps
        for calculation_step in best_tier_data['Details']:
            st.write(f"• {calculation_step}")

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
                **Cap Reached! 🚫**
                
                Monthly cap: ${best_tier_data['Cap']}
                
                Amount over cap: ${best_tier_data['Cap Difference']:.2f}
                
                You're losing ${best_tier_data['Cap Difference']:.2f}/month
                """)
            else:
                st.success(f"""
                **Under Cap ✅**
                
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
