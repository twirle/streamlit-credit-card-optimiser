import streamlit as st
import pandas as pd

# Import custom modules
from services.data.card_loader import get_card_loader
from services.rewards_service import get_rewards_service
from models.credit_card_model import UserSpending
from components.inputs.spending_inputs import create_spending_inputs
from components.inputs.filters import create_filters
from components.layout.summary_dashboard import create_summary_dashboard
from components.single_card_component import render_single_card_component
from components.combination_card_component import render_combination_component

# Page config
st.set_page_config(
    page_title="Singapore Credit Card Reward Optimizer",
    page_icon="💳",
    layout="wide"
)


@st.cache_data(ttl=1800, max_entries=50)  # Cache for 30 minutes
def convert_spending_to_model(spending_dict: dict) -> UserSpending:
    """Convert spending dictionary to UserSpending model with caching"""
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


@st.cache_data(ttl=900, max_entries=100)  # Cache for 15 minutes
def convert_results_to_dataframe(results: list, available_cards: pd.DataFrame, card_categories: pd.DataFrame, card_tiers: pd.DataFrame, reward_rates: pd.DataFrame) -> pd.DataFrame:
    """Convert reward calculation results to DataFrame for display, including card_type, Issuer, Categories, Cap, and Min Spend."""
    if not results:
        return pd.DataFrame()

    # Use lookup tables for better performance
    card_loader = get_card_loader()
    lookup_tables = card_loader.build_lookup_tables()
    
    card_name_to_id = lookup_tables['card_name_to_id']
    card_id_to_info = lookup_tables['card_id_to_info']
    card_id_to_categories = lookup_tables['card_id_to_categories']
    card_id_to_tiers = lookup_tables['card_id_to_tiers']
    tier_id_to_rates = lookup_tables['tier_id_to_rates']

    data = []
    for result in results:
        # Lookup card info from optimized lookup table
        card_id = card_name_to_id.get(result.card_name)
        card_info = card_id_to_info.get(card_id, {}) if card_id else {}
        card_type = card_info.get('type')
        issuer = card_info.get('issuer')
        
        # Lookup categories from optimized lookup table (convert tuple back to list)
        categories_list = list(card_id_to_categories.get(card_id, ())) if card_id else []
        categories = ', '.join(categories_list)
        
        # Lookup tier and cap info from optimized lookup table
        cap = 'No Cap'
        min_spend = None
        if card_id and card_id in card_id_to_tiers:
            tiers = list(card_id_to_tiers[card_id])  # Convert tuple back to list
            # Find matching tier by description
            matching_tier = None
            for tier in tiers:
                if tier['description'] == result.tier_description:
                    matching_tier = tier
                    break
            
            if not matching_tier and len(tiers) == 1:
                matching_tier = tiers[0]  # fallback to single tier
            
            if matching_tier:
                tier_id = matching_tier['tier_id']
                min_spend = matching_tier['min_spend']
                # Find max cap for this tier from optimized lookup table
                if tier_id in tier_id_to_rates:
                    tier_rates = list(tier_id_to_rates[tier_id])  # Convert tuple back to list
                    cap_amounts = [rate['cap_amount'] for rate in tier_rates 
                                 if rate.get('cap_amount') is not None]
                    if cap_amounts:
                        cap = max(cap_amounts)
        
        data.append({
            'Card Name': result.card_name,
            'Tier': result.tier_description,
            'Monthly Reward': result.monthly_reward,
            'Cap Reached': result.cap_reached,
            'Cap Difference': result.cap_difference,
            'Min Spend Met': result.min_spend_met,
            'Details': '; '.join(result.details) if result.details else '',
            'Card Type': card_type,
            'Issuer': issuer,
            'Categories': categories,
            'Original Reward': result.original_reward,
            'Cap': cap,
            'Min Spend': min_spend
        })

    return pd.DataFrame(data)


def main():
    st.header("🏆Singapore Credit Card Reward Optimizer (Beta)")

    # Initialize services
    card_loader = get_card_loader()
    rewards_service = get_rewards_service()

    try:
        # Load credit card data with better naming (cached)
        with st.spinner("Loading card data..."):
            available_cards, card_tiers, reward_rates, card_categories = card_loader.load_all_card_data()

        # Sidebar spending inputs and filters
        user_spending_data, miles_to_sgd_rate, miles_value_cents = create_spending_inputs()
        selected_card_types = create_filters(available_cards)

        # Convert spending data to model with caching
        spending_model = convert_spending_to_model(user_spending_data)

        # Filter cards based on user selection with better naming
        filtered_cards = available_cards[available_cards['Card Type'].isin(
            selected_card_types)]
        if not filtered_cards.empty:
            selected_cards = filtered_cards.copy()
            if not isinstance(selected_cards, pd.DataFrame):
                selected_cards = pd.DataFrame(selected_cards)
        else:
            selected_cards = pd.DataFrame()

        # Calculate rewards for selected cards only with optimized batch processing
        with st.spinner("Calculating rewards..."):
            all_results = rewards_service.calculate_filtered_cards_rewards(
                selected_cards, spending_model, miles_to_sgd_rate)

        # Convert results to DataFrame for display with better naming and caching
        card_results = convert_results_to_dataframe(
            all_results, available_cards, card_categories, card_tiers, reward_rates)

        # Get top cards for summary (from filtered results) - reuse existing results
        top_cards = rewards_service.get_top_cards_from_results(
            all_results, limit=10)
        top_cards_df = convert_results_to_dataframe(
            top_cards, available_cards, card_categories, card_tiers, reward_rates)

        # Calculate combination results for summary dashboard with caching
        combinations_df = None
        if not selected_cards.empty and len(selected_cards) >= 2:
            try:
                with st.spinner("Calculating optimal combinations..."):
                    card_combinations_results = rewards_service.find_best_card_combinations(
                        selected_cards, user_spending_data, miles_to_sgd_rate, card_results
                    )
                    if card_combinations_results:
                        combinations_df = pd.DataFrame(card_combinations_results)
                        combinations_df = combinations_df.sort_values('Monthly Reward', ascending=False)
            except Exception as e:
                print(f"Error calculating combinations for summary: {e}")

        # Add summary dashboard
        create_summary_dashboard(
            user_spending_data, top_cards_df, miles_value_cents, combinations_df)

        # Card analysis tabs
        single_card_tab, combination_analysis_tab = st.tabs([
            "💳 Single Card Analysis",
            "🔗 Multi-Card Strategy"
        ])

        # render single card tab
        with single_card_tab:
            render_single_card_component(
                best_cards_summary_df=top_cards_df,
                detailed_results_df=card_results,
                user_spending_data=user_spending_data,
                miles_value_cents=miles_value_cents
            )

        # render multi-card tab
        with combination_analysis_tab:
            render_combination_component(
                selected_cards_df=selected_cards,
                best_single_cards_df=top_cards_df,
                card_results_df=card_results,
                user_spending_data=user_spending_data,
                miles_to_sgd_rate=miles_to_sgd_rate,
                miles_value_cents=miles_value_cents
            )

    except Exception as e:
        st.error(f"Error loading application: {e}")
        st.info(
            "Please check that all data files are present in the cardData/ directory.")


if __name__ == "__main__":
    main()
