import streamlit as st
import pandas as pd
from collections import namedtuple
from components.breakdown_format_utils import format_breakdown_df, get_ranked_selectbox_options
from components.card_calculation_utils import calculate_uob_ladys_rewards, calculate_trust_cashback_rewards
from components.state.session import (
    get_selected_card_display, set_selected_card_display, get_user_spending, set_user_spending, initialize_spending_state
)
from components.inputs.spending_inputs import DEFAULT_SPENDING_VALUES

SingleCardRewardsResult = namedtuple('SingleCardRewardsResult', [
    'summary_df', 'breakdown_dict']
)


def calculate_cashback_card_rewards(card, tier, user_spending):
    base_rate = tier.base_rate or 0
    reward = 0
    cap = tier.cap
    cap_remaining = cap if cap is not None else float('inf')
    category_agg = {}
    for cat, amount in user_spending.items():
        if cat == 'total':
            continue
        cat_key = cat.strip().lower()
        rate = tier.reward_rates.get(cat_key, base_rate)
        reward_for_cat = amount * (rate / 100)
        # Always show the potential reward for each category
        if cat not in category_agg:
            category_agg[cat] = {
                'Category': cat,
                'Amount': amount,
                'Rate': rate,
                'Reward': reward_for_cat
            }
        else:
            category_agg[cat]['Amount'] += amount
            category_agg[cat]['Reward'] += reward_for_cat
        reward += reward_for_cat
    # The total reward will be capped in the summary, but per-category shows potential
    details = list(category_agg.values())
    return reward, details

def calculate_miles_card_rewards(card, tier, user_spending, miles_to_sgd_rate):
    base_rate = tier.base_rate or 0
    reward = 0
    details = []
    for cat, amount in user_spending.items():
        if cat == 'total':
            continue
        cat_key = cat.strip().lower()
        rate = tier.reward_rates.get(cat_key, base_rate)
        reward_for_cat = amount * rate * miles_to_sgd_rate
        details.append({
            'Category': cat,
            'Amount': amount,
            'Rate': rate,
            'Reward': reward_for_cat
        })
        reward += reward_for_cat
    return reward, details


def calculate_card_tier_reward(card, tier, user_spending, miles_to_sgd_rate):
    if hasattr(card, 'tiers') and len(card.tiers) > 1:
        eligible_tiers = sorted(card.tiers, key=lambda t: (t.min_spend or 0))
        selected_tier = None
        for t in eligible_tiers:
            if card.card_type.lower() == 'cashback':
                total_eligible_spend = sum(
                    amount for cat, amount in user_spending.items() if cat != 'total')
            else:
                eligible_cats = list(t.reward_rates.keys())
                total_eligible_spend = sum(user_spending.get(
                    cat.strip().lower(), 0) for cat in eligible_cats)
            if t.min_spend is None or total_eligible_spend >= (t.min_spend or 0):
                selected_tier = t
        if selected_tier is None:
            # No eligible tier, use a base tier with only the base rate
            base_tier = card.tiers[0]  # lowest tier, for base_rate
            tier = type(base_tier)(
                min_spend=None,
                cap=None,
                reward_rates={},  # no bonus rates
                base_rate=base_tier.base_rate,
                description="Base Rate"
            )
        else:
            tier = selected_tier
    base_rate = tier.base_rate or 0
    bonus_categories = [cat for cat,
                        rate in tier.reward_rates.items() if rate > base_rate]
    bonus_spend = sum(user_spending.get(cat, 0) for cat in bonus_categories)
    if card.card_type.lower() == 'cashback':
        min_spend_met = (tier.min_spend is None) or (sum(
            amount for cat, amount in user_spending.items() if cat != 'total') >= (tier.min_spend or 0))
    else:
        min_spend_met = (tier.min_spend is None) or (
            bonus_spend >= tier.min_spend)
    reward = 0
    details = []

    # Special logic for UOB Lady's and Lady's Solitaire
    if "UOB Lady" in card.name:
        is_solitaire = "Solitaire" in card.name
        from components.card_calculation_utils import calculate_uob_ladys_rewards
        reward, details = calculate_uob_ladys_rewards(
            user_spending, miles_to_sgd_rate, tier, is_solitaire=is_solitaire)
    # Special logic for UOB Visa Signature
    elif "UOB Visa Signature" in card.name:
        from components.card_calculation_utils import calculate_uob_visa_signature_rewards
        reward, details = calculate_uob_visa_signature_rewards(
            user_spending, miles_to_sgd_rate, tier)
    # Special logic for Trust Cashback
    elif card.name == "Trust Cashback":
        reward, details = calculate_trust_cashback_rewards(
            user_spending, tier)
    # Special logic for miles cards with a cap and bonus categories
    elif card.card_type.lower() == 'miles' and tier.cap is not None and bonus_categories:
        from components.card_calculation_utils import calculate_miles_card_with_bonus_cap
        reward, details = calculate_miles_card_with_bonus_cap(
            user_spending, miles_to_sgd_rate, tier, bonus_categories)
    else:
        if card.card_type.lower() == 'cashback':
            reward, details = calculate_cashback_card_rewards(card, tier, user_spending)
        elif card.card_type.lower() == 'miles':
            reward, details = calculate_miles_card_rewards(card, tier, user_spending, miles_to_sgd_rate)
        else:
            # fallback: treat as cashback
            reward, details = calculate_cashback_card_rewards(card, tier, user_spending)
    # Recalculate min_spend_met for the selected tier
    if card.card_type.lower() == 'cashback':
        min_spend_met = (tier.min_spend is None) or (sum(
            amount for cat, amount in user_spending.items() if cat != 'total') >= (tier.min_spend or 0))
    else:
        eligible_cats = list(tier.reward_rates.keys())
        min_spend_met = (tier.min_spend is None) or (sum(user_spending.get(
            cat.strip().lower(), 0) for cat in eligible_cats) >= (tier.min_spend or 0))
    return reward, details, min_spend_met, False, tier


def build_summary_dataframe(results):
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Monthly Reward (SGD)',
                            ascending=False).reset_index(drop=True)
        df.insert(0, 'Rank', df.index + 1)
        cols = [
            'Rank', 'Card Name', 'Card Type', 'Monthly Reward (SGD)',
            'Reward Rate', 'Min Spend Met', 'Cap Reached', 'Tier'
        ]
        df = df[cols]
    return df


def build_breakdown_dict(breakdowns):
    return breakdowns


def render_card_metrics(rewards_df, user_spending_data):
    if not rewards_df.empty:
        top_card = rewards_df.iloc[0]
        monthly_reward_val = float(
            top_card['Monthly Reward (SGD)'].replace('$', '').replace(',', ''))
        total_spending = user_spending_data.get('total', 0)
        annual_reward = monthly_reward_val * 12
        reward_rate = (monthly_reward_val / total_spending *
                       100) if total_spending > 0 else 0
        st.markdown("### 🏆 Top Card")
        col1, col2 = st.columns(2)
        col1.metric(
            "💳 Card",
            top_card['Card Name'],
            help="The name of the best card for your current spending profile."
        )
        col2.metric(
            "🏷️ Card Type",
            top_card['Card Type'],
            help="Cashback or miles."
        )
        col3, col4 = st.columns(2)
        col3.metric(
            "💰 Monthly Reward",
            f"${monthly_reward_val:,.2f}",
            help="Estimated monthly reward based on your current spending."
        )
        col4.metric(
            "📅 Annual Reward",
            f"${annual_reward:,.2f}",
            help="Projected yearly reward if your spending remains consistent."
        )
        st.metric(
            "📈 Reward Rate",
            f"{reward_rate:.2f}%",
            help="Percentage of your total spending returned as rewards."
        )


def render_breakdown_table(breakdown, card_type, capped_reward=None, capped_rate=None):
    breakdown_df = pd.DataFrame(list(breakdown))
    if not breakdown_df.empty and isinstance(breakdown_df, pd.DataFrame):
        breakdown_df = format_breakdown_df(
            breakdown, card_type, capped_reward=capped_reward, capped_rate=capped_rate)
        st.dataframe(
            breakdown_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": st.column_config.Column(width="small"),
                "Amount": st.column_config.Column(width="small"),
                "Rate": st.column_config.Column(width="small"),
                "Reward": st.column_config.Column(width="small"),
                "Potential Reward": st.column_config.Column(width="small"),
            }
        )


def single_card_rewards_and_breakdowns(user_spending, miles_to_sgd_rate=0.02, cards=None):
    if cards is None:
        raise ValueError("cards must be provided to single_card_rewards_and_breakdowns")
    results = []
    breakdowns = {}
    total_spending = user_spending.get('total', 0)
    for card in cards:
        best_reward = 0
        best_tier = None
        best_details = {}
        best_reward_rate = 0
        for tier in card.tiers:
            reward, details, min_spend_met, cap_reached, used_tier = calculate_card_tier_reward(
                card, tier, user_spending, miles_to_sgd_rate)
            reward_rate = (reward / total_spending *
                           100) if total_spending > 0 else 0
            if reward > best_reward or best_tier is None:
                best_reward = reward
                best_tier = used_tier
                best_details = {
                    'details': details,
                    'cap_reached': False,  # set after cap check
                    'min_spend_met': min_spend_met
                }
                best_reward_rate = reward_rate

        # Apply cap after selecting the best tier
        cap_reached = False
        if best_tier and best_tier.cap is not None and best_reward > best_tier.cap:
            best_reward = best_tier.cap
            cap_reached = True
            best_details['cap_reached'] = cap_reached
            # Recalculate reward rate using capped reward
            best_reward_rate = (best_reward / total_spending * 100) if total_spending > 0 else 0

        results.append({
            'Card Name': card.name,
            'Card Type': card.card_type,
            'Issuer': card.issuer,
            'Monthly Reward (SGD)': round(best_reward, 2),  # keep as float
            'Reward Rate': best_reward_rate,  # keep as float
            'Min Spend Met': best_details.get('min_spend_met', False),
            'Cap Reached': best_details.get('cap_reached', False),
            'Tier': best_tier.description if best_tier else ''
        })
        breakdowns[card.name] = best_details.get('details', [])
    df = build_summary_dataframe(results)
    return SingleCardRewardsResult(summary_df=df, breakdown_dict=build_breakdown_dict(breakdowns))


def render_single_card_component(user_spending_data, miles_to_sgd_rate=0.02, cards=None):
    st.subheader("\U0001F4B3 Single Card Monthly Rewards")
    # Ensure session state is initialized (if needed)
    # If you want to ensure it's always set
    initialize_spending_state(DEFAULT_SPENDING_VALUES)
    if cards is None:
        raise ValueError("cards must be provided to render_single_card_component")
    result = single_card_rewards_and_breakdowns(
        user_spending_data, miles_to_sgd_rate, cards)
    rewards_df = result.summary_df.copy()
    breakdowns = result.breakdown_dict
    # Format columns for display only
    if 'Monthly Reward (SGD)' in rewards_df.columns:
        rewards_df['Monthly Reward (SGD)'] = rewards_df['Monthly Reward (SGD)'].apply(
            lambda x: f"${x:,.2f}")
    if 'Reward Rate' in rewards_df.columns:
        rewards_df['Reward Rate'] = rewards_df['Reward Rate'].apply(
            lambda x: f"{x:.2f}%")
    render_card_metrics(rewards_df, get_user_spending())
    st.dataframe(
        rewards_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.Column(),
            "Card Name": st.column_config.Column(),
            "Card Type": st.column_config.Column(),
            "Monthly Reward (SGD)": st.column_config.Column(),
            "Reward Rate": st.column_config.Column(),
            "Min Spend Met": st.column_config.Column(),
            "Cap Reached": st.column_config.Column(),
            "Tier": st.column_config.Column(),
        }
    )
    # Card selector and detailed breakdown
    st.subheader("\U0001F50E Detailed Spending Breakdown")
    card_names = rewards_df['Card Name'].tolist()

    # Use ranked selectbox options
    options, display_to_card = get_ranked_selectbox_options(rewards_df)
    # Persist selected card in session state using helpers
    selected_display = get_selected_card_display()
    if selected_display not in options:
        selected_display = options[0] if options else None
        set_selected_card_display(selected_display)
    selected_display = st.selectbox(
        "Select a card for breakdown", options, key="breakdown_card_selectbox",
        index=options.index(
            selected_display) if selected_display in options else 0,
        on_change=lambda: set_selected_card_display(st.session_state['breakdown_card_selectbox']))
    set_selected_card_display(selected_display)
    selected_card = display_to_card[selected_display] if selected_display in display_to_card else (
        card_names[0] if card_names else None)

    # Show reward categories for selected card
    from components.breakdown_format_utils import get_reward_categories_with_icons
    card_obj = next((c for c in cards if c.name == selected_card), None)
    if card_obj and card_obj.tiers:
        # Use the best tier (first match by description, else first tier)
        tier_obj = card_obj.tiers[0]
        if hasattr(rewards_df, 'Tier') and 'Tier' in rewards_df.columns:
            tier_desc = rewards_df.loc[rewards_df['Card Name'] == selected_card,
                                       'Tier'].values[0] if selected_card in rewards_df['Card Name'].values else None
            if tier_desc:
                for t in card_obj.tiers:
                    if t.description == tier_desc:
                        tier_obj = t
                        break
        cats_str = get_reward_categories_with_icons(
            card_obj, tier_obj, as_string=True)
        st.caption(f"Reward Categories: {cats_str}")
    breakdown = breakdowns.get(selected_card, [])
    card_type = rewards_df.loc[rewards_df['Card Name'] == selected_card, 'Card Type'].values[0].lower(
    ) if selected_card in rewards_df['Card Name'].values else ''
    # Pass capped_reward and capped_rate if cap is reached
    capped_reward = None
    capped_rate = None
    if 'Cap Reached' in rewards_df.columns and selected_card in rewards_df['Card Name'].values:
        cap_reached = rewards_df.loc[rewards_df['Card Name']
                                     == selected_card, 'Cap Reached'].values[0]
        if cap_reached:
            capped_reward = float(rewards_df.loc[rewards_df['Card Name'] == selected_card,
                                  'Monthly Reward (SGD)'].values[0].replace('$', '').replace(',', ''))
            total_amount = sum(float(d['Amount']) for d in breakdown if isinstance(
                d, dict) and 'Amount' in d)
            capped_rate = (capped_reward / total_amount *
                           100) if total_amount > 0 else 0
    render_breakdown_table(
        breakdown, card_type, capped_reward=capped_reward, capped_rate=capped_rate)
