import streamlit as st
import pandas as pd
import itertools
from components.single_card_component import single_card_rewards_and_breakdowns
from components.breakdown_format_utils import format_breakdown_df, category_icons, get_ranked_selectbox_options, get_reward_categories_with_icons
from services.data.card_loader import load_cards_and_models
from components.card_calculation_utils import calculate_miles_card_with_bonus_cap, calculate_uob_ladys_rewards, UOB_LADYS_GROUP_MAP, calculate_uob_visa_signature_rewards
from itertools import combinations


def allocate_spending_two_cards(card1, tier1, card2, tier2, user_spending, miles_to_sgd_rate):
    """
    Allocate user spending optimally between two cards, considering reward rates, caps, and UOB Lady's logic.
    Returns: (reward1, breakdown1, reward2, breakdown2, total_combined_reward)
    """
    def get_rate(card, tier, cat):
        return tier.reward_rates.get(cat, tier.base_rate or 0)

    # Helper to check if card is Lady's or Solitaire
    def is_ladys(card):
        return "UOB Lady" in card.name and "Solitaire" not in card.name
    def is_solitaire(card):
        return "UOB Lady" in card.name and "Solitaire" in card.name
    def is_uob_visa_signature(card):
        return "UOB Visa Signature" in card.name

    # Use shared group definitions for Lady's logic
    group_map = UOB_LADYS_GROUP_MAP
    group_names = list(group_map.keys())
    categories = [cat for cat in user_spending.keys() if cat != 'total']

    # Helper to allocate spending for a given Lady's group assignment
    def allocate_ladys_groups(ladys_card, ladys_tier, other_card, other_tier, user_spending, miles_to_sgd_rate, selected_groups):
        # 1. Allocate up to cap in selected groups to Lady's
        group_cap = ladys_tier.cap if ladys_tier.cap is not None else float('inf')
        ladys_spending = {cat: 0 for cat in categories}
        other_spending = {cat: 0 for cat in categories}
        # For each selected group, allocate up to cap to Lady's
        for g in selected_groups:
            group_cats = group_map[g]
            group_total = sum(user_spending.get(cat, 0) for cat in group_cats)
            cap_left = min(group_total, group_cap)
            # Allocate to Lady's up to cap, rest to other card
            for cat in group_cats:
                amt = user_spending.get(cat, 0)
                if amt == 0:
                    continue
                amt_ladys = min(amt, cap_left)
                ladys_spending[cat] += amt_ladys
                cap_left -= amt_ladys
                amt_other = amt - amt_ladys
                if amt_other > 0:
                    other_spending[cat] += amt_other
        # All other categories (not in selected groups) go to other card
        for g, group_cats in group_map.items():
            if g not in selected_groups:
                for cat in group_cats:
                    amt = user_spending.get(cat, 0)
                    if amt > 0:
                        other_spending[cat] += amt
        # Any categories not in group_map (e.g., groceries, online, etc.) go to other card
        for cat in categories:
            if not any(cat in group_map[g] for g in group_map):
                amt = user_spending.get(cat, 0)
                if amt > 0:
                    other_spending[cat] += amt
        # 2. Calculate rewards for each card
        reward_ladys, breakdown_ladys = calculate_uob_ladys_rewards(ladys_spending, miles_to_sgd_rate, ladys_tier, is_solitaire=(len(selected_groups) == 2))
        # For the other card, use the generic logic (single card reward for the allocated spending)
        reward_other = 0
        breakdown_other = []
        base_rate = other_tier.base_rate or 0
        for cat, amt in other_spending.items():
            if amt == 0:
                continue
            rate = other_tier.reward_rates.get(cat, base_rate)
            if other_card.card_type.lower() == 'cashback':
                reward = amt * (rate / 100)
            elif other_card.card_type.lower() == 'miles':
                reward = amt * rate * miles_to_sgd_rate
            else:
                reward = 0
            reward_other += reward
            breakdown_other.append({'Category': cat, 'Amount': amt, 'Rate': rate, 'Reward': reward})
        total_reward = reward_ladys + reward_other
        return total_reward, reward_ladys, breakdown_ladys, reward_other, breakdown_other

    # If either card is Lady's or Solitaire, try all valid group assignments
    if is_ladys(card1) or is_solitaire(card1):
        n_groups = 2 if is_solitaire(card1) else 1
        best = None
        for selected_groups in combinations(group_names, n_groups):
            result = allocate_ladys_groups(card1, tier1, card2, tier2, user_spending, miles_to_sgd_rate, selected_groups)
            if best is None or result[0] > best[0]:
                best = result
        # Unpack best result
        _, reward1, breakdown1, reward2, breakdown2 = best
        return reward1, breakdown1, reward2, breakdown2, reward1 + reward2
    if is_ladys(card2) or is_solitaire(card2):
        n_groups = 2 if is_solitaire(card2) else 1
        best = None
        for selected_groups in combinations(group_names, n_groups):
            result = allocate_ladys_groups(card2, tier2, card1, tier1, user_spending, miles_to_sgd_rate, selected_groups)
            # Swap breakdowns/rewards for card1/card2
            total, reward2, breakdown2, reward1, breakdown1 = result
            if best is None or total > best[0]:
                best = (total, reward1, breakdown1, reward2, breakdown2)
        # Unpack best result
        _, reward1, breakdown1, reward2, breakdown2 = best
        return reward1, breakdown1, reward2, breakdown2, reward1 + reward2
    if is_uob_visa_signature(card1) or is_uob_visa_signature(card2):
        # Optimal allocation for UOB Visa Signature + any card, with cap overflow logic and tier re-evaluation
        fcy_group = ['fcy']
        non_fcy_group = ['dining', 'groceries', 'petrol', 'simplygo', 'entertainment', 'retail']
        all_groups = fcy_group + non_fcy_group
        if is_uob_visa_signature(card1):
            visa_card, visa_tier, other_card, other_tier = card1, tier1, card2, tier2
        else:
            visa_card, visa_tier, other_card, other_tier = card2, tier2, card1, tier1
        base_rate_visa = visa_tier.base_rate or 0.4
        bonus_rate_visa = 4.0
        min_spend = visa_tier.min_spend or 1000
        cap = visa_tier.cap or 1200
        base_rate_other = other_tier.base_rate or 0
        cap_other = other_tier.cap if other_tier.cap is not None else float('inf')
        # Track cap usage for both cards
        visa_cap_used_fcy = 0
        visa_cap_used_nonfcy = 0
        other_cap_used = {cat: 0 for cat in categories}
        # Track allocations for min spend check
        allocated_fcy = 0
        allocated_nonfcy = 0
        # Build breakdowns
        visa_breakdown = []
        other_breakdown = []
        visa_reward = 0
        other_reward = 0
        # Track allocations for SC Smart (or other min spend tier cards)
        other_allocated_total = 0
        other_allocated_by_cat = {cat: 0 for cat in categories}
        for cat in categories:
            amt_left = user_spending.get(cat, 0)
            if amt_left == 0:
                continue
            is_fcy = cat in fcy_group
            is_nonfcy = cat in non_fcy_group
            # Determine UOB Visa Signature's rate and cap for this category
            if is_fcy:
                visa_min_met = True  # We'll check min spend after allocation
                visa_cap_left = cap - visa_cap_used_fcy
                visa_rate = bonus_rate_visa if visa_cap_left > 0 else base_rate_visa
            elif is_nonfcy:
                visa_min_met = True
                visa_cap_left = cap - visa_cap_used_nonfcy
                visa_rate = bonus_rate_visa if visa_cap_left > 0 else base_rate_visa
            else:
                visa_min_met = False
                visa_cap_left = 0
                visa_rate = base_rate_visa
            # Determine other card's rate and cap for this category (tier will be re-evaluated after allocation)
            other_rate = other_tier.reward_rates.get(cat, base_rate_other)
            other_cap_left = cap_other - other_cap_used.get(cat, 0)
            visa_reward_per_dollar = visa_rate * miles_to_sgd_rate if visa_card.card_type.lower() == 'miles' else visa_rate / 100
            other_reward_per_dollar = other_rate * miles_to_sgd_rate if other_card.card_type.lower() == 'miles' else other_rate / 100
            # Allocate to card with higher reward per dollar first, up to cap
            alloc_options = [
                (visa_card, visa_rate, visa_reward_per_dollar, visa_cap_left, True),
                (other_card, other_rate, other_reward_per_dollar, other_cap_left, False)
            ]
            alloc_options.sort(key=lambda x: x[2], reverse=True)  # highest reward per dollar first
            amt_remaining = amt_left
            for card, rate, reward_per_dollar, cap_left, is_visa_card in alloc_options:
                if amt_remaining <= 0 or cap_left <= 0 or reward_per_dollar == 0:
                    continue
                amt_to_card = min(amt_remaining, cap_left)
                if amt_to_card <= 0:
                    continue
                if is_visa_card:
                    if is_fcy:
                        visa_cap_used_fcy += amt_to_card
                        allocated_fcy += amt_to_card
                    elif is_nonfcy:
                        visa_cap_used_nonfcy += amt_to_card
                        allocated_nonfcy += amt_to_card
                    reward_amt = amt_to_card * reward_per_dollar
                    visa_breakdown.append({'Category': cat, 'Amount': amt_to_card, 'Rate': rate, 'Reward': reward_amt})
                    visa_reward += reward_amt
                else:
                    other_cap_used[cat] += amt_to_card
                    other_allocated_total += amt_to_card
                    other_allocated_by_cat[cat] += amt_to_card
                    reward_amt = amt_to_card * reward_per_dollar
                    other_breakdown.append({'Category': cat, 'Amount': amt_to_card, 'Rate': rate, 'Reward': reward_amt})
                    other_reward += reward_amt
                amt_remaining -= amt_to_card
        # After allocation, check if allocated_fcy and allocated_nonfcy meet min spend for UOB Visa Signature
        if allocated_fcy < min_spend:
            for d in visa_breakdown:
                if d['Category'] in fcy_group:
                    d['Rate'] = base_rate_visa
                    d['Reward'] = d['Amount'] * (base_rate_visa * miles_to_sgd_rate if visa_card.card_type.lower() == 'miles' else base_rate_visa / 100)
            visa_reward = sum(d['Reward'] for d in visa_breakdown)
        if allocated_nonfcy < min_spend:
            for d in visa_breakdown:
                if d['Category'] in non_fcy_group:
                    d['Rate'] = base_rate_visa
                    d['Reward'] = d['Amount'] * (base_rate_visa * miles_to_sgd_rate if visa_card.card_type.lower() == 'miles' else base_rate_visa / 100)
            visa_reward = sum(d['Reward'] for d in visa_breakdown)
        # After allocation, re-evaluate tier for other card (e.g., SC Smart)
        # Find the best tier for the allocated total
        if hasattr(other_card, 'tiers') and other_card.tiers and len(other_card.tiers) > 1:
            # Sort tiers by min_spend descending (higher min spend = higher tier)
            sorted_tiers = sorted(other_card.tiers, key=lambda t: (t.min_spend or 0), reverse=True)
            selected_tier = sorted_tiers[-1]
            for t in sorted_tiers:
                if (t.min_spend or 0) <= other_allocated_total:
                    selected_tier = t
                    break
            # Rebuild other_breakdown and other_reward using the selected tier's rates and cap
            base_rate_selected = selected_tier.base_rate or 0
            cap_selected = selected_tier.cap if selected_tier.cap is not None else float('inf')
            cap_used_selected = {cat: 0 for cat in categories}
            new_other_breakdown = []
            new_other_reward = 0
            for cat in categories:
                amt = other_allocated_by_cat[cat]
                if amt == 0:
                    continue
                rate = selected_tier.reward_rates.get(cat, base_rate_selected)
                cap_left = cap_selected - cap_used_selected[cat]
                amt_to_card = min(amt, cap_left)
                if amt_to_card > 0:
                    reward_amt = amt_to_card * (rate / 100 if other_card.card_type.lower() == 'cashback' else rate * miles_to_sgd_rate)
                    new_other_breakdown.append({'Category': cat, 'Amount': amt_to_card, 'Rate': rate, 'Reward': reward_amt})
                    new_other_reward += reward_amt
                    cap_used_selected[cat] += amt_to_card
            other_breakdown = new_other_breakdown
            other_reward = new_other_reward
        if is_uob_visa_signature(card1):
            return visa_reward, visa_breakdown, other_reward, other_breakdown, visa_reward + other_reward
        else:
            return other_reward, other_breakdown, visa_reward, visa_breakdown, visa_reward + other_reward
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
        # Calculate effective reward for each card for this category
        rate1 = get_rate(card1, tier1, cat)
        rate2 = get_rate(card2, tier2, cat)
        is_cashback1 = card1.card_type.lower() == 'cashback'
        is_cashback2 = card2.card_type.lower() == 'cashback'
        reward_per_dollar1 = (rate1 / 100) if is_cashback1 else rate1 * miles_to_sgd_rate
        reward_per_dollar2 = (rate2 / 100) if is_cashback2 else rate2 * miles_to_sgd_rate
        # Allocate to card with higher reward per dollar, up to its cap
        # Calculate remaining cap for each card
        rem_cap1 = cap1 - used_cap1
        rem_cap2 = cap2 - used_cap2
        # Max amount that can be allocated to each card before hitting cap
        max_amt1 = rem_cap1 / reward_per_dollar1 if reward_per_dollar1 > 0 else 0
        max_amt2 = rem_cap2 / reward_per_dollar2 if reward_per_dollar2 > 0 else 0
        # Decide allocation
        if reward_per_dollar1 >= reward_per_dollar2:
            amt1 = min(amt, max_amt1)
            reward_amt1 = amt1 * reward_per_dollar1
            reward1 += reward_amt1
            breakdown1.append({'Category': cat, 'Amount': amt1, 'Rate': rate1, 'Reward': reward_amt1})
            used_cap1 += reward_amt1
            amt2 = amt - amt1
            if amt2 > 0 and reward_per_dollar2 > 0:
                amt2 = min(amt2, max_amt2)
                reward_amt2 = amt2 * reward_per_dollar2
                reward2 += reward_amt2
                breakdown2.append({'Category': cat, 'Amount': amt2, 'Rate': rate2, 'Reward': reward_amt2})
                used_cap2 += reward_amt2
        else:
            amt2 = min(amt, max_amt2)
            reward_amt2 = amt2 * reward_per_dollar2
            reward2 += reward_amt2
            breakdown2.append({'Category': cat, 'Amount': amt2, 'Rate': rate2, 'Reward': reward_amt2})
            used_cap2 += reward_amt2
            amt1 = amt - amt2
            if amt1 > 0 and reward_per_dollar1 > 0:
                amt1 = min(amt1, max_amt1)
                reward_amt1 = amt1 * reward_per_dollar1
                reward1 += reward_amt1
                breakdown1.append({'Category': cat, 'Amount': amt1, 'Rate': rate1, 'Reward': reward_amt1})
                used_cap1 += reward_amt1
    # Post-process UOB Lady's and Trust Cashback as before (if needed)
    # ... existing post-processing logic ...
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
    # Cap logic for breakdown
    capped_reward1 = None
    capped_rate1 = None
    if tier1_obj and tier1_obj.cap is not None:
        uncapped_total1 = sum(float(d['Reward']) for d in breakdown1 if isinstance(d, dict) and 'Reward' in d)
        if uncapped_total1 > tier1_obj.cap:
            capped_reward1 = tier1_obj.cap
            total_amount1 = sum(float(d['Amount']) for d in breakdown1 if isinstance(d, dict) and 'Amount' in d)
            capped_rate1 = (capped_reward1 / total_amount1 * 100) if total_amount1 > 0 else 0
    breakdown_df1 = format_breakdown_df(breakdown1, card1_type, capped_reward=capped_reward1, capped_rate=capped_rate1)
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
    capped_reward2 = None
    capped_rate2 = None
    if tier2_obj and tier2_obj.cap is not None:
        uncapped_total2 = sum(float(d['Reward']) for d in breakdown2 if isinstance(d, dict) and 'Reward' in d)
        if uncapped_total2 > tier2_obj.cap:
            capped_reward2 = tier2_obj.cap
            total_amount2 = sum(float(d['Amount']) for d in breakdown2 if isinstance(d, dict) and 'Amount' in d)
            capped_rate2 = (capped_reward2 / total_amount2 * 100) if total_amount2 > 0 else 0
    breakdown_df2 = format_breakdown_df(breakdown2, card2_type, capped_reward=capped_reward2, capped_rate=capped_rate2)
    if not breakdown_df2.empty:
        st.dataframe(breakdown_df2, use_container_width=True, hide_index=True,
                     column_config={
                         "Category": st.column_config.Column(width="small"),
                         "Amount": st.column_config.Column(width="small"),
                         "Rate": st.column_config.Column(width="small"),
                         "Reward": st.column_config.Column(width="small"),
                     }
                     )
