import streamlit as st
import pandas as pd
import itertools
from components.single_card_component import single_card_rewards_and_breakdowns
from components.breakdown_format_utils import format_breakdown_df, category_icons
from services.data.card_loader import load_cards_and_models


def render_multi_card_component(user_spending_data, miles_to_sgd_rate=0.02):
    st.subheader("🃏 Multi-Card Monthly Rewards")
    # Get all cards and their single rewards
    single_result = single_card_rewards_and_breakdowns(
        user_spending_data, miles_to_sgd_rate)
    single_df = single_result.summary_df
    # Get best single card reward (float, not $-formatted)
    if not single_df.empty:
        best_single_val = float(single_df.iloc[0]['Monthly Reward (SGD)'])
    else:
        best_single_val = 0
    # Load all cards
    cards = load_cards_and_models()
    card_names = [card.name for card in cards]
    # Compute all unique 2-card combinations
    combos = list(itertools.combinations(cards, 2))
    results = []
    combo_lookup = {}
    for card1, card2 in combos:
        # For now, just sum the rewards from single card logic (simple baseline)
        reward1 = None
        reward2 = None
        for row in single_df.itertuples():
            if row._2 == card1.name:
                reward1 = float(row._5) if isinstance(row._5, (int, float)) or (isinstance(
                    row._5, str) and row._5.replace('$', '').replace(',', '').replace('.', '', 1).isdigit()) else 0
                if isinstance(row._5, str):
                    try:
                        reward1 = float(row._5.replace(
                            '$', '').replace(',', ''))
                    except:
                        reward1 = 0
            if row._2 == card2.name:
                reward2 = float(row._5) if isinstance(row._5, (int, float)) or (isinstance(
                    row._5, str) and row._5.replace('$', '').replace(',', '').replace('.', '', 1).isdigit()) else 0
                if isinstance(row._5, str):
                    try:
                        reward2 = float(row._5.replace(
                            '$', '').replace(',', ''))
                    except:
                        reward2 = 0
        if reward1 is None:
            reward1 = 0
        if reward2 is None:
            reward2 = 0
        combined_reward = reward1 + reward2
        combo_name = f"{card1.name} + {card2.name}"
        results.append({
            'Card Names': combo_name,
            'Monthly Reward (SGD)': combined_reward,
            'vs Best Single': combined_reward - best_single_val
        })
        combo_lookup[combo_name] = (card1, card2, reward1, reward2)
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Monthly Reward (SGD)',
                            ascending=False).reset_index(drop=True)
        df.insert(0, 'Rank', df.index + 1)
        # Format columns
        df['Monthly Reward (SGD)'] = df['Monthly Reward (SGD)'].astype('object')
        df['Monthly Reward (SGD)'] = df['Monthly Reward (SGD)'].apply(
            lambda x: f"${x:,.2f}")
        df['vs Best Single'] = df['vs Best Single'].apply(
            lambda x: f"+${x:,.2f}" if x > 0 else f"${x:,.2f}")
        # Add Reward Rate column
        total_spending = user_spending_data.get('total', 0)
        if total_spending > 0:
            df['Reward Rate'] = df['Monthly Reward (SGD)'].apply(
                lambda x: float(str(x).replace('$','').replace(',','')) / total_spending * 100 if str(x).replace('$','').replace(',','').replace('.','',1).isdigit() else 0)
            df['Reward Rate'] = df['Reward Rate'].astype('object')
            df['Reward Rate'] = df['Reward Rate'].apply(lambda x: f"{x:.2f}%")
        else:
            df['Reward Rate'] = "0.00%"
    if not df.empty:
        top_row = df.iloc[0]
        top_combo_name = top_row['Card Names']
        card1, card2, reward1, reward2 = combo_lookup[top_combo_name]
        combined_reward = reward1 + reward2
        total_spending = user_spending_data.get('total', 0)
        annual_reward = combined_reward * 12
        reward_rate = (combined_reward / total_spending * 100) if total_spending > 0 else 0
        st.markdown("### 🏆 Top Card Pair Metrics")
        # First row: Card Pair, vs Best Single
        card_pair_col, vs_single_col = st.columns([2, 1])
        card_pair_col.metric("🃏 Card Pair", top_combo_name, help="The best two-card combination for your spending.")
        vs_single_col.metric("vs Best Single", f"+${combined_reward-best_single_val:,.2f}" if combined_reward-best_single_val > 0 else f"${combined_reward-best_single_val:,.2f}", help="Difference vs the best single card reward.")
        # Second row: Monthly Reward, Annual Reward, Reward Rate
        monthly_col, annual_col, rate_col = st.columns(3)
        monthly_col.metric("💰 Monthly Reward", f"${combined_reward:,.2f}", help="Combined monthly reward for this pair.")
        annual_col.metric("📅 Annual Reward", f"${annual_reward:,.2f}", help="Projected yearly reward for this pair.")
        rate_col.metric("📈 Reward Rate", f"{reward_rate:.2f}%", help="Percentage of your total spending returned as rewards.")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.Column(),
            "Card Names": st.column_config.Column(),
            "Monthly Reward (SGD)": st.column_config.Column(),
            "Reward Rate": st.column_config.Column(),
            "vs Best Single": st.column_config.Column(),
        }
    )

    # --- Detailed Spending Breakdown for Multi-Card ---
    st.markdown("### 🔎 Detailed Spending Breakdown (Multi-Card)")
    # Card selectors
    all_card_names = [card.name for card in cards]
    default1 = card1.name if 'card1' in locals() else all_card_names[0]
    default2 = card2.name if 'card2' in locals() else all_card_names[1] if len(all_card_names) > 1 else all_card_names[0]
    colA, colB = st.columns(2)
    with colA:
        selected_card1 = st.selectbox("Select Card 1", all_card_names, index=all_card_names.index(default1))
    with colB:
        selected_card2 = st.selectbox("Select Card 2", all_card_names, index=all_card_names.index(default2))

    # Get breakdowns for selected cards
    single_result = single_card_rewards_and_breakdowns(user_spending_data, miles_to_sgd_rate)
    breakdowns = single_result.breakdown_dict
    # Show breakdown for Card 1
    st.markdown(f"#### 🔎 {selected_card1} Spending Breakdown")
    card1_type = next((c.card_type.lower() for c in cards if c.name == selected_card1), 'cashback')
    breakdown1 = breakdowns.get(selected_card1, [])
    breakdown_df1 = format_breakdown_df(breakdown1, card1_type)
    if not breakdown_df1.empty:
        st.dataframe(breakdown_df1, use_container_width=True, hide_index=True,
            column_config={
                "Category": st.column_config.Column(width="small"),
                "Amount": st.column_config.Column(width="small"),
                "Rate": st.column_config.Column(width="small"),
                "Reward": st.column_config.Column(width="small"),
            }
        )
    # Show breakdown for Card 2
    st.markdown(f"#### 🔎 {selected_card2} Spending Breakdown")
    card2_type = next((c.card_type.lower() for c in cards if c.name == selected_card2), 'cashback')
    breakdown2 = breakdowns.get(selected_card2, [])
    breakdown_df2 = format_breakdown_df(breakdown2, card2_type)
    if not breakdown_df2.empty:
        st.dataframe(breakdown_df2, use_container_width=True, hide_index=True,
            column_config={
                "Category": st.column_config.Column(width="small"),
                "Amount": st.column_config.Column(width="small"),
                "Rate": st.column_config.Column(width="small"),
                "Reward": st.column_config.Column(width="small"),
            }
        )
