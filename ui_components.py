import streamlit as st
import plotly.express as px
import pandas as pd


def initialize_spending_session_state():
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
            'other': 150
        }

    if 'miles_value_cents' not in st.session_state:
        st.session_state.miles_value_cents = 2.0

    if 'miles_to_sgd_rate' not in st.session_state:
        st.session_state.miles_to_sgd_rate = 0.02


def create_spending_inputs():
    # Initialize session state
    initialize_spending_session_state()

    st.sidebar.header("📊 Monthly Spending")

    # Miles valuation - compact
    miles_value_cents = st.sidebar.number_input(
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

    # st.sidebar.markdown("---")

    # Compact spending inputs using columns within sidebar
    st.sidebar.subheader("💸 Categories")

    # Group 1: Food & Daily
    with st.sidebar.container():
        st.write("**Food & Daily**")
        col1, col2 = st.sidebar.columns(2)
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

    # Group 2: Entertainment & Utilities
    with st.sidebar.container():
        st.write("**Entertainment & Bills**")
        col3, col4 = st.sidebar.columns(2)
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

    # Group 3: Travel & Others
    with st.sidebar.container():
        st.write("**Travel & Others**")
        col5, col6 = st.sidebar.columns(2)
        with col5:
            travel = st.number_input(
                "Travel", 0, 2000, st.session_state.user_spending_data['travel'], 50, key="travel")
            overseas = st.number_input(
                "Overseas", 0, 2000, st.session_state.user_spending_data['overseas'], 50, key="overseas")
        with col6:
            other = st.number_input(
                "Other", 0, 1000, st.session_state.user_spending_data['other'], 25, key="other")

    # Calculate total
    total = dining + groceries + petrol + transport + streaming + \
        entertainment + utilities + online + travel + overseas + other

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
        'other': other,
        'total': total
    })

    st.sidebar.success(f"**Total: ${total:,}/month**")

    return st.session_state.user_spending_data, st.session_state.miles_to_sgd_rate, st.session_state.miles_value_cents


def create_filters(df):
    st.sidebar.header("🔍 Filters")
    filter_option = st.sidebar.selectbox(
        "Select Card Type:",
        options=["All Cards", "Miles Only", "Cashback Only"],
        index=0
    )

    if filter_option == "All Cards":
        card_types = df['Type'].unique().tolist()
    elif filter_option == "Miles Only":
        card_types = ["Miles"]
    else:  # "Cashback Only"
        card_types = ["Cashback"]

    return card_types


def display_miles_info(miles_value_cents):
    return st.info(f"""
    **Miles Valuation Guide:**
    • Economy flights: 1.5-2.5¢
    • Business class: 3-6¢  
    • First class: 6-8¢+
    • Currently using: **{miles_value_cents:.1f}¢** per mile
    """)


def create_rewards_chart(display_results_df, miles_value_cents):
    if len(display_results_df) > 0:
        chart_data = display_results_df.head(8).sort_values(
            'Monthly Reward', ascending=True)

        fig = px.bar(
            chart_data,
            x='Monthly Reward',
            y='Card Name',
            color='Type',
            title=f"Monthly Reward Comparison (Miles @ {miles_value_cents:.1f}¢ each)",
            labels={'Monthly Reward': 'Monthly Reward'},
            orientation='h'
        )
        fig.update_layout(height=500)
        return fig
    return None


def display_results_table(display_results_df):
    display_df = display_results_df.head(10).copy()
    display_df['Monthly Reward'] = display_df['Monthly Reward'].round(2)

    display_df['Cap Status'] = display_df.apply(lambda row:
                                                f"🚫 Capped" if row['Cap Reached'] else
                                                "✅ Under Cap", axis=1)

    # Add ranking column
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))

    # Replace top 3 ranks with medal emojis
    if len(display_df) >= 1:
        display_df.iloc[0, 0] = '🥇'
    if len(display_df) >= 2:
        display_df.iloc[1, 0] = '🥈'
    if len(display_df) >= 3:
        display_df.iloc[2, 0] = '🥉'

    st.dataframe(
        display_df[['Rank', 'Card Name', 'Issuer', 'Categories',
                    'Type', 'Monthly Reward', 'Cap Status']],
        use_container_width=True,
        hide_index=True
    )
