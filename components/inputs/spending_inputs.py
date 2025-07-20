import streamlit as st

# Centralized default values for all spending categories
DEFAULT_SPENDING_VALUES = {
    'dining': 250,
    'groceries': 250,
    'transport': 60,
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
    if 'user_spending_data' not in st.session_state:
        st.session_state.user_spending_data = DEFAULT_SPENDING_VALUES.copy()

    if 'miles_value_cents' not in st.session_state:
        st.session_state.miles_value_cents = 2.0

    if 'miles_to_sgd_rate' not in st.session_state:
        st.session_state.miles_to_sgd_rate = 0.02


def create_miles_valuation_input():
    if 'miles_value_cents' not in st.session_state:
        st.session_state['miles_value_cents'] = 2.0

    with st.sidebar.container():
        st.markdown("**💎 Miles Valuation**")
        st.number_input(
            "Miles Value (¢)",
            min_value=1.0,
            max_value=10.0,
            step=0.1,
            help="Value per mile in cents SGD",
            key="miles_value_cents"
        )
    return st.session_state['miles_value_cents']


def create_food_daily_inputs():
    """Create food and daily spending inputs"""
    for key in ["dining", "groceries", "transport", "simplygo"]:
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_SPENDING_VALUES[key]
    with st.sidebar.expander("🍽️ Food & Daily", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Dining", 0, 2000, step=25, key="dining",
                help="Restaurants, cafes, hawkers, FoodPanda, GrabFood")
            st.number_input(
                "Groceries", 0, 2000, step=25, key="groceries",
                help="Supermarkets, RedMart")
        with col2:
            st.number_input(
                "Transport", 0, 500, step=25, key="transport",
                help="Ride-hailing, taxis, private hire")
            st.number_input(
                "SimplyGo", 0, 500, step=25, key="simplygo",
                help="Public transport (bus/MRT)")
    return st.session_state["dining"], st.session_state["groceries"], st.session_state["transport"], st.session_state["simplygo"]


def create_entertainment_utilities_inputs():
    """Create entertainment, bills, and petrol spending inputs"""
    for key in ["streaming", "entertainment", "utilities", "petrol"]:
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_SPENDING_VALUES[key]
    with st.sidebar.expander("🎬 Entertainment & Bills", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            st.number_input(
                "Streaming", 0, 200, step=5, key="streaming",
                help="Netflix, Disney+, Spotify, etc.")
            st.number_input(
                "Petrol", 0, 1000, step=25, key="petrol",
                help="Fuel for private car")
        with col4:
            st.number_input(
                "Entertainment", 0, 500, step=25, key="entertainment",
                help="Movies, concerts, events")
            st.number_input(
                "Utilities", 0, 500, step=25, key="utilities",
                help="Electricity, water, gas")
    return st.session_state["streaming"], st.session_state["entertainment"], st.session_state["utilities"], st.session_state["petrol"]


def create_shopping_inputs():
    """Create shopping spending inputs"""
    for key in ["retail", "online"]:
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_SPENDING_VALUES[key]
    with st.sidebar.expander("🛍️ Shopping", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.number_input(
                "Retail", 0, 1000, step=25, key="retail",
                help="In-store shopping, malls, fashion, discount stores, Wattsons, etc.")
        with col2:
            st.number_input(
                "Online", 0, 1000, step=25, key="online",
                help="E-commerce, Lazada, Shopee, Amazon")
    return st.session_state["retail"], st.session_state["online"]


def create_travel_fcy_inputs():
    """Create travel and FCY spending inputs"""
    for key in ["travel", "fcy"]:
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_SPENDING_VALUES[key]
    with st.sidebar.expander("✈️ Travel & FCY", expanded=True):
        col5, col6 = st.columns(2)
        with col5:
            st.number_input(
                "Travel", 0, 2000, step=50, key="travel",
                help="Hotels, flights")
        with col6:
            st.number_input(
                "FCY", 0, 2000, step=50, key="fcy",
                help="All non-SGD spend, e.g. online or overseas")
    return st.session_state["travel"], st.session_state["fcy"]


def create_spending_summary(total):
    """Create spending summary with metrics and progress bar"""
    # Enhanced total display with progress bar
    st.sidebar.metric("Total Spending", f"${total:,}")

    # Progress bar for spending categories
    if total > 0:
        st.sidebar.progress(min(total / 2000, 1.0), text="Spending Level")


def create_spending_inputs():
    """Create spending inputs with enhanced UI and progress indicators"""
    # Initialize session state
    initialize_spending_session_state()

    st.sidebar.header("📊 Monthly Spending")

    # Miles valuation
    miles_value_cents = create_miles_valuation_input()

    # Enhanced spending inputs with progress indicators
    st.sidebar.subheader("💸 Spending Categories")

    # Get all spending inputs
    dining, groceries, transport, simplygo = create_food_daily_inputs()
    streaming, entertainment, utilities, petrol = create_entertainment_utilities_inputs()
    retail, online = create_shopping_inputs()
    travel, fcy = create_travel_fcy_inputs()

    # Calculate total
    total = dining + groceries + petrol + transport + simplygo + streaming + \
        entertainment + utilities + online + travel + fcy + retail

    # Update session state with all values
    st.session_state.user_spending_data.update({
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

    # Create spending summary
    create_spending_summary(total)

    return st.session_state.user_spending_data, st.session_state.miles_to_sgd_rate, miles_value_cents
