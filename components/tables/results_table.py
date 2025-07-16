"""
Results Table Component

This module handles all table display functionality including
results tables and data formatting.
"""

import streamlit as st
import pandas as pd


def display_results_table(display_results_df: pd.DataFrame):
    """
    Display results table with enhanced styling and metrics, 
    always showing all results in a scrollable table.

    Args:
        display_results_df: DataFrame with card results
    """
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
    display_results_df.insert(0, 'Rank', list(
        range(1, len(display_results_df) + 1)))
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


def display_combination_results_table(combinations_df: pd.DataFrame, best_single_reward: float):
    """
    Display combination results table with comparison to best single card

    Args:
        combinations_df: DataFrame with combination results
        best_single_reward: Best single card reward for comparison
    """
    if combinations_df.empty:
        st.write("No combinations to display.")
        return

    display_df = combinations_df.copy()
    display_df['vs Best Single'] = display_df['Monthly Reward'].apply(
        lambda reward: f"+${reward - best_single_reward:.2f}" if reward > best_single_reward else f"${reward - best_single_reward:.2f}"
    )
    display_df['Monthly Reward'] = display_df['Monthly Reward'].apply(
        lambda x: f"${x:.2f}")

    # Add ranking column with medal emojis for top 3
    display_df.insert(0, 'Rank', list(range(1, len(display_df) + 1)))
    display_df['Rank'] = display_df['Rank'].astype(str)
    if len(display_df) >= 1:
        display_df.iloc[0, 0] = '🥇'
    if len(display_df) >= 2:
        display_df.iloc[1, 0] = '🥈'
    if len(display_df) >= 3:
        display_df.iloc[2, 0] = '🥉'

    st.dataframe(
        display_df[['Rank', 'Card Name', 'Categories',
                    'Monthly Reward', 'vs Best Single']],
        use_container_width=True,
        hide_index=True
    )


def display_spending_allocation_table(allocation_data: dict, card_names: list, selected_cards_df: pd.DataFrame = None):
    """
    Display spending allocation table for card combinations

    Args:
        allocation_data: Dictionary with allocation data
        card_names: List of card names
        selected_cards_df: DataFrame with card data (optional)
    """
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
        if selected_cards_df is not None and 'Card Type' in selected_cards_df.columns:
            match = selected_cards_df[selected_cards_df['Card Name'] == card_name]
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


def create_detailed_spending_table(card_name: str, details: list) -> pd.DataFrame:
    """
    Create detailed spending breakdown table from calculation details

    Args:
        card_name: Name of the card
        details: List of calculation detail strings

    Returns:
        DataFrame with spending breakdown
    """
    import re

    rows = []
    for detail in details:
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

    # Sort by reward in descending order (excluding total row)
    if not df.empty:
        # Extract numeric values for sorting
        df['Reward_Numeric'] = df['Reward'].str.replace('$', '').astype(float)
        df = df.sort_values('Reward_Numeric', ascending=False)
        df = df.drop('Reward_Numeric', axis=1)

        # Extract numeric values from the formatted strings for total calculation
        amounts = [int(amount_str.replace("$", ""))
                   for amount_str in df["Amount"]]
        rewards = [float(reward_str.replace("$", ""))
                   for reward_str in df["Reward"]]
        total_amount = sum(amounts)
        total_reward = sum(rewards)

        total_row = pd.DataFrame([{
            "Category": "Total",
            "Amount": f"${total_amount}",
            "Rate": "",
            "Reward": f"${total_reward:.2f}"
        }])

        df = pd.concat([df, total_row], ignore_index=True)

    return df
