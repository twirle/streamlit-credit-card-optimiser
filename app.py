import streamlit as st
from components.inputs.spending_inputs import create_spending_inputs
from components.single_card_component import render_single_card_component
from components.multi_card_component import render_multi_card_component

# Page config
st.set_page_config(page_title="Credit Card Optimizer", layout="wide")


def main():
    st.info('↑ Use the sidebar to input your monthly spending.')
    st.header("💳 Singapore Credit Card Reward Optimiser (Beta)")
    st.subheader("📊 Spending & Rewards")

    # Get user spending and miles value
    user_spending_data, miles_to_sgd_rate, _ = create_spending_inputs()

    # Show 2 tabs of metrics: Total Monthly Spending, Best Single Card Strategy, Single Reward Rate, Best Multi Strategy Reward,
    single_card, multi_card = st.tabs(["Single", "Multi"])
    with single_card:
        render_single_card_component(user_spending_data, miles_to_sgd_rate)
    with multi_card:
        render_multi_card_component(user_spending_data, miles_to_sgd_rate)


if __name__ == "__main__":
    main()
