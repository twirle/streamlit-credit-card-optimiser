import pandas as pd
# For single and multi_card_component to display the card spending breakdown dataframe


# Category to emoji mapping
category_icons = {
    'dining': '🍽️',
    'groceries': '🛒',
    'petrol': '⛽',
    'transport': '🚌',
    'streaming': '📺',
    'entertainment': '🎬',
    'utilities': '💡',
    'online': '🛍️',
    'travel': '✈️',
    'overseas': '🌏',
    'retail': '🏬',
    'total': '🧮',
}


def format_breakdown_df(breakdown, card_type):
    breakdown_df = pd.DataFrame(list(breakdown))
    if not breakdown_df.empty and isinstance(breakdown_df, pd.DataFrame):
        if 'Reward' in breakdown_df.columns:
            breakdown_df = breakdown_df[breakdown_df['Reward'] != 0].copy()
            # Ensure pandas DataFrame
            breakdown_df = pd.DataFrame(breakdown_df)
        if 'Category' in breakdown_df.columns:
            breakdown_df.loc[:, 'Category'] = breakdown_df['Category'].astype(
                'string').str.capitalize()
            breakdown_df.loc[:, 'Category'] = breakdown_df['Category'].apply(
                lambda x: f"{category_icons.get(x.lower(), '🔹')} {x}" if isinstance(x, str) else x)
        if 'Amount' in breakdown_df.columns:
            breakdown_df.loc[:, 'Amount'] = pd.to_numeric(
                breakdown_df['Amount'], errors='coerce')
            breakdown_df = breakdown_df.sort_values(
                by='Amount', ascending=False)
            breakdown_df['Amount'] = breakdown_df['Amount'].astype('object')
            breakdown_df.loc[:, 'Amount'] = breakdown_df['Amount'].apply(
                lambda x: f"${x:,.2f}")
        if 'Rate' in breakdown_df.columns:
            if card_type == 'cashback':
                breakdown_df['Rate'] = breakdown_df['Rate'].astype('object')
                breakdown_df.loc[:, 'Rate'] = breakdown_df['Rate'].apply(
                    lambda x: f"{x:.2f}%")
            elif card_type == 'miles':
                breakdown_df['Rate'] = breakdown_df['Rate'].astype('object')
                breakdown_df.loc[:, 'Rate'] = breakdown_df['Rate'].apply(
                    lambda x: f"{x:.2f} mpd")
            else:
                breakdown_df['Rate'] = breakdown_df['Rate'].astype('object')
                breakdown_df.loc[:, 'Rate'] = breakdown_df['Rate'].astype(
                    'string')
        if 'Reward' in breakdown_df.columns:
            breakdown_df['Reward'] = breakdown_df['Reward'].astype('object')
            breakdown_df.loc[:, 'Reward'] = breakdown_df['Reward'].apply(
                lambda x: f"${x:,.2f}")
            total_reward = sum([row['Reward'] for row in breakdown if isinstance(
                row, dict) and 'Reward' in row])
            total_row = {col: '' for col in breakdown_df.columns}
            total_row['Category'] = f"{category_icons.get('total', '🧮')} Total"
            total_row['Reward'] = f"${total_reward:,.2f}"
            breakdown_df = pd.concat(
                [breakdown_df, pd.DataFrame([total_row])], ignore_index=True)
    return breakdown_df


def get_ranked_selectbox_options(df, name_col='Card Name', rank_col='Rank'):
    """
    Given a DataFrame with rank and name columns, return a list of strings like '#1 UOB Lady’s'.
    Returns a tuple: (list of display strings, dict mapping display string to card name)
    """
    if name_col not in df.columns or rank_col not in df.columns:
        return [], {}
    options = []
    mapping = {}
    for _, row in df.iterrows():
        display = f"#{int(row[rank_col])} {row[name_col]}"
        options.append(display)
        mapping[display] = row[name_col]
    return options, mapping


def get_reward_categories_with_icons(card_obj, tier_obj=None, as_string=True):
    """
    Returns a list of (icon, category) tuples or a formatted string for the reward categories for a given card and tier.
    If as_string is True, returns a comma-separated string with icons. Otherwise, returns a list of tuples.
    """
    if card_obj is None or not hasattr(card_obj, 'tiers') or not card_obj.tiers:
        return "" if as_string else []
    if tier_obj is None:
        tier_obj = card_obj.tiers[0]
    reward_cats = [cat.capitalize() for cat in tier_obj.reward_rates.keys()]
    reward_cats_with_icons = [(category_icons.get(cat.lower(), '🔹'), cat) for cat in reward_cats]
    if as_string:
        return ', '.join([f"{icon} {cat}" for icon, cat in reward_cats_with_icons])
    return reward_cats_with_icons
