import streamlit as st
import pandas as pd
from components.inputs.spending_inputs import initialize_spending_session_state
from services.data import get_card_loader

# initialise session state for persistance of spending data
initialize_spending_session_state()

st.title("About Credit Card Optimiser")
st.markdown("""
    This tool helps you find the best credit card strategy to maximise your rewards based on your spending patterns. It calculates optimal rewards based on your monthly spending habits, and suggests single card or multi-card strategies.
            
    Application is still in beta with reward calculations for multi-card being worked out.
    """)

# Get card data using the card loader service
card_loader = get_card_loader()

try:
    # Get cards for display
    cards_df = card_loader.get_cards_for_display()

    if not cards_df.empty:
        st.markdown("#### Supported Cards:")

        # Create tabs for different card types
        tab1, tab2 = st.tabs(["Cashback Cards", "Miles Cards"])

        with tab1:
            cashback_cards = card_loader.get_cards_by_type('Cashback')
            if not cashback_cards.empty:
                # Display as a simple table with consistent column widths
                display_df = cashback_cards[['Issuer', 'Card Name']].sort_values(
                    ['Issuer', 'Card Name'])
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Issuer": st.column_config.TextColumn("Issuer", width="medium"),
                        "Card Name": st.column_config.TextColumn("Card Name", width="large")
                    }
                )
            else:
                st.info("No cashback cards found.")

        with tab2:
            miles_cards = card_loader.get_cards_by_type('Miles')
            if not miles_cards.empty:
                # Display as a simple table with consistent column widths
                display_df = miles_cards[['Issuer', 'Card Name']].sort_values(
                    ['Issuer', 'Card Name'])
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Issuer": st.column_config.TextColumn("Issuer", width="medium"),
                        "Card Name": st.column_config.TextColumn("Card Name", width="large")
                    }
                )
            else:
                st.info("No miles cards found.")
    else:
        st.error("No card data available.")

except Exception as e:
    st.error(f"Error loading card data: {e}")

st.markdown("""
    #### Note:
    - Categories between credit cards may or may not be identical to each other, and one to one comparisons between cards of similar categories should be taken with caution.
    - This application also does not take into account bonuses outside of cashback and miles, e.g. sign-up bonuses, instant bonus cashbacks, limo services to Changi, free gifts.
    - Transaction classifications are determined by Merchant Category Codes (MCC) specified by the card issuer, do your own final checks to confirm if your purchases are including in the MCC list for each card.
    
        SC Smart has a really alluring 10% cashback, coupled with common daily spending categories with a somewhat acceptable minimum spending of $1500. This is a really attractive card, until you look at the fineprint to see what merchants you can spend on with it. 
        - **Dining**: McDonald's, KFC, Burger King, Ya Kun Kaya Toast, Subway and Toast Box, Starbucks, The Coffee Bean & Tea Leaf, Pizza Hut and Domino's Pizza
        - **Transport**: Bus and/or MRT via SimplyGo, EV Charging
        - **Streaming**: Netflix, Spotify, YouTube and Disney+, Amazon Prime, Viu, iQIYI and HBO GO

        > You're either a full time EV Grab driver that loves Toast Box subcribed to multiple streaming platforms, or you're throwing a Burger King party at your place every weekend.


    **Last updated**: 1 Jun 2025

    #### Known Issues:
    - UOB Lady's is clear to work best in a high spending category with its 4mpd. Optimal calculation logic for 2-card combinations with UOB Lady's is still a work in progress.
    - Limited responsiveness in resizing causing tables to clip on smaller devices.

    """
            )
