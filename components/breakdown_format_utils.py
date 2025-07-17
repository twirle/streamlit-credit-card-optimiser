import pandas as pd

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
            breakdown_df = pd.DataFrame(breakdown_df)  # Ensure pandas DataFrame
        if 'Category' in breakdown_df.columns:
            breakdown_df.loc[:, 'Category'] = breakdown_df['Category'].astype('string').str.capitalize()
            breakdown_df.loc[:, 'Category'] = breakdown_df['Category'].apply(
                lambda x: f"{category_icons.get(x.lower(), '🔹')} {x}" if isinstance(x, str) else x)
        if 'Amount' in breakdown_df.columns:
            breakdown_df.loc[:, 'Amount'] = pd.to_numeric(breakdown_df['Amount'], errors='coerce')
            breakdown_df = breakdown_df.sort_values(by='Amount', ascending=False)
            breakdown_df['Amount'] = breakdown_df['Amount'].astype('object')
            breakdown_df.loc[:, 'Amount'] = breakdown_df['Amount'].apply(lambda x: f"${x:,.2f}")
        if 'Rate' in breakdown_df.columns:
            if card_type == 'cashback':
                breakdown_df['Rate'] = breakdown_df['Rate'].astype('object')
                breakdown_df.loc[:, 'Rate'] = breakdown_df['Rate'].apply(lambda x: f"{x:.2f}%")
            elif card_type == 'miles':
                breakdown_df['Rate'] = breakdown_df['Rate'].astype('object')
                breakdown_df.loc[:, 'Rate'] = breakdown_df['Rate'].apply(lambda x: f"{x:.2f} mpd")
            else:
                breakdown_df['Rate'] = breakdown_df['Rate'].astype('object')
                breakdown_df.loc[:, 'Rate'] = breakdown_df['Rate'].astype('string')
        if 'Reward' in breakdown_df.columns:
            breakdown_df['Reward'] = breakdown_df['Reward'].astype('object')
            breakdown_df.loc[:, 'Reward'] = breakdown_df['Reward'].apply(lambda x: f"${x:,.2f}")
            total_reward = sum([row['Reward'] for row in breakdown if isinstance(row, dict) and 'Reward' in row])
            total_row = {col: '' for col in breakdown_df.columns}
            total_row['Category'] = f"{category_icons.get('total', '🧮')} Total"
            total_row['Reward'] = f"${total_reward:,.2f}"
            breakdown_df = pd.concat(
                [breakdown_df, pd.DataFrame([total_row])], ignore_index=True)
    return breakdown_df 