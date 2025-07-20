import streamlit as st


def initialize_spending_session_state():
    """Initialize session state for spending data and miles valuation"""
    if 'user_spending_data' not in st.session_state:
        st.session_state.user_spending_data = {
            'dining': 200,
            'groceries': 250,
            'transport': 50,
            'simplygo': 75,
            'streaming': 25,
            'entertainment': 25,
            'utilities': 0,
            'petrol': 0,
            'retail': 100,
            'online': 250,
            'travel': 100,
            'fcy': 0,
        }

    if 'miles_value_cents' not in st.session_state:
        st.session_state.miles_value_cents = 1.5

    if 'miles_to_sgd_rate' not in st.session_state:
        st.session_state.miles_to_sgd_rate = 0.02


def create_miles_valuation_input():
    """Create miles valuation input with enhanced styling"""
    with st.sidebar.container():
        st.markdown("**💎 Miles Valuation**")
        miles_value_cents = st.number_input(
            "Miles Value (¢)",
            min_value=1.0,
            max_value=10.0,
            value=st.session_state.miles_value_cents,
            step=0.1,
            help="Value per mile in cents SGD"
        )

    # Update session state
    st.session_state.miles_value_cents = miles_value_cents
    st.session_state.miles_to_sgd_rate = miles_value_cents / 100

    return miles_value_cents


def create_food_daily_inputs():
    """Create food and daily spending inputs"""
    with st.sidebar.expander("🍽️ Food & Daily", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            dining = st.number_input(
                "Dining", 0, 2000, st.session_state.user_spending_data['dining'], 25, key="dining")
            groceries = st.number_input(
                "Groceries", 0, 2000, st.session_state.user_spending_data['groceries'], 25, key="groceries")
        with col2:
            transport = st.number_input(
                "Transport", 0, 500, st.session_state.user_spending_data['transport'], 25, key="transport")
            simplygo = st.number_input(
                "SimplyGo", 0, 500, st.session_state.user_spending_data['simplygo'], 25, key="simplygo")
    return dining, groceries, transport, simplygo


def create_entertainment_utilities_inputs():
    """Create entertainment, bills, and petrol spending inputs"""
    with st.sidebar.expander("🎬 Entertainment & Bills", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            streaming = st.number_input(
                "Streaming", 0, 200, st.session_state.user_spending_data['streaming'], 5, key="streaming")
            petrol = st.number_input(
                "Petrol", 0, 1000, st.session_state.user_spending_data['petrol'], 25, key="petrol")
        with col4:
            entertainment = st.number_input(
                "Entertainment", 0, 500, st.session_state.user_spending_data['entertainment'], 25, key="entertainment")
            utilities = st.number_input(
                "Utilities", 0, 500, st.session_state.user_spending_data['utilities'], 25, key="utilities")
    return streaming, entertainment, utilities, petrol


def create_shopping_inputs():
    """Create shopping spending inputs"""
    with st.sidebar.expander("🛍️ Shopping", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            retail = st.number_input(
                "Retail", 0, 1000, st.session_state.user_spending_data['retail'], 25, key="retail")
        with col2:
            online = st.number_input(
                "Online", 0, 1000, st.session_state.user_spending_data['online'], 25, key="online")
    return retail, online


def create_travel_fcy_inputs():
    """Create travel and FCY spending inputs"""
    with st.sidebar.expander("✈️ Travel & FCY", expanded=True):
        col5, col6 = st.columns(2)
        with col5:
            travel = st.number_input(
                "Travel", 0, 2000, st.session_state.user_spending_data['travel'], 50, key="travel")
        with col6:
            fcy = st.number_input(
                "FCY", 0, 2000, st.session_state.user_spending_data['fcy'], 50, key="fcy")
    return travel, fcy


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
