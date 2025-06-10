import pandas as pd
from data_loader import get_card_categories


def calculate_uob_lady_reward(card_row, user_spending, miles_value_sgd):
    details = []
    total_reward = 0
    cap_value = 1000  # UOB Lady's cap is $1000 per month

    # Automatically find the highest spending category (excluding 'total')
    spending_categories = {
        k: v for k, v in user_spending.items() if k != 'total' and v > 0}

    if not spending_categories:
        return 0, ["No spending in any category"], False, 0, 0, True

    chosen_category = max(spending_categories, key=spending_categories.get)
    chosen_amount = spending_categories[chosen_category]

    details.append(
        f"🎯 **Auto-selected category: {chosen_category.capitalize()} (${chosen_amount})**")

    # Apply 4mpd to chosen category (with cap) and 0.4mpd to others
    for category, amount in user_spending.items():
        if category == 'total' or amount == 0:
            continue

        if category == chosen_category:
            # Chosen category gets 4mpd up to $1000 cap
            eligible_spend = min(amount, cap_value)
            reward = eligible_spend * 4 * miles_value_sgd
            details.append(
                f"{category.capitalize()} (bonus): ${eligible_spend:.0f} × 4 mpd × {miles_value_sgd:.3f} = {reward:.2f} SGD")
            if eligible_spend < amount:
                remaining_spend = amount - eligible_spend
                remaining_reward = remaining_spend * 0.4 * miles_value_sgd
                reward += remaining_reward
                details.append(
                    f"{category.capitalize()} (over cap): ${remaining_spend:.0f} × 0.4 mpd × {miles_value_sgd:.3f} = {remaining_reward:.2f} SGD")
        else:
            # Other categories get 0.4mpd
            reward = amount * 0.4 * miles_value_sgd
            details.append(
                f"{category.capitalize()}: ${amount} × 0.4 mpd × {miles_value_sgd:.3f} = {reward:.2f} SGD")

        total_reward += reward

    # Cap analysis for chosen category only
    chosen_spending = user_spending.get(chosen_category, 0)
    cap_reached = chosen_spending > cap_value
    cap_diff = chosen_spending - cap_value if cap_reached else cap_value - chosen_spending

    return total_reward, details, cap_reached, cap_diff, total_reward, True


def calculate_card_reward_details(card_row, user_spending, miles_value_sgd):
    # Edge case for UOB Lady's Card
    if "Lady" in card_row['Name']:
        return calculate_uob_lady_reward(card_row, user_spending, miles_value_sgd)

    details = []
    total_reward = 0
    cap = card_row.get('Cap')
    cap_value = cap if pd.notna(cap) else None

    # Check if minimum spend is met
    card_min_spend = card_row.get('Min Spend', 0)
    min_spend_met = user_spending['total'] >= card_min_spend if pd.notna(
        card_min_spend) else True

    if not min_spend_met:
        base_rate = card_row.get('Base Rate', 0)
        if pd.notna(base_rate):
            if card_row.get('Type') == 'Miles':
                total_reward = user_spending['total'] * \
                    base_rate * miles_value_sgd
                details.append(
                    f"Base rate (min spend not met): {total_reward:.2f} SGD")
            else:
                total_reward = user_spending['total'] * (base_rate / 100)
                details.append(
                    f"Base rate (min spend not met): {total_reward:.2f} SGD")
        else:
            details.append("No rewards - minimum spend not met")
            total_reward = 0
    else:
        category_mapping = {
            'dining': 'Dining Rate',
            'groceries': 'Groceries Rate',
            'petrol': 'Petrol Rate',
            'transport': 'Transport Rate',
            'streaming': 'Streaming Rate',
            'entertainment': 'Entertainment Rate',
            'utilities': 'Utilities Rate',
            'retail': 'Retail Rate',
            'online': 'Online Rate',
            'travel': 'Travel Rate',
            'overseas': 'Overseas Rate'
        }

        # Calculate category-specific rewards with cap application
        total_capped_spending = 0

        for category, amount in user_spending.items():
            if category == 'total' or amount == 0:
                continue

            rate_col = category_mapping.get(category)
            if rate_col and rate_col in card_row.index:
                rate = card_row[rate_col]
                if pd.notna(rate):
                    # Apply cap on spending amount for this category
                    if cap_value is not None:
                        eligible_spend = min(
                            amount, cap_value - total_capped_spending)
                        eligible_spend = max(0, eligible_spend)
                        total_capped_spending += eligible_spend
                    else:
                        eligible_spend = amount

                    if card_row.get('Type') == 'Miles':
                        reward = eligible_spend * rate * miles_value_sgd
                        if eligible_spend < amount and cap_value is not None:
                            details.append(
                                f"{category.capitalize()}: ${eligible_spend:.0f} (capped from ${amount}) × {rate} mpd × {miles_value_sgd:.3f} = {reward:.2f} SGD")
                        else:
                            details.append(
                                f"{category.capitalize()}: ${eligible_spend} × {rate} mpd × {miles_value_sgd:.3f} = {reward:.2f} SGD")
                    else:
                        reward = eligible_spend * (rate / 100)
                        if eligible_spend < amount and cap_value is not None:
                            details.append(
                                f"{category.capitalize()}: ${eligible_spend:.0f} (capped from ${amount}) × {rate}% = {reward:.2f} SGD")
                        else:
                            details.append(
                                f"{category.capitalize()}: ${eligible_spend} × {rate}% = {reward:.2f} SGD")

                    total_reward += reward

                    if cap_value is not None and total_capped_spending >= cap_value:
                        break

    # Cap analysis
    cap_reached = False
    cap_diff = None
    original_reward = total_reward

    if cap_value is not None:
        total_eligible_spending = sum(user_spending[cat] for cat in ['dining', 'groceries', 'petrol', 'transport',
                                      'streaming', 'entertainment', 'utilities', 'online', 'travel', 'overseas'] if user_spending.get(cat, 0) > 0)

        if total_eligible_spending > cap_value:
            cap_reached = True
            cap_diff = total_eligible_spending - cap_value
        else:
            cap_diff = cap_value - total_eligible_spending

    return total_reward, details, cap_reached, cap_diff, original_reward, min_spend_met


def calculate_category_reward(card_row, category, spend, miles_value_sgd):
    rate_col_map = {
        'dining': 'Dining Rate',
        'groceries': 'Groceries Rate',
        'petrol': 'Petrol Rate',
        'transport': 'Transport Rate',
        'streaming': 'Streaming Rate',
        'entertainment': 'Entertainment Rate',
        'utilities': 'Utilities Rate',
        'retail': 'Retail Rate',
        'online': 'Online Rate',
        'travel': 'Travel Rate',
        'overseas': 'Overseas Rate'
    }
    rate_col = rate_col_map.get(category)
    if not rate_col or rate_col not in card_row:
        return 0
    rate = card_row[rate_col]
    if pd.isna(rate) or spend <= 0:
        return 0

    # For miles cards, convert miles to SGD
    if card_row.get('Type') == 'Miles':
        reward = spend * rate * miles_value_sgd
    else:
        reward = spend * (rate / 100)
    return reward


def combine_two_cards_rewards(card1, card2, user_spending, miles_value_sgd):
    # Categories to consider
    categories = [
        'dining', 'groceries', 'petrol', 'transport', 'streaming', 'entertainment',
        'utilities', 'retail', 'online', 'travel', 'overseas', 'other'
    ]

    rate_col_map = {
        'dining': 'Dining Rate',
        'groceries': 'Groceries Rate',
        'petrol': 'Petrol Rate',
        'transport': 'Transport Rate',
        'streaming': 'Streaming Rate',
        'entertainment': 'Entertainment Rate',
        'utilities': 'Utilities Rate',
        'retail': 'Retail Rate',
        'online': 'Online Rate',
        'travel': 'Travel Rate',
        'overseas': 'Overseas Rate'
    }

    # Initialize spending allocation
    allocation = {cat: {'card1': 0, 'card2': 0} for cat in categories}

    # Initialize caps tracking per card
    cap1 = card1.get('Cap') if pd.notna(card1.get('Cap')) else None
    cap2 = card2.get('Cap') if pd.notna(card2.get('Cap')) else None

    # Track total reward per card to respect caps
    total_reward_card1 = 0
    total_reward_card2 = 0

    # For each category, decide which card gives better reward per dollar spent
    for cat in categories:
        spend = user_spending.get(cat, 0)
        if spend <= 0:
            continue

        reward1 = calculate_category_reward(card1, cat, spend, miles_value_sgd)
        reward2 = calculate_category_reward(card2, cat, spend, miles_value_sgd)

        # Calculate reward per dollar
        rpd1 = reward1 / spend if spend > 0 else 0
        rpd2 = reward2 / spend if spend > 0 else 0

        # Assign spending to card with higher reward per dollar
        if rpd1 > rpd2:
            # Check if cap will be exceeded for card1
            if cap1 is not None and total_reward_card1 + reward1 > cap1:
                # Calculate max spend before cap
                max_spend = (cap1 - total_reward_card1) / \
                    rpd1 if rpd1 > 0 else 0
                max_spend = max(0, min(max_spend, spend))
                allocation[cat]['card1'] = max_spend
                allocation[cat]['card2'] = spend - max_spend
                total_reward_card1 += calculate_category_reward(
                    card1, cat, max_spend, miles_value_sgd)
                total_reward_card2 += calculate_category_reward(
                    card2, cat, spend - max_spend, miles_value_sgd)
            else:
                allocation[cat]['card1'] = spend
                total_reward_card1 += reward1
        else:
            # Check if cap will be exceeded for card2
            if cap2 is not None and total_reward_card2 + reward2 > cap2:
                max_spend = (cap2 - total_reward_card2) / \
                    rpd2 if rpd2 > 0 else 0
                max_spend = max(0, min(max_spend, spend))
                allocation[cat]['card2'] = max_spend
                allocation[cat]['card1'] = spend - max_spend
                total_reward_card2 += calculate_category_reward(
                    card2, cat, max_spend, miles_value_sgd)
                total_reward_card1 += calculate_category_reward(
                    card1, cat, spend - max_spend, miles_value_sgd)
            else:
                allocation[cat]['card2'] = spend
                total_reward_card2 += reward2

    # Calculate final rewards
    final_reward_card1 = 0
    final_reward_card2 = 0
    details_card1 = []
    details_card2 = []

    for cat in categories:
        spend1 = allocation[cat]['card1']
        spend2 = allocation[cat]['card2']

        if spend1 > 0:
            r = calculate_category_reward(card1, cat, spend1, miles_value_sgd)
            final_reward_card1 += r

            # Generate string with rate information
            rate_col = rate_col_map.get(cat)
            if rate_col and rate_col in card1:
                rate = card1[rate_col]
                if pd.notna(rate):
                    if card1.get('Type') == 'Miles':
                        details_card1.append(
                            f"{cat.capitalize()}: ${spend1:.0f} × {rate} mpd × {miles_value_sgd:.3f} = {r:.2f}")
                    else:
                        details_card1.append(
                            f"{cat.capitalize()}: ${spend1:.0f} × {rate}% = {r:.2f}")
                else:
                    details_card1.append(
                        f"{cat.capitalize()}: ${spend1:.0f} → ${r:.2f}")
            else:
                details_card1.append(
                    f"{cat.capitalize()}: ${spend1:.0f} → ${r:.2f}")

        if spend2 > 0:
            r = calculate_category_reward(card2, cat, spend2, miles_value_sgd)
            final_reward_card2 += r

            # Generate string with rate information
            rate_col = rate_col_map.get(cat)
            if rate_col and rate_col in card2:
                rate = card2[rate_col]
                if pd.notna(rate):
                    if card2.get('Type') == 'Miles':
                        details_card2.append(
                            f"{cat.capitalize()}: ${spend2:.0f} × {rate} mpd × {miles_value_sgd:.3f} = {r:.2f}")
                    else:
                        details_card2.append(
                            f"{cat.capitalize()}: ${spend2:.0f} × {rate}% = {r:.2f}")
                else:
                    details_card2.append(
                        f"{cat.capitalize()}: ${spend2:.0f} → ${r:.2f}")
            else:
                details_card2.append(
                    f"{cat.capitalize()}: ${spend2:.0f} → ${r:.2f}")

    total_combined_reward = final_reward_card1 + final_reward_card2

    return {
        'allocation': allocation,
        'card1_reward': final_reward_card1,
        'card2_reward': final_reward_card2,
        'total_reward': total_combined_reward,
        'details_card1': details_card1,
        'details_card2': details_card2
    }


def find_best_card_combinations(df_filtered, user_spending, miles_value_sgd, results_df):
    """Find best two-card combinations, focusing on capped cards first"""

    # Check which cards are capped
    capped_cards = results_df[results_df['Cap Reached']
                              == True]['Card Name'].unique()

    combinations = []

    top_cards = results_df.groupby('Card Name')['Monthly Reward'].max(
    ).sort_values(ascending=False).head(5).index.tolist()

    for i, card1_name in enumerate(top_cards):
        for card2_name in top_cards[i+1:]:  # Avoid duplicate combinations

            # Get the best tier for each card
            card1_rows = df_filtered[df_filtered['Name'] == card1_name]
            card2_rows = df_filtered[df_filtered['Name'] == card2_name]

            if len(card1_rows) == 0 or len(card2_rows) == 0:
                continue

            card1_data = card1_rows.iloc[0]
            card2_data = card2_rows.iloc[0]

            # Calculate combined rewards
            combined_result = combine_two_cards_rewards(
                card1_data, card2_data, user_spending, miles_value_sgd)

            # Create combination entry
            combo_name = f"{card1_name} + {card2_name}"
            combo_issuer = f"{card1_data['Issuer']} + {card2_data['Issuer']}"

            # Combine categories
            cat1 = get_card_categories(card1_data)
            cat2 = get_card_categories(card2_data)
            combo_categories = ", ".join(
                list(set(cat1 + cat2)))  # Remove duplicates

            combinations.append({
                'Card Name': combo_name,
                'Issuer': combo_issuer,
                'Type': 'Combination',
                'Categories': combo_categories,
                'Monthly Reward': combined_result['total_reward'],
                'Min Spend': 0,  # Combinations don't have min spend
                'Cap': 'Combined',
                'Cap Reached': False,  # Combinations are designed to avoid caps
                'Cap Difference': None,
                'Original Reward': combined_result['total_reward'],
                'Min Spend Met': True,
                'Details': [f"Card 1: ${combined_result['card1_reward']:.2f}", f"Card 2: ${combined_result['card2_reward']:.2f}"],
                'Source': 'Combination'
            })

    return combinations
