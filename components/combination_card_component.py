import streamlit as st
import pandas as pd
import plotly.express as px
import re
from services.calculations import find_best_card_combinations, combine_two_cards_rewards


def render_combination_component(filtered_cards_df, best_single_cards_df, detailed_results_df,
                                 user_spending_data, miles_to_sgd_rate, miles_value_cents):
    st.header("🔗 Optimize with Multi-Card Strategy")
    st.write(
        "Find the best two-card combination to maximize rewards while avoiding caps.")

    # Calculate card combinations
    card_combinations_results = find_best_card_combinations(
        filtered_cards_df, user_spending_data, miles_to_sgd_rate, detailed_results_df
    )

    if card_combinations_results:
        # Organize combination data
        combinations_summary_df = pd.DataFrame(card_combinations_results)
        combinations_summary_df = combinations_summary_df.sort_values(
            'Monthly Reward', ascending=False)

        # Get best single card for comparison
        best_single_card_reward = best_single_cards_df.iloc[0]['Monthly Reward']
        best_single_card_name = best_single_cards_df.iloc[0]['Card Name']

        # Display combination results
        display_combination_strategies(
            combinations_summary_df,
            best_single_card_reward,
            best_single_card_name,
            miles_value_cents
        )

        # Show detailed combination breakdown
        render_combination_details(
            combinations_summary_df,
            filtered_cards_df,
            user_spending_data,
            miles_to_sgd_rate,
            best_single_card_reward
        )

    else:
        st.info("No beneficial two-card combinations found for your spending pattern.")
        st.write(
            f"**Best single card:** {best_single_cards_df.iloc[0]['Card Name']} - ${best_single_cards_df.iloc[0]['Monthly Reward']:.2f}/month")


def display_combination_strategies(combinations_df, best_single_reward, best_single_name, miles_value_cents):
    # Always show all combinations in a scrollable table
    if combinations_df.empty:
        st.write("No combinations to display.")
        return

    display_df = combinations_df.copy()
    display_df['vs Best Single'] = display_df['Monthly Reward'].apply(
        lambda reward: f"+${reward - best_single_reward:.2f}" if reward > best_single_reward else f"${reward - best_single_reward:.2f}"
    )
    display_df['Monthly Reward'] = display_df['Monthly Reward'].apply(lambda x: f"${x:.2f}")

    # Add ranking column with medal emojis for top 3
    display_df.insert(0, 'Rank', range(1, len(display_df) + 1))
    display_df['Rank'] = display_df['Rank'].astype(str)
    if len(display_df) >= 1:
        display_df.iloc[0, 0] = '🥇'
    if len(display_df) >= 2:
        display_df.iloc[1, 0] = '🥈'
    if len(display_df) >= 3:
        display_df.iloc[2, 0] = '🥉'

    st.dataframe(
        display_df[['Rank', 'Card Name', 'Categories', 'Monthly Reward', 'vs Best Single']],
        use_container_width=True,
        hide_index=True
    )

    # Comparison chart (show top 10)
    if len(combinations_df) > 0:
        strategy_comparison_chart = create_strategy_comparison_chart(
            combinations_df, best_single_reward, best_single_name
        )
        st.plotly_chart(strategy_comparison_chart, use_container_width=True)

    # Display optimization results
    display_optimization_summary(
        combinations_df, best_single_reward, best_single_name)


def create_strategy_comparison_chart(combinations_df, best_single_reward, best_single_name):
    comparison_strategies = []

    # Add best single card
    comparison_strategies.append({
        'Strategy': f"{best_single_name} (Single)",
        'Monthly Reward': best_single_reward,
        'Strategy Type': 'Single Card'
    })

    # Add top 10 combinations
    for _, combination_data in combinations_df.head(10).iterrows():
        comparison_strategies.append({
            'Strategy': combination_data['Card Name'],
            'Monthly Reward': combination_data['Monthly Reward'],
            'Strategy Type': 'Combination'
        })

    comparison_strategies_df = pd.DataFrame(comparison_strategies)
    comparison_strategies_df = comparison_strategies_df.sort_values(
        'Monthly Reward', ascending=True)

    comparison_chart = px.bar(
        comparison_strategies_df,
        x='Monthly Reward',
        y='Strategy',
        color='Strategy Type',
        title="Single Card vs Multi-Card Strategies",
        labels={'Monthly Reward': 'Monthly Reward'},
        orientation='h'
    )
    comparison_chart.update_layout(height=400)
    return comparison_chart


def display_optimization_summary(combinations_df, best_single_reward, best_single_name):
    if len(combinations_df) > 0:
        optimal_combination = combinations_df.iloc[0]
        reward_improvement = optimal_combination['Monthly Reward'] - \
            best_single_reward

        if reward_improvement > 0:
            st.success(f"""
            **💰 Optimal Strategy: {optimal_combination['Card Name']}**
            
             **Monthly Reward**: ${optimal_combination['Monthly Reward']:.2f}
            
            **Improvement**: +${reward_improvement:.2f}/month vs best single card
            
            **Annual Benefit**: +${reward_improvement * 12:.2f}/year
            """)
        else:
            st.info(f"""
            **🎯 Best Single Card is Still Optimal**
            
            **{best_single_name}** at ${best_single_reward:.2f}/month
            
            No significant benefit from combinations with your spending pattern.
            """)


def render_combination_details(combinations_df, filtered_cards_df, user_spending_data,
                               miles_to_sgd_rate, best_single_reward):
    st.header("🔍 Detailed Multi-Card Rewards Analysis")

    # Combination selection options
    show_limited_combinations = st.checkbox("Show only top 10 combinations", value=True)

    if show_limited_combinations:
        available_combinations_for_detail = combinations_df.head(10)['Card Name'].tolist()
    else:
        # Show all combinations
        available_combinations_for_detail = combinations_df['Card Name'].tolist()

    selected_combination_name = st.selectbox(
        "Select a combination to analyze:",
        options=available_combinations_for_detail,
        index=0,
        help="Select a combination to view detailed reward calculation breakdown"
    )

    if selected_combination_name:
        selected_combination_data = combinations_df[
            combinations_df['Card Name'] == selected_combination_name
        ].iloc[0]

        display_combination_breakdown(
            selected_combination_data,
            selected_combination_name,
            filtered_cards_df,
            user_spending_data,
            miles_to_sgd_rate,
            best_single_reward
        )


def display_combination_breakdown(combination_data, combination_name, filtered_cards_df,
                                  user_spending_data, miles_to_sgd_rate, best_single_reward):
    breakdown_details_column, combination_metrics_column = st.columns([3, 1])

    with breakdown_details_column:
        st.subheader(f"💳 {combination_name}")
        st.write(f"**🎯 Categories:** {combination_data['Categories']}")

        # Parse combination to get individual cards
        individual_card_names = combination_name.split(' + ')

        if len(individual_card_names) == 2:
            # Get card data and calculate detailed breakdown
            first_card_data = filtered_cards_df[filtered_cards_df['Card Name']
                                                == individual_card_names[0]].iloc[0]
            second_card_data = filtered_cards_df[filtered_cards_df['Card Name']
                                                 == individual_card_names[1]].iloc[0]

            detailed_combination_result = combine_two_cards_rewards(
                first_card_data, second_card_data, user_spending_data, miles_to_sgd_rate
            )

            # Enhanced displays
            display_spending_allocation_table(
                detailed_combination_result['allocation'], individual_card_names, filtered_cards_df)

            display_detailed_breakdown_expandable(
                detailed_combination_result['allocation'],
                individual_card_names,
                detailed_combination_result
            )

    with combination_metrics_column:
        st.metric(
            label="Total Monthly Reward",
            value=f"${combination_data['Monthly Reward']:.2f}"
        )

        # Compare with best single card
        reward_improvement = combination_data['Monthly Reward'] - \
            best_single_reward
        if reward_improvement > 0:
            st.success(f"""
            **Better than Single Card! ✅**
            
            Best single: ${best_single_reward:.2f}
            
            Improvement: +${reward_improvement:.2f}/month
            
            Annual benefit: +${reward_improvement * 12:.2f}/year
            """)
        else:
            st.info(f"""
            **Single Card Better**
            
            Best single: ${best_single_reward:.2f}
            
            Difference: ${reward_improvement:.2f}/month
            """)

        st.info("**No Caps Reached** - Combination optimized to avoid caps!")


def display_spending_allocation_table(allocation_data, card_names, filtered_cards_df=None):
    st.write("### 📊 Card Rewards Breakdown")

    # The allocation_data structure is:
    # {
    #   'Card Name 1': {'reward': amount, 'categories': [...], 'details': [...]},
    #   'Card Name 2': {'reward': amount, 'categories': [...], 'details': [...]}
    # }

    allocation_rows = []
    for card_name, card_data in allocation_data.items():
        # Default card type to None
        card_type = None
        if filtered_cards_df is not None and 'Card Type' in filtered_cards_df.columns:
            match = filtered_cards_df[filtered_cards_df['Card Name'] == card_name]
            if not match.empty:
                card_type = match.iloc[0]['Card Type']
        allocation_rows.append({
            'Card': card_name,
            'Card Type': card_type,
            'Monthly Reward': f"${card_data['reward']:.2f}",
            'Categories': ', '.join(card_data['categories']) if card_data['categories'] else 'N/A'
        })

    if allocation_rows:
        allocation_df = pd.DataFrame(allocation_rows)

        # Calculate total reward
        total_reward = sum(card_data['reward']
                           for card_data in allocation_data.values())

        # Add total row
        total_row = {
            'Card': 'Total',
            'Card Type': '',
            'Monthly Reward': f"${total_reward:.2f}",
            'Categories': 'Combined'
        }

        allocation_df = pd.concat(
            [allocation_df, pd.DataFrame([total_row])], ignore_index=True)

        st.dataframe(allocation_df, use_container_width=True, hide_index=True)
    else:
        st.write("No allocation data available")


def display_detailed_breakdown_expandable(allocation_data, card_names, detailed_result):
    """Display detailed breakdown using containers instead of columns"""

    with st.expander("📋 Detailed Spending Breakdown", expanded=False):

        # Display breakdown for each card
        for card_name, card_data in allocation_data.items():
            with st.container():
                st.write(f"**{card_name} Breakdown**")
                if card_data['details']:
                    df = create_detailed_spending_table(
                        card_name, allocation_data, card_data['details'])
                    if not df.empty:
                        st.dataframe(df, use_container_width=True,
                                     hide_index=True)
                    else:
                        st.write("No spending details available for this card")
                else:
                    st.write("No spending details available for this card")

            st.markdown("---")


def create_detailed_spending_table(card_name, allocation_data, details):
    rows = []
    for detail in details:
        # Split by ':' to get category
        if ':' not in detail:
            continue
        category_part, rest = detail.split(':', 1)
        category = category_part.strip()

        # Extract amount spent
        amount_match = re.search(r'\$(\d+)', detail)
        amount = int(amount_match.group(1)) if amount_match else 0

        # Extract cashback or mpd rate
        rate_match = re.search(r'×\s*(\d+(?:\.\d+)?)\s*(%| mpd)', detail)
        if rate_match:
            rate_value = rate_match.group(1)
            rate_unit = rate_match.group(2)
            rate = f"{rate_value}{rate_unit}"
        else:
            # Fallback: try without × symbol
            rate_match_fallback = re.search(
                r'(\d+(?:\.\d+)?)\s*(%| mpd)', detail)
            if rate_match_fallback:
                rate_value = rate_match_fallback.group(1)
                rate_unit = rate_match_fallback.group(2)
                rate = f"{rate_value}{rate_unit}"
            else:
                rate = ""

        # Extract reward - handle both cashback and miles formats
        # For cashback: "Dining: $500.00 × 5% = $25.00"
        # For miles: "Dining: $500.00 × 3 mpd = 1500 miles × $0.020 = $30.00"
        reward_match = re.search(r'=\s*\$(\d+\.\d+)$', detail)
        if reward_match:
            reward = float(reward_match.group(1))
        else:
            # Fallback: try to find any dollar amount at the end
            reward_match_fallback = re.search(r'\$(\d+\.\d+)$', detail)
            reward = float(reward_match_fallback.group(
                1)) if reward_match_fallback else 0.0

        rows.append({
            "Category": category,
            "Amount": f"${amount}",
            "Rate": rate,
            "Reward": f"${reward:.2f}"
        })

    df = pd.DataFrame(rows)

    # Add total row if there are any rows
    if not df.empty:
        total_amount = sum([int(str(row["Amount"]).replace("$", ""))
                           for _, row in df.iterrows()])
        total_reward = sum([float(str(row["Reward"]).replace("$", ""))
                           for _, row in df.iterrows()])

        total_row = pd.DataFrame([{
            "Category": "Total",
            "Amount": f"${total_amount}",
            "Rate": "",
            "Reward": f"${total_reward:.2f}"
        }])

        df = pd.concat([df, total_row], ignore_index=True)

    return df
