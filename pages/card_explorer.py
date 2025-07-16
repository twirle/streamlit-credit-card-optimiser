import streamlit as st
import pandas as pd

# Load data
cards = pd.read_csv("cardData/cards.csv")
tiers = pd.read_csv("cardData/card_tiers.csv")
rates = pd.read_csv("cardData/category_rates.csv")

st.set_page_config(page_title="Card Explorer", layout="wide")


def _display_category_group(group_data, selected_card):
    """Helper function to display a category group with rate and cap info"""
    # Format rate display
    rate_str = f"{group_data['rate_value']:.1f}{'%' if group_data['rate_type'] == 'percentage' else ' mpd'}"

    # Format cap display
    if pd.notna(group_data['cap_amount']):
        cap_type = str(group_data['cap_type']).replace(
            '_', ' ').title() if pd.notna(group_data['cap_type']) else "Cap"
        if 'dollars_earned' in str(group_data['cap_type']):
            cap_display = f"{group_data['cap_amount']:,.0f} {'dollars' if selected_card['card_type'] == 'Cashback' else 'miles'}"
        elif 'dollars_spent' in str(group_data['cap_type']):
            cap_display = f"${group_data['cap_amount']:,.0f} spent"
        else:
            cap_display = f"{group_data['cap_amount']:,.0f}"
    else:
        cap_display = "-"

    # Determine if this is a shared cap group
    has_shared_cap = pd.notna(group_data['cap_group']) and str(
        group_data['cap_group']).strip()

    # Display categories
    if len(group_data['categories']) == 1:
        st.markdown(f"**💳 {group_data['categories'][0]}**")
    else:
        categories_text = ", ".join(group_data['categories'])
        if has_shared_cap:
            st.markdown(f"**🎯 {categories_text} (Shared Cap)**")
        else:
            st.markdown(f"**📦 {categories_text}**")

    # Create a container for the rate and cap info
    with st.container():
        # Use columns for rate and cap display
        rate_col, cap_col = st.columns(2)

        with rate_col:
            st.caption("Rate")
            st.markdown(f"**{rate_str}**")

        with cap_col:
            cap_title = "Combined Cap" if has_shared_cap else "Cap"
            st.caption(cap_title)
            st.markdown(f"**{cap_display}**")

        # Add a subtle divider
        # st.divider()


st.title("🗂️ Card Explorer")

# Card selector on main page
card_name = st.selectbox("Select a card to explore:", cards["name"].unique())

selected_card = cards[cards["name"] == card_name].iloc[0]
card_tiers = tiers[tiers["card_id"] == selected_card["card_id"]]

# Card summary with metrics - more compact
cardType, cardIssuer,  = st.columns(2)
with cardType:
    st.metric(
        "💳 Card Type", selected_card['card_type'])
    # Count total categories for this card
    tier_ids = card_tiers['tier_id'].tolist()
    total_categories = len(rates[rates['tier_id'].isin(tier_ids)])
    st.metric("📊 Total Categories", total_categories)

with cardIssuer:
    st.metric("🏦 Issuer", selected_card['issuer'])

    # Calculate highest rate
    tier_ids = card_tiers['tier_id'].tolist()
    all_rates = rates[rates['tier_id'].isin(tier_ids)]
    if len(all_rates) > 0:
        max_rate = all_rates['rate_value'].max()
        max_rate_rows = all_rates[all_rates['rate_value'] == max_rate]
        if len(max_rate_rows) > 0:
            max_rate_row = max_rate_rows.iloc[0]
            rate_str = f"{max_rate:.1f}{'%' if max_rate_row['rate_type'] == 'percentage' else ' mpd'}"

            # Get all categories with the highest rate
            max_categories = max_rate_rows['category'].tolist()
            if len(max_categories) == 1:
                delta_text = f"on {max_categories[0]}"
            else:
                delta_text = f"on {', '.join(max_categories)}"

            st.metric("⭐ Highest Rate", rate_str, delta=delta_text)

st.markdown(f"### {selected_card['name']}")

# Show each tier in a neat card format
for _, tier in card_tiers.iterrows():
    # description, minimumSpend = st.columns([2, 1])
    # with description:
    st.markdown(f"### 📊 {tier['description']}")

  # Show minimum spend as metric
    # with minimumSpend:
    min_spend = tier['min_spend']
    if min_spend == 0:
        st.success("✅ No minimum spending required")
    else:
        st.warning(f"💰 Minimum spending: ${min_spend:,.0f}")

    tier_rates: pd.DataFrame = rates[rates["tier_id"]
                                     == tier["tier_id"]].copy()
    # Filter out categories with 0 rates (0% or 0mpd)
    tier_rates = tier_rates[tier_rates['rate_value'] > 0].copy()

    if len(tier_rates) > 0:
        # Group categories by their rate and cap characteristics
        rate_groups = {}

        for _, row in tier_rates.iterrows():
            # Create a unique key for grouping based on rate and cap characteristics
            cap_group_val = row['cap_group']
            cap_group_str = None
            cap_group_str_val = str(cap_group_val).strip()
            if cap_group_str_val:
                cap_group_str = cap_group_str_val

            cap_amount_val = row['cap_amount']
            cap_amount_final = cap_amount_val

            cap_type_val = row['cap_type']
            cap_type_final = cap_type_val

            rate_key = (
                row['rate_value'],
                row['rate_type'],
                cap_amount_final,
                cap_type_final,
                cap_group_str
            )

            if rate_key not in rate_groups:
                rate_groups[rate_key] = {
                    'categories': [],
                    'rate_value': row['rate_value'],
                    'rate_type': row['rate_type'],
                    'cap_amount': row['cap_amount'],
                    'cap_type': row['cap_type'],
                    'cap_group': row['cap_group']
                }

            rate_groups[rate_key]['categories'].append(row['category'])

        # Convert to list for easier processing
        rate_groups_list = list(rate_groups.items())

        # Display grouped categories in 2 columns
        for i in range(0, len(rate_groups_list), 2):
            col1, col2 = st.columns(2, border=True)

            # First column
            with col1:
                if i < len(rate_groups_list):
                    rate_key, group_data = rate_groups_list[i]
                    _display_category_group(group_data, selected_card)

            # Second column
            with col2:
                if i + 1 < len(rate_groups_list):
                    rate_key, group_data = rate_groups_list[i + 1]
                    _display_category_group(group_data, selected_card)
    else:
        st.info("No category rates found for this tier.")
