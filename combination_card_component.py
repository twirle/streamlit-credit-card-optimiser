import streamlit as st
import pandas as pd
import plotly.express as px
from calculations import find_best_card_combinations, combine_two_cards_rewards


def render_combination_component(filtered_cards_df, best_single_cards_df, detailed_results_df,
                                 user_spending_data, miles_to_sgd_rate, miles_value_cents):
    st.header("🔗 Optimize with Multi-Card Strategy")
    st.write(
        "Find the best two-card combination to maximize rewards while avoiding caps")

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
        _render_combination_details(
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
    st.subheader("🏆 Top Multi-Card Strategies")

    # Prepare display data
    top_combinations_df = combinations_df.head(5).copy()
    top_combinations_df['Monthly Reward'] = top_combinations_df['Monthly Reward'].round(
        2)
    top_combinations_df['vs Best Single'] = top_combinations_df['Monthly Reward'].apply(
        lambda reward: f"+${reward - best_single_reward:.2f}" if reward > best_single_reward else f"${reward - best_single_reward:.2f}"
    )

    # Display combinations table
    st.dataframe(
        top_combinations_df[['Card Name', 'Issuer',
                             'Categories', 'Monthly Reward', 'vs Best Single']],
        use_container_width=True
    )

    # Comparison chart
    if len(combinations_df) > 0:
        strategy_comparison_chart = _create_strategy_comparison_chart(
            combinations_df, best_single_reward, best_single_name
        )
        st.plotly_chart(strategy_comparison_chart, use_container_width=True)

    # Display optimization results
    display_optimization_summary(
        combinations_df, best_single_reward, best_single_name)


def _create_strategy_comparison_chart(combinations_df, best_single_reward, best_single_name):
    comparison_strategies = []

    # Add best single card
    comparison_strategies.append({
        'Strategy': f"{best_single_name} (Single)",
        'Monthly Reward': best_single_reward,
        'Strategy Type': 'Single Card'
    })

    # Add top 5 combinations
    for _, combination_data in combinations_df.head(5).iterrows():
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
            **🎯 Optimal Strategy: {optimal_combination['Card Name']}**
            
            💰 Monthly Reward: ${optimal_combination['Monthly Reward']:.2f}
            
            📈 Improvement: +${reward_improvement:.2f}/month vs best single card
            
            📅 Annual Benefit: +${reward_improvement * 12:.2f}/year
            """)
        else:
            st.info(f"""
            **🎯 Best Single Card is Still Optimal**
            
            **{best_single_name}** at ${best_single_reward:.2f}/month
            
            No significant benefit from combinations with your spending pattern.
            """)


def _render_combination_details(combinations_df, filtered_cards_df, user_spending_data,
                                miles_to_sgd_rate, best_single_reward):
    st.header("🔍 Detailed Multi-Card Analysis")

    top_combinations_for_detail = combinations_df.head(5)['Card Name'].tolist()
    selected_combination_name = st.selectbox(
        "Select a combination to analyze:",
        options=top_combinations_for_detail,
        index=0,
        help="Showing top 5 combinations for detailed analysis"
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
            first_card_data = filtered_cards_df[filtered_cards_df['Name']
                                                == individual_card_names[0]].iloc[0]
            second_card_data = filtered_cards_df[filtered_cards_df['Name']
                                                 == individual_card_names[1]].iloc[0]

            detailed_combination_result = combine_two_cards_rewards(
                first_card_data, second_card_data, user_spending_data, miles_to_sgd_rate
            )

            # Display breakdown for each card
            display_individual_card_contribution(
                individual_card_names[0],
                detailed_combination_result['details_card1'],
                detailed_combination_result['card1_reward']
            )

            display_individual_card_contribution(
                individual_card_names[1],
                detailed_combination_result['details_card2'],
                detailed_combination_result['card2_reward']
            )

            # Show spending allocation
            display_spending_allocation(
                detailed_combination_result['allocation'], individual_card_names)

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


def display_individual_card_contribution(card_name, card_details, card_reward):
    st.write(f"### {card_name} Contribution")
    if card_details:
        for detail in card_details:
            st.write(f"• {detail}")
    else:
        st.write("• No spending allocated to this card")

    st.write(f"**{card_name} Reward:** ${card_reward:.2f}")


def display_spending_allocation(allocation_data, card_names):
    st.write("### Optimal Spending Allocation")
    for category, allocation in allocation_data.items():
        if allocation['card1'] > 0 or allocation['card2'] > 0:
            st.write(
                f"• **{category.capitalize()}:** {card_names[0]}: ${allocation['card1']:.0f}, {card_names[1]}: ${allocation['card2']:.0f}")
