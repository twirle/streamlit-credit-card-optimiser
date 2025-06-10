import streamlit as st
from ui_components import initialize_spending_session_state

# initialise session state for persistance of spending data
initialize_spending_session_state()

st.title("About Credit Card Optimiser")
st.markdown("""
    This tool helps you find the best credit card strategy to maximise your rewards based on your spending patterns.         
    
    It calculates optimal rewards based on your monthly spending habits, and suggests single card or multi-card strategies.
            
    Application is still in beta with reward calculations for multi-card being worked out.
            
    **This does not take into account bonuses outside of cashback and miles, e.g. sign-up bonuses, instant bonus cashbacks, limo services to Changi, free gifts.** 

    #### Supported Cards:
    - **Cashback**: SC Smart, SC Simply Cash, Citi Cash Back, OCBC 365, DBS Live Fresh, HSBC Live +
    - **Miles**: SC Journey, Citi Prestige, Citi Rewards, Citi PremierMiles, OCBC Rewards, DBS Women’s World, DBS Women’s, HSBC Revolution, UOB KrisFlyer, UOB PRVI Miles, UOB Visa Signature, UOB Platinum Visa, UOB Lady’s, Maybank World Mastercard, Maybank Horizon Visa Signature

    **Last updated**: 1 Jun 2025

    #### Known Issues:
    - SC Smart triggering 8% and 10% cashback without hitting $ 800 / 1500 minimum req.
    - Limited responsiveness causing tables to clip on smaller devices.

    """
            )
