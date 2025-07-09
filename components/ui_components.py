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
            'retail': 200,
            'departmental': 100,
            'other': 150
        }

    if 'miles_value_cents' not in st.session_state:
        st.session_state.miles_value_cents = 2.0

    if 'miles_to_sgd_rate' not in st.session_state:
        st.session_state.miles_to_sgd_rate = 0.02


def create_spending_inputs():
    """Create spending inputs with enhanced UI and progress indicators"""
    # Initialize session state
    initialize_spending_session_state()

    st.sidebar.header("📊 Monthly Spending")

    # Miles valuation with better styling
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

    # Enhanced spending inputs with progress indicators
    st.sidebar.subheader("💸 Spending Categories")

    # Group 1: Food & Daily
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

    # Group 2: Entertainment & Utilities
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

    # Group 2.5: Shopping
    with st.sidebar.expander("🛍️ Shopping", expanded=True):
        col_shopping1, col_shopping2 = st.columns(2)
        with col_shopping1:
            retail = st.number_input(
                "Retail", 0, 1000, st.session_state.user_spending_data['retail'], 25, key="retail")
        with col_shopping2:
            departmental = st.number_input(
                "Departmental", 0, 500, st.session_state.user_spending_data['departmental'], 25, key="departmental")

    # Group 3: Travel & Others
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

    # Enhanced total display with progress bar
    # Spending summary with metrics
    st.sidebar.metric("Total Spending", f"${total:,}")

    # Progress bar for spending categories
    if total > 0:
        st.sidebar.progress(min(total / 2000, 1.0), text="Spending Level")

    return st.session_state.user_spending_data, st.session_state.miles_to_sgd_rate, st.session_state.miles_value_cents


def create_filters(df):
    """Create filters for card types"""
    filter_option = st.sidebar.selectbox(
        "Select Card Type:",
        options=["All Cards", "Miles Only", "Cashback Only"],
        index=0
    )

    if filter_option == "All Cards":
        # Handle both column naming conventions
        if 'Card Type' in df.columns:
            card_types = df['Card Type'].unique().tolist()
        elif 'card_type' in df.columns:
            card_types = df['card_type'].unique().tolist()
        else:
            card_types = ["Miles", "Cashback"]
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
    """Create enhanced rewards comparison chart with better styling"""
    if len(display_results_df) > 0:
        chart_data = display_results_df.head(10).sort_values(
            'Monthly Reward', ascending=True)

        # Enhanced color scheme
        color_map = {
            'Miles': '#1f77b4',  # Blue for miles
            'Cashback': '#ff7f0e'  # Orange for cashback
        }

        fig = px.bar(
            chart_data,
            x='Monthly Reward',
            y='Card Name',
            color='Card Type',
            title=f"Monthly Reward Comparison (Miles @ {miles_value_cents:.1f}¢ each)",
            labels={
                'Monthly Reward': 'Monthly Reward ($)', 'Card Name': 'Credit Card'},
            orientation='h',
            color_discrete_map=color_map,
            hover_data=['Issuer', 'Categories']
        )

        # Enhanced layout
        fig.update_layout(
            height=600,  # Increased height to accommodate 10 cards
            title_x=0.5,
            title_font_size=16,
            showlegend=True,
            legend_title="Card Type",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20)
        )

        # Enhanced hover template
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>" +
            "Monthly Reward: $%{x:.2f}<br>" +
            "Issuer: %{customdata[0]}<br>" +
            "Categories: %{customdata[1]}<br>" +
            "<extra></extra>"
        )

        return fig
    return None


def display_results_table(display_results_df):
    """Display results table with enhanced styling and metrics, always showing all results in a scrollable table."""
    if display_results_df.empty:
        st.write("No results to display.")
        return

    # Sort by Monthly Reward descending
    display_results_df = display_results_df.sort_values(
        'Monthly Reward', ascending=False).copy()

    # Format Monthly Reward as currency
    display_results_df['Monthly Reward'] = display_results_df['Monthly Reward'].apply(
        lambda x: f"${x:.2f}")

    # Create styled cap status with better visual indicators
    display_results_df['Cap Status'] = display_results_df.apply(lambda row:
                                                                "🚫 Capped" if row['Cap Reached'] else
                                                                "✅ Under Cap", axis=1)

    # Add ranking column with medal emojis for top 3
    display_results_df.insert(0, 'Rank', range(1, len(display_results_df) + 1))
    display_results_df['Rank'] = display_results_df['Rank'].astype(str)
    if len(display_results_df) >= 1:
        display_results_df.iloc[0, 0] = '🥇'
    if len(display_results_df) >= 2:
        display_results_df.iloc[1, 0] = '🥈'
    if len(display_results_df) >= 3:
        display_results_df.iloc[2, 0] = '🥉'

    # Show table with selected columns (scrollable if many rows)
    st.dataframe(display_results_df[['Rank', 'Card Name', 'Card Type',
                 'Monthly Reward', 'Cap Status']], hide_index=True, use_container_width=True)


def create_summary_dashboard(user_spending_data, best_cards_summary_df, miles_value_cents):
    """Create a summary dashboard with key metrics and insights"""

    st.markdown("## 📊 **Spending & Rewards Summary**")

    # Key metrics in a grid layout
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Monthly Spending",
            f"${user_spending_data['total']:,}",
            help="Your total monthly spending across all categories"
        )

    with col2:
        if len(best_cards_summary_df) > 0:
            best_reward = best_cards_summary_df.iloc[0]['Monthly Reward']
            st.metric(
                "Best Monthly Reward",
                f"${best_reward:.2f}",
                help="Highest monthly reward from any single card"
            )
        else:
            st.metric("Best Monthly Reward", "$0.00")

    with col3:
        if len(best_cards_summary_df) > 0:
            best_annual = best_cards_summary_df.iloc[0]['Monthly Reward'] * 12
            st.metric(
                "Best Annual Reward",
                f"${best_annual:.2f}",
                help="Annual reward from the best single card"
            )
        else:
            st.metric("Best Annual Reward", "$0.00")

    with col4:
        if len(best_cards_summary_df) > 0 and user_spending_data['total'] > 0:
            reward_rate = (
                best_cards_summary_df.iloc[0]['Monthly Reward'] / user_spending_data['total']) * 100
            st.metric(
                "Reward Rate",
                f"{reward_rate:.1f}%",
                help="Reward as percentage of total spending"
            )
        else:
            st.metric("Reward Rate", "0.0%")

    # Spending breakdown chart
    st.markdown("### 💰 Spending Breakdown")

    # Prepare spending data for chart
    spending_categories = {
        'Dining': user_spending_data['dining'],
        'Groceries': user_spending_data['groceries'],
        'Petrol': user_spending_data['petrol'],
        'Transport': user_spending_data['transport'],
        'Streaming': user_spending_data['streaming'],
        'Entertainment': user_spending_data['entertainment'],
        'Utilities': user_spending_data['utilities'],
        'Online': user_spending_data['online'],
        'Travel': user_spending_data['travel'],
        'Overseas': user_spending_data['overseas'],
        'Retail': user_spending_data['retail'],
        'Departmental': user_spending_data['departmental'],
        'Other': user_spending_data['other']
    }

    # Filter out zero spending categories
    spending_categories = {k: v for k,
                           v in spending_categories.items() if v > 0}

    if spending_categories:
        categories = list(spending_categories.keys())
        amounts = list(spending_categories.values())
        spending_df = pd.DataFrame({
            'Category': categories,
            'Amount': amounts
        })

        fig = px.pie(
            spending_df,
            values='Amount',
            names='Category',
            title="Monthly Spending Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_layout(
            title_x=0.5,
            showlegend=True,
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # Insights section
    st.markdown("### 💡 **Key Insights**")

    insights_col1, insights_col2 = st.columns(2)

    with insights_col1:
        # Top spending category
        if spending_categories:
            top_category = max(spending_categories.keys(),
                               key=lambda k: spending_categories[k])
            top_amount = spending_categories[top_category]
            st.info(f"**Highest spending:** {top_category} (${top_amount:,})")

        # Spending level insight
        total_spending = user_spending_data['total']
        if total_spending < 800:
            st.warning(
                "**Low spender:** Consider cards with no minimum spend requirements")
        elif total_spending < 1500:
            st.info("**Medium spender:** You can access most card tiers")
        else:
            st.success(
                "**High spender:** You can maximize rewards with premium cards")

    with insights_col2:
        # Miles valuation insight
        if miles_value_cents <= 2.5:
            st.info("**Miles value:** Economy flights range - good for budget travel")
        elif miles_value_cents <= 6.0:
            st.info("**Miles value:** Business class range - premium travel benefits")
        else:
            st.info("**Miles value:** First class range - luxury travel rewards")

        # Card type recommendation
        if not best_cards_summary_df.empty:
            best_card_type = best_cards_summary_df.iloc[0]['Card Type']
            if best_card_type == 'Miles':
                st.info('✈️ You are likely to benefit most from a miles card.')
            else:
                st.info('💵 You are likely to benefit most from a cashback card.')