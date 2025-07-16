"""
Spending Inputs Component

This module handles all user spending input functionality including
session state management and input validation.
"""

import streamlit as st


def initialize_spending_session_state():
    """Initialize session state for spending data and miles valuation"""
    if 'user_spending_data' not in st.session_state:
        st.session_state.user_spending_data = {
            'dining': 250,
            'groceries': 450,
            'petrol': 0,
            'transport': 150,
            'streaming': 25,
            'entertainment': 50,
            'utilities': 150,
            'online': 250,
            'travel': 0,
            'overseas': 50,
            'retail': 200,
            'departmental': 100,
            'other': 150
        }

    if 'miles_value_cents' not in st.session_state:
        st.session_state.miles_value_cents = 2.0

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
            petrol = st.number_input(
                "Petrol", 0, 1000, st.session_state.user_spending_data['petrol'], 25, key="petrol")
            transport = st.number_input(
                "Transport", 0, 500, st.session_state.user_spending_data['transport'], 25, key="transport")
    
    return dining, groceries, petrol, transport


def create_entertainment_utilities_inputs():
    """Create entertainment and utilities spending inputs"""
    with st.sidebar.expander("🎬 Entertainment & Bills", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            streaming = st.number_input(
                "Streaming", 0, 200, st.session_state.user_spending_data['streaming'], 5, key="streaming")
            entertainment = st.number_input(
                "Entertainment", 0, 500, st.session_state.user_spending_data['entertainment'], 25, key="entertainment")
        with col4:
            utilities = st.number_input(
                "Utilities", 0, 500, st.session_state.user_spending_data['utilities'], 25, key="utilities")
            online = st.number_input(
                "Online", 0, 1000, st.session_state.user_spending_data['online'], 25, key="online")
    
    return streaming, entertainment, utilities, online


def create_shopping_inputs():
    """Create shopping spending inputs"""
    with st.sidebar.expander("🛍️ Shopping", expanded=True):
        col_shopping1, col_shopping2 = st.columns(2)
        with col_shopping1:
            retail = st.number_input(
                "Retail", 0, 1000, st.session_state.user_spending_data['retail'], 25, key="retail")
        with col_shopping2:
            departmental = st.number_input(
                "Departmental", 0, 500, st.session_state.user_spending_data['departmental'], 25, key="departmental")
    
    return retail, departmental


def create_travel_others_inputs():
    """Create travel and other spending inputs"""
    with st.sidebar.expander("✈️ Travel & Others", expanded=True):
        col5, col6 = st.columns(2)
        with col5:
            travel = st.number_input(
                "Travel", 0, 2000, st.session_state.user_spending_data['travel'], 50, key="travel")
            overseas = st.number_input(
                "Overseas", 0, 2000, st.session_state.user_spending_data['overseas'], 50, key="overseas")
        with col6:
            other = st.number_input(
                "Other", 0, 1000, st.session_state.user_spending_data['other'], 25, key="other")
    
    return travel, overseas, other


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
    dining, groceries, petrol, transport = create_food_daily_inputs()
    streaming, entertainment, utilities, online = create_entertainment_utilities_inputs()
    retail, departmental = create_shopping_inputs()
    travel, overseas, other = create_travel_others_inputs()

    # Calculate total
    total = dining + groceries + petrol + transport + streaming + \
        entertainment + utilities + online + travel + \
        overseas + retail + departmental + other

    # Update session state with all values
    st.session_state.user_spending_data.update({
        'dining': dining,
        'groceries': groceries,
        'petrol': petrol,
        'transport': transport,
        'streaming': streaming,
        'entertainment': entertainment,
        'utilities': utilities,
        'online': online,
        'travel': travel,
        'overseas': overseas,
        'retail': retail,
        'departmental': departmental,
        'other': other,
        'total': total
    })

    # Create spending summary
    create_spending_summary(total)

    return st.session_state.user_spending_data, st.session_state.miles_to_sgd_rate, miles_value_cents 