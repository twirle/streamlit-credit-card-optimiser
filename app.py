import streamlit as st
from components.inputs.spending_inputs import create_spending_inputs
from components.single_card_component import render_single_card_component
from components.multi_card_component import render_multi_card_component
from services.data.card_loader import load_cards_and_models

# Page config
st.set_page_config(page_title="Credit Card Optimizer", layout="wide")

# Cache the card loader
def get_cards():
    # Use Streamlit's cache to avoid reloading unless data changes
    return load_cards_and_models()
get_cards = st.cache_data(get_cards)

def main():
    st.info('↑ Use the sidebar to input your monthly spending.')
    st.header("\U0001F4B3 Singapore Credit Card Reward Optimiser (Beta)")
    st.subheader("\U0001F4CA Spending & Rewards")

    # Get user spending and miles value
    user_spending_data, miles_to_sgd_rate, _ = create_spending_inputs()

    # Load cards once
    cards = get_cards()

    # Show 2 tabs of metrics: Total Monthly Spending, Best Single Card Strategy, Single Reward Rate, Best Multi Strategy Reward,
    single_card, multi_card = st.tabs(["Single", "Multi"])
    with single_card:
        render_single_card_component(user_spending_data, miles_to_sgd_rate, cards)
    with multi_card:
        render_multi_card_component(user_spending_data, miles_to_sgd_rate, cards)


if __name__ == "__main__":
    main()
