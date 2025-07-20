import streamlit as st
from components.card_table import render_card_table

st.title("About Credit Card Optimiser")

st.caption("**Last updated**: 21 Jul 2025")

"""
This tool helps you find the best credit card strategy to maximise your rewards based on your spending patterns. It calculates optimal rewards based on your monthly spending habits, and suggests single card or multi-card strategies.

Application is still in beta with reward calculations for multi-card being improved on.
"""

# Show the card table in an expander (hidden by default)
render_card_table()


with st.expander("**Info**", expanded=False):
    """
    - Categories between credit cards may or may not be identical to each other, and one to one comparisons between cards of similar categories should be taken with caution.
    - This application also does not take into account bonuses outside of cashback and miles, e.g. sign-up bonuses, instant bonus cashbacks, limo services to Changi, free gifts.
    - Transaction classifications are determined by Merchant Category Codes (MCC) specified by the card issuer, do your own final checks to confirm if your purchases are including in the MCC list for each card.
    """

    """
        **SC Smart**

        SC Smart has a really alluring 10% cashback, coupled with common daily spending categories. Seems decent, until you look at the fineprint to see what merchants you can spend on with it.
        - **Dining**: McDonald's, KFC, Burger King, Ya Kun Kaya Toast, Subway and Toast Box, Starbucks, The Coffee Bean & Tea Leaf, Pizza Hut and Domino's Pizza
        - **Transport**: Bus and/or MRT via SimplyGo, EV Charging
        - **Streaming**: Netflix, Spotify, YouTube and Disney+, Amazon Prime, Viu, iQIYI and HBO GO

        > You're either a full time EV Grab driver that loves Toast Box subcribed to multiple streaming platforms, or you're throwing a Burger King party at your place every weekend.

    """


"""
##### Next Steps:

1. Further improve and optimise 2-card algorithm.
2. Build Card Explorer page, with filters for card type and category.
3. Add more cards to database.

"""
