import streamlit as st
import pandas as pd
import itertools
from components.single_card_component import single_card_rewards_and_breakdowns
from components.breakdown_format_utils import format_breakdown_df, category_icons, get_ranked_selectbox_options, get_reward_categories_with_icons
from services.data.card_loader import load_cards_and_models


def allocate_spending_two_cards(card1, tier1, card2, tier2, user_spending, miles_to_sgd_rate):
    """
    Allocate user spending optimally between two cards, considering reward rates, caps, and UOB Lady's logic.
    Returns: (reward1, breakdown1, reward2, breakdown2, total_combined_reward)
    """
    def get_rate(card, tier, cat):
        return tier.reward_rates.get(cat, tier.base_rate or 0)

    # Step 1: For each category, decide allocation (ignore UOB Lady's special for now)
    categories = [cat for cat in user_spending.keys() if cat != 'total']
    cap1 = tier1.cap if tier1.cap is not None else float('inf')
    cap2 = tier2.cap if tier2.cap is not None else float('inf')
    used_cap1 = 0
    used_cap2 = 0
    reward1 = 0
    reward2 = 0
    breakdown1 = []
    breakdown2 = []
    for cat in categories:
        amt = user_spending.get(cat, 0)
        if amt == 0:
            continue
        rate1 = get_rate(card1, tier1, cat)
        rate2 = get_rate(card2, tier2, cat)
        if rate1 == 0 and rate2 == 0:
            continue
        if rate1 > 0 and rate2 == 0:
            reward_amt = amt * \
                (rate1 / 100) if card1.card_type.lower() == 'cashback' else amt * \
                rate1 * miles_to_sgd_rate
            reward_amt = min(reward_amt, cap1 - used_cap1)
            reward1 += reward_amt
            used_amt = reward_amt / \
                ((rate1 / 100) if card1.card_type.lower() ==
                 'cashback' else rate1 * miles_to_sgd_rate)
            breakdown1.append(
                {'Category': cat, 'Amount': used_amt, 'Rate': rate1, 'Reward': reward_amt})
            used_cap1 += reward_amt
            continue
        if rate2 > 0 and rate1 == 0:
            reward_amt = amt * \
                (rate2 / 100) if card2.card_type.lower() == 'cashback' else amt * \
                rate2 * miles_to_sgd_rate
            reward_amt = min(reward_amt, cap2 - used_cap2)
            reward2 += reward_amt
            used_amt = reward_amt / \
                ((rate2 / 100) if card2.card_type.lower() ==
                 'cashback' else rate2 * miles_to_sgd_rate)
            breakdown2.append(
                {'Category': cat, 'Amount': used_amt, 'Rate': rate2, 'Reward': reward_amt})
            used_cap2 += reward_amt
            continue
        # Both cards reward this category
        if rate1 >= rate2:
            max_amt1 = (cap1 - used_cap1) / ((rate1 / 100) if card1.card_type.lower()
                                             == 'cashback' else rate1 * miles_to_sgd_rate)
            amt1 = min(amt, max_amt1)
            reward_amt1 = amt1 * (rate1 / 100) if card1.card_type.lower(
            ) == 'cashback' else amt1 * rate1 * miles_to_sgd_rate
            reward1 += reward_amt1
            breakdown1.append({'Category': cat, 'Amount': amt1,
                              'Rate': rate1, 'Reward': reward_amt1})
            used_cap1 += reward_amt1
            amt2 = amt - amt1
            if amt2 > 0:
                max_amt2 = (cap2 - used_cap2) / ((rate2 / 100) if card2.card_type.lower()
                                                 == 'cashback' else rate2 * miles_to_sgd_rate)
                amt2 = min(amt2, max_amt2)
                reward_amt2 = amt2 * (rate2 / 100) if card2.card_type.lower(
                ) == 'cashback' else amt2 * rate2 * miles_to_sgd_rate
                reward2 += reward_amt2
                breakdown2.append(
                    {'Category': cat, 'Amount': amt2, 'Rate': rate2, 'Reward': reward_amt2})
                used_cap2 += reward_amt2
        else:
            max_amt2 = (cap2 - used_cap2) / ((rate2 / 100) if card2.card_type.lower()
                                             == 'cashback' else rate2 * miles_to_sgd_rate)
            amt2 = min(amt, max_amt2)
            reward_amt2 = amt2 * (rate2 / 100) if card2.card_type.lower(
            ) == 'cashback' else amt2 * rate2 * miles_to_sgd_rate
            reward2 += reward_amt2
            breakdown2.append({'Category': cat, 'Amount': amt2,
                              'Rate': rate2, 'Reward': reward_amt2})
            used_cap2 += reward_amt2
            amt1 = amt - amt2
            if amt1 > 0:
                max_amt1 = (cap1 - used_cap1) / ((rate1 / 100) if card1.card_type.lower()
                                                 == 'cashback' else rate1 * miles_to_sgd_rate)
                amt1 = min(amt1, max_amt1)
                reward_amt1 = amt1 * (rate1 / 100) if card1.card_type.lower(
                ) == 'cashback' else amt1 * rate1 * miles_to_sgd_rate
                reward1 += reward_amt1
                breakdown1.append(
                    {'Category': cat, 'Amount': amt1, 'Rate': rate1, 'Reward': reward_amt1})
                used_cap1 += reward_amt1

    # Step 2: Post-process UOB Lady's breakdowns
    def postprocess_uob_ladys(card, breakdown):
        if card.name != "UOB Lady’s":
            return breakdown
        eligible = ['dining', 'entertainment', 'retail', 'travel']
        # Find the eligible category with the highest assigned amount
        eligible_rows = [row for row in breakdown if row['Category'].strip().lower() in eligible]
        if not eligible_rows:
            return breakdown
        # Find the row(s) with the highest amount
        max_amt = max(row['Amount'] for row in eligible_rows)
        # Only pick the first eligible category with the max amount
        special_cat = None
        for row in eligible_rows:
            if row['Amount'] == max_amt:
                special_cat = row['Category'].strip().lower()
                break
        # Debug print
        # print(f"UOB Lady's: setting 4mpd for category: {special_cat}")
        new_breakdown = []
        for row in breakdown:
            cat_lc = row['Category'].strip().lower()
            if cat_lc in eligible:
                if cat_lc == special_cat:
                    rate = 4.0
                else:
                    rate = 0.4
                reward = row['Amount'] * rate * miles_to_sgd_rate
                new_breakdown.append({**row, 'Rate': rate, 'Reward': reward})
            else:
                # For non-eligible categories, never set 4mpd
                new_breakdown.append({**row, 'Rate': row['Rate'] if row['Rate'] != 4.0 else 0.4, 'Reward': row['Amount'] * (row['Rate'] if row['Rate'] != 4.0 else 0.4) * miles_to_sgd_rate if card.name != 'UOB Lady’s' or row['Rate'] == 4.0 else row['Reward']})
        return new_breakdown

    breakdown1 = postprocess_uob_ladys(card1, breakdown1)
    breakdown2 = postprocess_uob_ladys(card2, breakdown2)
    reward1 = sum(row['Reward'] for row in breakdown1)
    reward2 = sum(row['Reward'] for row in breakdown2)
    total_combined_reward = reward1 + reward2
    return reward1, breakdown1, reward2, breakdown2, total_combined_reward


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
        # Use best tier for each card (first tier for now)
        tier1 = card1.tiers[0] if card1.tiers else None
        tier2 = card2.tiers[0] if card2.tiers else None
        if not tier1 or not tier2:
            continue
        reward1, breakdown1, reward2, breakdown2, combined_reward = allocate_spending_two_cards(
            card1, tier1, card2, tier2, user_spending_data, miles_to_sgd_rate)
        combo_name = f"{card1.name} + {card2.name}"
        results.append({
            'Card Names': combo_name,
            'Monthly Reward (SGD)': combined_reward,
            'vs Best Single': combined_reward - best_single_val
        })
        combo_lookup[combo_name] = (
            card1, card2, reward1, reward2, breakdown1, breakdown2)
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Monthly Reward (SGD)',
                            ascending=False).reset_index(drop=True)
        df.insert(0, 'Rank', df.index + 1)

        # Format columns
        df['Monthly Reward (SGD)'] = df['Monthly Reward (SGD)'].astype(
            'object')
        df['Monthly Reward (SGD)'] = df['Monthly Reward (SGD)'].apply(
            lambda x: f"${x:,.2f}")
        df['vs Best Single'] = df['vs Best Single'].apply(
            lambda x: f"+${x:,.2f}" if x > 0 else f"${x:,.2f}")

        # Add Reward Rate column
        total_spending = user_spending_data.get('total', 0)
        if total_spending > 0:
            df['Reward Rate'] = df['Monthly Reward (SGD)'].apply(
                lambda x: float(str(x).replace('$', '').replace(',', '')) / total_spending * 100 if str(x).replace('$', '').replace(',', '').replace('.', '', 1).isdigit() else 0)
            df['Reward Rate'] = df['Reward Rate'].astype('object')
            df['Reward Rate'] = df['Reward Rate'].apply(lambda x: f"{x:.2f}%")
        else:
            df['Reward Rate'] = "0.00%"
    if not df.empty:
        top_row = df.iloc[0]
        top_combo_name = top_row['Card Names']
        card1, card2, reward1, reward2, breakdown1, breakdown2 = combo_lookup[top_combo_name]
        combined_reward = reward1 + reward2
        total_spending = user_spending_data.get('total', 0)
        annual_reward = combined_reward * 12
        reward_rate = (combined_reward / total_spending *
                       100) if total_spending > 0 else 0
        st.markdown("### 🏆 Top Card Pair Metrics")

        # First row: Card Pair, vs Best Single
        card_pair_col, vs_single_col = st.columns([2, 1])
        card_pair_col.metric("🃏 Card Pair", top_combo_name,
                             help="The best two-card combination for your spending.")
        vs_single_col.metric("vs Best Single", f"+${combined_reward-best_single_val:,.2f}" if combined_reward-best_single_val >
                             0 else f"${combined_reward-best_single_val:,.2f}", help="Difference vs the best single card reward.")

        # Second row: Monthly Reward, Annual Reward, Reward Rate
        monthly_col, annual_col, rate_col = st.columns(3)
        monthly_col.metric(
            "💰 Monthly Reward", f"${combined_reward:,.2f}", help="Combined monthly reward for this pair.")
        annual_col.metric(
            "📅 Annual Reward", f"${annual_reward:,.2f}", help="Projected yearly reward for this pair.")
        rate_col.metric("📈 Reward Rate", f"{reward_rate:.2f}%",
                        help="Percentage of your total spending returned as rewards.")

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

    # Detailed Spending Breakdown for Multi-Card
    st.markdown("### 🔎 Detailed Spending Breakdown (Multi-Card)")
    # Card selectors
    all_card_names = [card.name for card in cards]
    default1 = card1.name if 'card1' in locals() else all_card_names[0]
    default2 = card2.name if 'card2' in locals() else all_card_names[1] if len(
        all_card_names) > 1 else all_card_names[0]
    colA, colB = st.columns(2)
    with colA:
        selected_card1 = st.selectbox(
            "Select Card 1", all_card_names, index=all_card_names.index(default1))
    with colB:
        selected_card2 = st.selectbox(
            "Select Card 2", all_card_names, index=all_card_names.index(default2))

    # Get breakdowns for selected cards
    # Use the actual allocation breakdowns for the selected card pair
    combo_name = f"{selected_card1} + {selected_card2}"
    reverse_combo_name = f"{selected_card2} + {selected_card1}"
    if combo_name in combo_lookup:
        _, _, _, _, breakdown1, breakdown2 = combo_lookup[combo_name]
    elif reverse_combo_name in combo_lookup:
        _, _, _, _, breakdown2, breakdown1 = combo_lookup[reverse_combo_name]
    else:
        breakdown1, breakdown2 = [], []

    # Show breakdown for Card 1
    st.markdown(f"#### 🔎 {selected_card1} Spending Breakdown")
    card1_type = next((c.card_type.lower()
                      for c in cards if c.name == selected_card1), 'cashback')
    card1_obj = next((c for c in cards if c.name == selected_card1), None)
    tier1_obj = card1_obj.tiers[0] if card1_obj and card1_obj.tiers else None
    cats1_str = get_reward_categories_with_icons(
        card1_obj, tier1_obj, as_string=True)
    st.caption(f"Reward Categories: {cats1_str}")
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
    card2_type = next((c.card_type.lower()
                      for c in cards if c.name == selected_card2), 'cashback')
    card2_obj = next((c for c in cards if c.name == selected_card2), None)
    tier2_obj = card2_obj.tiers[0] if card2_obj and card2_obj.tiers else None
    cats2_str = get_reward_categories_with_icons(
        card2_obj, tier2_obj, as_string=True)
    st.caption(f"Reward Categories: {cats2_str}")
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
