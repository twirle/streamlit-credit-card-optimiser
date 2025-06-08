import streamlit as st
import plotly.express as px
import pandas as pd


def create_spending_inputs():
    st.sidebar.header("📊 Your Monthly Spending")

    # Miles valuation input
    st.sidebar.header("💰 Miles Valuation")
    miles_value_cents = st.sidebar.number_input(
        "Value per mile (cents SGD)",
        min_value=1.0,
        max_value=10.0,
        value=2.0,
        step=0.1,
        help="Average redemption value per mile. Typical range: 1.5-8 cents depending on redemption method."
    )
    miles_value_sgd = miles_value_cents / 100

    # Spending inputs
    dining = st.sidebar.number_input(
        "Dining", min_value=0, value=250, step=50)
    groceries = st.sidebar.number_input(
        "Groceries", min_value=0, value=450, step=50)
    petrol = st.sidebar.number_input(
        "Petrol", min_value=0, value=0, step=50)
    transport = st.sidebar.number_input(
        "Transport", min_value=0, value=150, step=25)
    streaming = st.sidebar.number_input(
        "Streaming", min_value=0, value=25, step=25)
    entertainment = st.sidebar.number_input(
        "Entertainment", min_value=0, value=50, step=25)
    utilities = st.sidebar.number_input(
        "Utilities", min_value=0, value=150, step=25)
    online = st.sidebar.number_input(
        "Online Shopping", min_value=0, value=250, step=50)
    travel = st.sidebar.number_input(
        "Travel", min_value=0, value=0, step=50)
    overseas = st.sidebar.number_input(
        "Overseas Spend", min_value=0, value=50, step=50)
    other = st.sidebar.number_input(
        "Other Spending", min_value=0, value=150, step=50)

    user_spending = {
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
        'total': dining + groceries + petrol + transport + streaming + entertainment + utilities + online + travel + overseas + other
    }

    st.sidebar.write(
        f"**Total Monthly Spend: SGD {user_spending['total']:,.0f}**")

    return user_spending, miles_value_sgd, miles_value_cents


def create_filters(df):
    st.sidebar.header("🔍 Filters")
    card_types = st.sidebar.multiselect(
        "Card Types",
        options=df['Type'].unique(),
        default=df['Type'].unique()
    )
    return card_types


def create_spending_pie_chart(user_spending):
    spending_data = {k: v for k, v in user_spending.items()
                     if k != 'total' and v > 0}
    if spending_data:
        fig_pie = px.pie(
            values=list(spending_data.values()),
            names=list(spending_data.keys()),
            title="Monthly Spending by Category"
        )
        return fig_pie
    return None


def display_miles_info(miles_value_cents):
    return st.info(f"""
    **Miles Valuation Guide:**
    • Economy flights: 1.5-2.5¢
    • Business class: 3-6¢  
    • First class: 6-8¢+
    • Currently using: **{miles_value_cents:.1f}¢** per mile
    """)


def display_best_single_card(display_results_df):
    if len(display_results_df) > 0:
        best_card = display_results_df.iloc[0]
        cap_status = "⚠️ Cap reached" if best_card['Cap Reached'] else "✅ Under cap"

        st.success(f"""
        **🎯 Best Single Card:**
        
        **{best_card['Card Name']}** ({best_card['Issuer']})
        
        🎯 **Categories:** {best_card['Categories']}
        
        💰 Monthly Value: SGD {best_card['Monthly Reward']:.2f}
        
        {cap_status}
        """)


def display_card_details(best_tier, selected_card_name, card_rows, user_spending):
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"💳 {selected_card_name}")
        st.write(f"**🎯 Categories:** {best_tier['Categories']}")

        if len(card_rows) > 1:
            st.info(
                f"**Optimal tier selected:** Min spend ${best_tier['Min Spend']} (out of {len(card_rows)} tiers)")

        for detail in best_tier['Details']:
            st.write(f"• {detail}")

        if best_tier['Original Reward'] != best_tier['Monthly Reward']:
            st.write(
                f"**Total before cap:** ${best_tier['Original Reward']:.2f}")

        st.write(
            f"**Final monthly reward:** ${best_tier['Monthly Reward']:.2f}")

    with col2:
        if pd.notna(best_tier['Cap']) and best_tier['Cap'] != 'No Cap':
            if best_tier['Cap Reached']:
                st.error(f"""
                **Cap Reached! 🚫**
                
                Monthly cap: ${best_tier['Cap']}
                
                Amount over cap: ${best_tier['Cap Difference']:.2f}
                
                You're losing ${best_tier['Cap Difference']:.2f}/month
                """)
            else:
                st.success(f"""
                **Under Cap ✅**
                
                Monthly cap: ${best_tier['Cap']}
                
                Room to earn: ${best_tier['Cap Difference']:.2f}
                """)
        else:
            st.info("**No Cap** - Unlimited earning potential!")

        if not best_tier['Min Spend Met']:
            st.warning(f"""
            **Minimum Spend Not Met ⚠️**
            
            Required: ${best_tier['Min Spend']}
            
            Your spend: ${user_spending['total']}
            
            Need ${best_tier['Min Spend'] - user_spending['total']} more
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
    display_df['Monthly Reward'] = display_df['Monthly Reward'].round(
        2)

    display_df['Cap Status'] = display_df.apply(lambda row:
                                                f"✅ Capped" if row['Cap Reached'] else
                                                "Under Cap", axis=1)

    st.dataframe(
        display_df[['Card Name', 'Issuer', 'Categories',
                    'Type', 'Monthly Reward', 'Cap Status']],
        use_container_width=True
    )
