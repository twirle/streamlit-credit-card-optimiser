import streamlit as st
from components.ui_components import initialize_spending_session_state

# initialise session state for persistance of spending data
initialize_spending_session_state()

st.title("About Credit Card Optimiser")
st.markdown("""
    This tool helps you find the best credit card strategy to maximise your rewards based on your spending patterns. It calculates optimal rewards based on your monthly spending habits, and suggests single card or multi-card strategies.
            
    Application is still in beta with reward calculations for multi-card being worked out.
            

    #### Supported Cards:
    - **Cashback**: SC Smart, SC Simply Cash, Citi Cash Back, OCBC 365, DBS Live Fresh, HSBC Live +
    - **Miles**: SC Journey, Citi Prestige, Citi Rewards, Citi PremierMiles, OCBC Rewards, DBS Women’s World, DBS Women’s, HSBC Revolution, UOB KrisFlyer, UOB PRVI Miles, UOB Visa Signature, UOB Platinum Visa, UOB Lady’s, Maybank World Mastercard, Maybank Horizon Visa Signature

    #### Note:
    - **This does not take into account bonuses outside of cashback and miles, e.g. sign-up bonuses, instant bonus cashbacks, limo services to Changi, free gifts.** 
    - Transaction classifications are in the end determined by Merchant Category Codes (MCC) specified by the card issuer.
    - Categories between credit cards may or may not be identical to each other, and one to one comparisons between cards of similar categories should be taken with caution.
    - Do your own final checks to confirm if your purchases are not excluded from the list MCCs for each card.
    - UOB Lady's is clear to work best in a high spending category with its 4mpd. Calculation logic for 2-card combinations with UOB Lady's is still a work in progress.

    **Last updated**: 1 Jun 2025

    #### Known Issues:
    - Calculation for UOB Lady's requires separate logic for 2-card combinations and is work in progress.
    - SC Smart triggering 8% and 10% cashback without hitting $ 800 / 1500 minimum req.
    - Limited responsiveness in resizing causing tables to clip on smaller devices.

    """
            )
