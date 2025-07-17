import streamlit as st
import pandas as pd

st.title("About Credit Card Optimiser")
st.markdown("""
    This tool helps you find the best credit card strategy to maximise your rewards based on your spending patterns. It calculates optimal rewards based on your monthly spending habits, and suggests single card or multi-card strategies.
            
    Application is still in beta with reward calculations for multi-card being worked out.
    """)

# Get card data using the card loader service

# Display table of cashback and miles cards in two tabs


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
