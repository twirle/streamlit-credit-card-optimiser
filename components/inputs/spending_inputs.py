import streamlit as st
from components.state.session import (
    initialize_spending_state, get_user_spending, set_user_spending
)
from components.category_help import CATEGORY_HELP

# Centralized default values for all spending categories
DEFAULT_SPENDING_VALUES = {
    'dining': 250,
    'groceries': 250,
    'transport': 75,
    'simplygo': 75,
    'streaming': 0,
    'entertainment': 50,
    'utilities': 0,
    'petrol': 0,
    'retail': 150,
    'online': 200,
    'travel': 0,
    'fcy': 75,
}


def initialize_spending_session_state():
    """Initialize session state for spending data and miles valuation"""
    initialize_spending_state(DEFAULT_SPENDING_VALUES)


def create_miles_valuation_input():
    with st.sidebar.container():
        st.markdown("**💎 Miles Valuation**")
        st.number_input(
            "Miles Value (¢)",
            min_value=1.0,
            max_value=10.0,
            step=0.1,
            value=2.0,
            help="Value per mile in cents SGD",
            key="miles_value_cents"
        )
    return st.session_state['miles_value_cents']


def create_food_daily_inputs():
    """Create food and daily spending inputs"""
    spending = get_user_spending()
    for key in ["dining", "groceries", "transport", "simplygo"]:
        if key not in spending:
            spending[key] = DEFAULT_SPENDING_VALUES[key]
    set_user_spending(spending)
    with st.sidebar.expander("🍽️ Food & Daily", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Dining", 0, 2000, value=spending.get("dining", DEFAULT_SPENDING_VALUES["dining"]), step=25, key="dining",
                help=CATEGORY_HELP["Dining"])
            st.number_input(
                "Groceries", 0, 2000, value=spending.get("groceries", DEFAULT_SPENDING_VALUES["groceries"]), step=25, key="groceries",
                help=CATEGORY_HELP["Groceries"])
        with col2:
            st.number_input(
                "Transport", 0, 500, value=spending.get("transport", DEFAULT_SPENDING_VALUES["transport"]), step=25, key="transport",
                help=CATEGORY_HELP["Transport"])
            st.number_input(
                "SimplyGo", 0, 500, value=spending.get("simplygo", DEFAULT_SPENDING_VALUES["simplygo"]), step=25, key="simplygo",
                help=CATEGORY_HELP["SimplyGo"])
    return st.session_state["dining"], st.session_state["groceries"], st.session_state["transport"], st.session_state["simplygo"]


def create_entertainment_utilities_inputs():
    """Create entertainment, bills, and petrol spending inputs"""
    spending = get_user_spending()
    for key in ["streaming", "entertainment", "utilities", "petrol"]:
        if key not in spending:
            spending[key] = DEFAULT_SPENDING_VALUES[key]
    set_user_spending(spending)
    with st.sidebar.expander("🎬 Entertainment & Bills", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            st.number_input(
                "Streaming", 0, 200, value=spending.get("streaming", DEFAULT_SPENDING_VALUES["streaming"]), step=5, key="streaming",
                help=CATEGORY_HELP["Streaming"])
            st.number_input(
                "Petrol", 0, 1000, value=spending.get("petrol", DEFAULT_SPENDING_VALUES["petrol"]), step=25, key="petrol",
                help=CATEGORY_HELP["Petrol"])
        with col4:
            st.number_input(
                "Entertainment", 0, 500, value=spending.get("entertainment", DEFAULT_SPENDING_VALUES["entertainment"]), step=25, key="entertainment",
                help=CATEGORY_HELP["Entertainment"])
            st.number_input(
                "Utilities", 0, 500, value=spending.get("utilities", DEFAULT_SPENDING_VALUES["utilities"]), step=25, key="utilities",
                help=CATEGORY_HELP["Utilities"])
    return st.session_state["streaming"], st.session_state["entertainment"], st.session_state["utilities"], st.session_state["petrol"]


def create_shopping_inputs():
    """Create shopping spending inputs"""
    spending = get_user_spending()
    for key in ["retail", "online"]:
        if key not in spending:
            spending[key] = DEFAULT_SPENDING_VALUES[key]
    set_user_spending(spending)
    with st.sidebar.expander("🛍️ Shopping", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Retail", 0, 1000, value=spending.get("retail", DEFAULT_SPENDING_VALUES["retail"]), step=25, key="retail",
                help=CATEGORY_HELP["Retail"])
        with col2:
            st.number_input(
                "Online", 0, 1000, value=spending.get("online", DEFAULT_SPENDING_VALUES["online"]), step=25, key="online",
                help=CATEGORY_HELP["Online"])
    return st.session_state["retail"], st.session_state["online"]


def create_travel_fcy_inputs():
    """Create travel and FCY spending inputs"""
    spending = get_user_spending()
    for key in ["travel", "fcy"]:
        if key not in spending:
            spending[key] = DEFAULT_SPENDING_VALUES[key]
    set_user_spending(spending)
    with st.sidebar.expander("✈️ Travel & FCY", expanded=True):
        col5, col6 = st.columns(2)
        with col5:
            st.number_input(
                "Travel", 0, 2000, value=spending.get("travel", DEFAULT_SPENDING_VALUES["travel"]), step=50, key="travel",
                help=CATEGORY_HELP["Travel"])
        with col6:
            st.number_input(
                "FCY", 0, 2000, value=spending.get("fcy", DEFAULT_SPENDING_VALUES["fcy"]), step=50, key="fcy",
                help=CATEGORY_HELP["FCY"])
    return st.session_state["travel"], st.session_state["fcy"]


def create_spending_summary(total):
    """Create spending summary with metrics and progress bar"""
    st.sidebar.metric("Total Spending", f"${total:,}")
    if total > 0:
        st.sidebar.progress(min(total / 2000, 1.0), text="Spending Level")


def create_spending_inputs():
    """Create spending inputs with enhanced UI and progress indicators"""
    initialize_spending_session_state()
    st.sidebar.header("📊 Monthly Spending")
    miles_value_cents = create_miles_valuation_input()
    st.sidebar.subheader("💸 Spending Categories")
    dining, groceries, transport, simplygo = create_food_daily_inputs()
    streaming, entertainment, utilities, petrol = create_entertainment_utilities_inputs()
    retail, online = create_shopping_inputs()
    travel, fcy = create_travel_fcy_inputs()
    total = dining + groceries + petrol + transport + simplygo + streaming + \
        entertainment + utilities + online + travel + fcy + retail
    spending = get_user_spending()
    spending.update({
        'dining': dining,
        'groceries': groceries,
        'petrol': petrol,
        'transport': transport,
        'simplygo': simplygo,
        'streaming': streaming,
        'entertainment': entertainment,
        'utilities': utilities,
        'online': online,
        'travel': travel,
        'fcy': fcy,
        'retail': retail,
        'total': total
    })
    set_user_spending(spending)
    create_spending_summary(total)
    return spending, st.session_state.miles_to_sgd_rate, miles_value_cents
