import streamlit as st
import pandas as pd

# Import custom modules
from services.data_loader import get_data_loader
from services.calculations import get_reward_calculator
from models.credit_card_model import UserSpending
from components.ui_components import create_spending_inputs, create_filters, create_summary_dashboard
from components.single_card_component import render_single_card_component
from components.combination_card_component import render_combination_component

# Page config
st.set_page_config(
    page_title="Singapore Credit Card Reward Optimizer",
    page_icon="💳",
    layout="wide"
)


def convert_spending_to_model(spending_dict: dict) -> UserSpending:
    """Convert spending dictionary to UserSpending model"""
    return UserSpending(
        dining=spending_dict.get('dining', 0.0),
        groceries=spending_dict.get('groceries', 0.0),
        petrol=spending_dict.get('petrol', 0.0),
        transport=spending_dict.get('transport', 0.0),
        streaming=spending_dict.get('streaming', 0.0),
        entertainment=spending_dict.get('entertainment', 0.0),
        utilities=spending_dict.get('utilities', 0.0),
        online=spending_dict.get('online', 0.0),
        travel=spending_dict.get('travel', 0.0),
        overseas=spending_dict.get('overseas', 0.0),
        retail=spending_dict.get('retail', 0.0),
        departmental=spending_dict.get('departmental', 0.0),
        other=spending_dict.get('other', 0.0)
    )


def convert_results_to_dataframe(results: list, cards_df: pd.DataFrame, card_categories_df: pd.DataFrame, tiers_df: pd.DataFrame, rates_df: pd.DataFrame) -> pd.DataFrame:
    """Convert reward calculation results to DataFrame for display, including card_type, Issuer, Categories, Cap, and Min Spend."""
    if not results:
        return pd.DataFrame()

    data = []
    for result in results:
        # Lookup card_type and issuer by card name
        card_type = None
        issuer = None
        categories = None
        cap = 'No Cap'
        min_spend = None
        
        # Use consistent Title Case column names
        match = cards_df[cards_df['Card Name'] == result.card_name]
        if not match.empty:
            card_type = match.iloc[0]['Card Type']
            issuer = match.iloc[0]['Issuer']
            card_id = match.iloc[0]['card_id']
            # Lookup categories for this card_id
            cat_rows = card_categories_df[card_categories_df['card_id'] == card_id]
            categories = ', '.join(pd.Series(cat_rows['category']).unique()) if not cat_rows.empty else ''
            # Lookup tier by tier description (result.tier_description)
            tier_row = tiers_df[(tiers_df['card_id'] == card_id) & (tiers_df['Description'] == result.tier_description)]
            if tier_row.empty:
                # fallback: if only one tier, use it
                tier_row = tiers_df[tiers_df['card_id'] == card_id]
            if not tier_row.empty:
                tier_id = tier_row.iloc[0]['tier_id']
                min_spend = tier_row.iloc[0]['Min Spend']
                # Find max cap for this tier in rates_df
                tier_rates = rates_df[rates_df['tier_id'] == tier_id]
                cap_values = pd.Series(tier_rates['Cap Amount']).dropna().unique()
                if len(cap_values) > 0:
                    # Use the max cap value for display
                    cap = max(cap_values)
        data.append({
            'Card Name': result.card_name,
            'Tier': result.tier_description,
            'Monthly Reward': result.monthly_reward,
            'Cap Reached': result.cap_reached,
            'Cap Difference': result.cap_difference,
            'Min Spend Met': result.min_spend_met,
            'Details': result.details,
            'Card Type': card_type,
            'Issuer': issuer,
            'Categories': categories,
            'Original Reward': result.original_reward,
            'Cap': cap,
            'Min Spend': min_spend
        })

    return pd.DataFrame(data)


def main():
    st.title("🏆Singapore Credit Card Reward Optimizer (Beta)")

    # Initialize services
    data_loader = get_data_loader()
    calculator = get_reward_calculator()

    try:
        # Load credit card data
        cards_df, tiers_df, rates_df, categories_df = data_loader.load_credit_card_data()

        # Sidebar spending inputs and filters
        user_spending_data, miles_to_sgd_rate, miles_value_cents = create_spending_inputs()
        selected_card_types = create_filters(cards_df)

        # Convert spending data to model
        spending_model = convert_spending_to_model(user_spending_data)

        # Filter cards based on user selection
        filtered_cards_df = cards_df[cards_df['Card Type'].isin(
            selected_card_types)]

        # Calculate rewards for filtered cards only
        all_results = calculator.calculate_filtered_cards_rewards(filtered_cards_df, spending_model, miles_to_sgd_rate)

        # Convert results to DataFrame for display
        all_cards_results_df = convert_results_to_dataframe(all_results, cards_df, categories_df, tiers_df, rates_df)

        # Get top cards for summary (from filtered results)
        top_cards = calculator.get_top_cards_from_results(all_results, limit=10)
        best_tier_per_card_df = convert_results_to_dataframe(top_cards, cards_df, categories_df, tiers_df, rates_df)

        # Add summary dashboard
        create_summary_dashboard(
            user_spending_data, best_tier_per_card_df, miles_value_cents)

        # Card analysis tabs
        single_card_tab, combination_analysis_tab = st.tabs([
            "💳 Single Card Analysis",
            "🔗 Multi-Card Strategy"
        ])

        # render single card tab
        with single_card_tab:
            render_single_card_component(
                best_cards_summary_df=best_tier_per_card_df,
                detailed_results_df=all_cards_results_df,
                user_spending_data=user_spending_data,
                miles_value_cents=miles_value_cents
            )

        # render multi-card tab
        with combination_analysis_tab:
            render_combination_component(
                filtered_cards_df=filtered_cards_df,
                best_single_cards_df=best_tier_per_card_df,
                detailed_results_df=all_cards_results_df,
                user_spending_data=user_spending_data,
                miles_to_sgd_rate=miles_to_sgd_rate,
                miles_value_cents=miles_value_cents
            )

    except Exception as e:
        st.error(f"Error loading application: {e}")
        st.info("Please check that all data files are present in the data/ directory.")


if __name__ == "__main__":
    main()
