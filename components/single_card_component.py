import streamlit as st
import pandas as pd
from collections import namedtuple
from services.data.card_loader import load_cards_and_models
from components.breakdown_format_utils import format_breakdown_df, category_icons

SingleCardRewardsResult = namedtuple('SingleCardRewardsResult', [
                                     'summary_df', 'breakdown_dict'])


def single_card_rewards_and_breakdowns(user_spending, miles_to_sgd_rate=0.02):
    cards = load_cards_and_models()
    results = []
    breakdowns = {}
    for card in cards:
        best_reward = 0
        best_tier = None
        best_details = {}
        for tier in card.tiers:
            base_rate = tier.base_rate or 0
            bonus_categories = [
                cat for cat, rate in tier.reward_rates.items() if rate > base_rate]
            bonus_spend = sum(user_spending.get(cat, 0)
                              for cat in bonus_categories)
            min_spend_met = (tier.min_spend is None) or (
                bonus_spend >= tier.min_spend)
            reward = 0
            details = []
            if min_spend_met:
                for cat, amount in user_spending.items():
                    if cat == 'total':
                        continue
                    rate = tier.reward_rates.get(cat, base_rate)
                    if card.card_type.lower() == 'cashback':
                        reward += amount * (rate / 100)
                    elif card.card_type.lower() == 'miles':
                        reward += amount * rate * miles_to_sgd_rate
                    details.append({
                        'Category': cat,
                        'Amount': amount,
                        'Rate': rate,
                        'Reward': amount * (rate / 100) if card.card_type.lower() == 'cashback' else amount * rate * miles_to_sgd_rate
                    })
            else:
                for cat, amount in user_spending.items():
                    if cat == 'total':
                        continue
                    rate = base_rate
                    if card.card_type.lower() == 'cashback':
                        reward += amount * (rate / 100)
                    elif card.card_type.lower() == 'miles':
                        reward += amount * rate * miles_to_sgd_rate
                    details.append({
                        'Category': cat,
                        'Amount': amount,
                        'Rate': rate,
                        'Reward': amount * (rate / 100) if card.card_type.lower() == 'cashback' else amount * rate * miles_to_sgd_rate
                    })
            cap_reached = False
            if tier.cap is not None and reward > tier.cap:
                reward = tier.cap
                cap_reached = True
            if reward > best_reward or best_tier is None:
                best_reward = reward
                best_tier = tier
                best_details = {
                    'details': details,
                    'cap_reached': cap_reached,
                    'min_spend_met': min_spend_met
                }
        results.append({
            'Card Name': card.name,
            'Card Type': card.card_type,
            'Issuer': card.issuer,
            'Monthly Reward (SGD)': round(best_reward, 2),
            'Min Spend Met': best_details.get('min_spend_met', False),
            'Cap Reached': best_details.get('cap_reached', False),
            'Tier': best_tier.description if best_tier else ''
        })
        breakdowns[card.name] = best_details.get('details', [])
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Monthly Reward (SGD)',
                            ascending=False).reset_index(drop=True)
        df.insert(0, 'Rank', df.index + 1)
        cols = [
            'Rank', 'Card Name', 'Card Type', 'Issuer', 'Monthly Reward (SGD)',
            'Min Spend Met', 'Cap Reached', 'Tier'
        ]
        df = df[cols]
    return SingleCardRewardsResult(summary_df=df, breakdown_dict=breakdowns)


def render_single_card_component(user_spending_data, miles_to_sgd_rate=0.02):
    st.subheader("💳 Single Card Monthly Rewards")
    result = single_card_rewards_and_breakdowns(
        user_spending_data, miles_to_sgd_rate)
    rewards_df = result.summary_df
    # Format Monthly Reward (SGD) with $ prefix
    if 'Monthly Reward (SGD)' in rewards_df.columns:
        rewards_df['Monthly Reward (SGD)'] = rewards_df['Monthly Reward (SGD)'].astype('object')
        rewards_df.loc[:, 'Monthly Reward (SGD)'] = rewards_df['Monthly Reward (SGD)'].apply(
            lambda x: f"${x:,.2f}")
    # Add Reward Rate column
    total_spending = user_spending_data.get('total', 0)
    if total_spending > 0 and 'Monthly Reward (SGD)' in rewards_df.columns:
        rewards_df['Reward Rate'] = rewards_df['Monthly Reward (SGD)'].apply(
            lambda x: float(str(x).replace('$','').replace(',','')) / total_spending * 100 if str(x).replace('$','').replace(',','').replace('.','',1).isdigit() else 0)
        rewards_df['Reward Rate'] = rewards_df['Reward Rate'].astype('object')
        rewards_df['Reward Rate'] = rewards_df['Reward Rate'].apply(lambda x: f"{x:.2f}%")
    else:
        rewards_df['Reward Rate'] = "0.00%"
    breakdowns = result.breakdown_dict

    # Show metrics for top-ranked card
    if not rewards_df.empty:
        top_card = rewards_df.iloc[0]
        # Remove $ for calculations
        monthly_reward_val = float(
            top_card['Monthly Reward (SGD)'].replace('$', '').replace(',', ''))
        # Get total user spending
        total_spending = user_spending_data.get('total', 0)
        annual_reward = monthly_reward_val * 12
        reward_rate = (monthly_reward_val / total_spending *
                       100) if total_spending > 0 else 0
        st.markdown("### 🏆 Top Card")
        # First row: Card, Card Type, Issuer
        col1, col2, col3 = st.columns(3)
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
        col3.metric(
            "🏦 Issuer",
            top_card['Issuer'],
            help="The bank or issuer of the card."
        )
        # Second row: Monthly Reward, Annual Reward, Reward Rate
        col4, col5, col6 = st.columns(3)
        col4.metric(
            "💰 Monthly Reward",
            f"${monthly_reward_val:,.2f}",
            help="Estimated monthly reward based on your current spending."
        )
        col5.metric(
            "📅 Annual Reward",
            f"${annual_reward:,.2f}",
            help="Projected yearly reward if your spending remains consistent."
        )
        col6.metric(
            "📈 Reward Rate",
            f"{reward_rate:.2f}%",
            help="Percentage of your total spending returned as rewards."
        )

    st.dataframe(
        rewards_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.Column(),
            "Card Name": st.column_config.Column(),
            "Card Type": st.column_config.Column(),
            "Issuer": st.column_config.Column(width="medium"),
            "Monthly Reward (SGD)": st.column_config.Column(),
            "Reward Rate": st.column_config.Column(),
            "Min Spend Met": st.column_config.Column(),
            "Cap Reached": st.column_config.Column(),
            "Tier": st.column_config.Column(),
        }
    )

    # Card selector and detailed breakdown
    st.subheader("🔎 Detailed Spending Breakdown")
    card_names = rewards_df['Card Name'].tolist()
    selected_card = st.selectbox("Select a card for breakdown", card_names)
    breakdown = breakdowns.get(selected_card, [])
    breakdown_df = pd.DataFrame(list(breakdown))
    # Get card type for selected card
    card_type = rewards_df.loc[rewards_df['Card Name'] == selected_card, 'Card Type'].values[0].lower() if selected_card in rewards_df['Card Name'].values else ''
    # Filter out rows with $0 reward, capitalize category, and sort by amount
    if not breakdown_df.empty and isinstance(breakdown_df, pd.DataFrame):
        breakdown_df = format_breakdown_df(breakdown, card_type)

    st.dataframe(
        breakdown_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Category": st.column_config.Column(width="small"),
            "Amount": st.column_config.Column(width="small"),
            "Rate": st.column_config.Column(width="small"),
            "Reward": st.column_config.Column(width="small"),
        }
    )
