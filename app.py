import streamlit as st
import pandas as pd

# Import custom modules
from data_loader import load_data, get_card_categories
from calculations import calculate_card_reward_details
from ui_components import create_spending_inputs, create_filters
from single_card_component import render_single_card_component
from combination_card_component import render_combination_component

# Page config
st.set_page_config(
    page_title="Singapore Credit Card Reward Optimizer",
    page_icon="💳",
    layout="wide"
)


def calculate_all_card_rewards(filtered_cards_df, user_spending_data, miles_to_sgd_rate):
    """Calculate rewards for all cards and return organized results"""
    individual_card_results = []

    for card_index, current_card in filtered_cards_df.iterrows():
        reward_amount, calculation_details, is_cap_reached, cap_difference, original_reward, min_spend_satisfied = calculate_card_reward_details(
            current_card, user_spending_data, miles_to_sgd_rate)

        # Get categories from CSV
        card_categories_list = get_card_categories(current_card)
        card_categories_display = ", ".join(card_categories_list)

        individual_card_results.append({
            'Card Name': current_card['Name'],
            'Issuer': current_card['Issuer'],
            'Type': current_card['Type'],
            'Categories': card_categories_display,
            'Monthly Reward': reward_amount,
            'Min Spend': current_card.get('Min Spend', 0),
            'Cap': current_card.get('Cap', 'No Cap'),
            'Cap Reached': is_cap_reached,
            'Cap Difference': cap_difference,
            'Original Reward': original_reward,
            'Min Spend Met': min_spend_satisfied,
            'Details': calculation_details,
            'Source': current_card.get('Source', '')
        })

    all_cards_results_df = pd.DataFrame(individual_card_results)

    # Group by card name and take the best tier for each card
    best_tier_per_card_df = all_cards_results_df.groupby(['Card Name', 'Issuer']).agg({
        'Monthly Reward': 'max',
        'Type': 'first',
        'Categories': 'first',
        'Cap Reached': 'any',
        'Cap Difference': 'first',
        'Source': 'first'
    }).reset_index()

    # Sort by Monthly Reward for display (highest first)
    best_tier_per_card_df = best_tier_per_card_df.sort_values(
        'Monthly Reward',
        ascending=False
    ).reset_index(drop=True)

    return all_cards_results_df, best_tier_per_card_df


def main():
    st.title("🏆Singapore Credit Card Reward Optimizer (Beta)")

    # Load credit card data
    credit_cards_df = load_data()

    # Sidebar spending inputs and filters
    user_spending_data, miles_to_sgd_rate, miles_value_cents = create_spending_inputs()
    selected_card_types = create_filters(credit_cards_df)

    # Filter cards based on user selection
    filtered_cards_df = credit_cards_df[credit_cards_df['Type'].isin(
        selected_card_types)]

    # Calculate rewards for all cards
    all_cards_results_df, best_tier_per_card_df = calculate_all_card_rewards(
        filtered_cards_df, user_spending_data, miles_to_sgd_rate
    )

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


if __name__ == "__main__":
    main()
