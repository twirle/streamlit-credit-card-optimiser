import streamlit as st
from components.card_table import render_card_table
from components.category_help import CATEGORY_HELP
import pandas as pd

st.subheader("📈About Credit Card Optimiser")
st.caption("**🏷️Card info database last updated**: 21 Jul 2025")

"""
This tool helps you find the best credit card strategy to maximise your rewards based on your spending patterns. It calculates optimal rewards based on your monthly spending habits on-the-fly, and displays the result of each single card or multi-card strategy.

Application is still in beta with reward calculations for multi-card being improved on.
"""

# Show the card table in an expander (hidden by default)
render_card_table()

with st.expander("Info", expanded=False):
    """
    - Categories between credit cards may or may not be identical to each other, and one to one comparisons between cards of similar categories should be taken with caution.
    - This application also does not take into account bonuses outside of cashback and miles, e.g. sign-up bonuses, instant bonus cashbacks, limo services to Changi, free gifts.
    - Transaction classifications are determined by Merchant Category Codes (MCC) specified by the card issuer, do your own final checks to confirm if your purchases are including in the MCC list for each card.

    """

with st.expander("Spending Categories Explained", expanded=False):
    df = pd.DataFrame(list(CATEGORY_HELP.items()),
                      columns=["Category", "Description"])
    st.dataframe(df, hide_index=True)

    """
    With some cards, 'Dining' only constitutes dining in at restaurants, or only food delivery. In future, I may choose to split this category up to allow for better manage and allocation of spending inputs.

    I have previously split 'Transport' into SimplyGo and ride-hailing already.
    """


with st.expander("Next Steps", expanded=False):
    """

    1. Further improve and optimise 2-card algorithm.
    2. Build Card Explorer page, with filters for card type and category.
    3. Add more cards to database.

    """

"Many thanks to [Milelion](https://milelion.com/)."
