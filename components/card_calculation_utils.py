# Group definitions for UOB Lady's/Lady's Solitaire (shared for single and multi-card logic)
UOB_LADYS_GROUP_MAP = {
    'dining': ['dining'],
    'entertainment': ['entertainment'],
    'retail': ['retail'],
    'transport': ['transport', 'simplygo', 'petrol'],
    'travel': ['travel']
}

def calculate_uob_ladys_rewards(user_spending, miles_to_sgd_rate, tier, is_solitaire=False):
    """
    For UOB Lady's: Only one eligible group (Dining, Entertainment, Retail, Transport, Travel) gets 4 mpd, capped per group. Lady's Solitaire: two groups, each capped.
    Transport group includes Transport, SimplyGo, Petrol.
    """
    group_map = UOB_LADYS_GROUP_MAP
    base_rate = tier.base_rate or 0.4
    bonus_rate = 4.0
    cap = tier.cap if tier.cap is not None else float('inf')
    # Calculate total spend per group
    group_spend = {g: sum(user_spending.get(cat, 0) for cat in cats) for g, cats in group_map.items()}
    # Pick top group(s)
    n_groups = 2 if is_solitaire else 1
    top_groups = sorted(group_spend, key=lambda g: group_spend[g], reverse=True)[:n_groups]
    # Track how much of each category is allocated to bonus/base
    group_bonus_left = {g: min(group_spend[g], cap) for g in top_groups}
    details = []
    reward = 0
    # For each group
    for g, cats in group_map.items():
        for cat in cats:
            amt = user_spending.get(cat, 0)
            if amt == 0:
                continue
            if g in top_groups:
                # Allocate up to cap at bonus, rest at base
                amt_bonus = min(amt, group_bonus_left[g])
                amt_base = amt - amt_bonus
                if amt_bonus > 0:
                    reward_bonus = amt_bonus * bonus_rate * miles_to_sgd_rate
                    reward += reward_bonus
                    details.append({'Category': cat, 'Amount': amt_bonus, 'Rate': bonus_rate, 'Reward': reward_bonus})
                    group_bonus_left[g] -= amt_bonus
                if amt_base > 0:
                    reward_base = amt_base * base_rate * miles_to_sgd_rate
                    reward += reward_base
                    details.append({'Category': cat, 'Amount': amt_base, 'Rate': base_rate, 'Reward': reward_base})
            else:
                # Not a selected group, all at base
                reward_base = amt * base_rate * miles_to_sgd_rate
                reward += reward_base
                details.append({'Category': cat, 'Amount': amt, 'Rate': base_rate, 'Reward': reward_base})
    return reward, details


def calculate_trust_cashback_rewards(user_spending, tier):
    """
    For Trust Cashback: When min spend is met, all bonus categories (those in tier.reward_rates) get the high rate, others get 1%. If min spend is not met, all categories get 1%.
    """
    # Get the high rate from tier (should be the same for all bonus categories in CSV)
    high_rate = None
    for rate in tier.reward_rates.values():
        if rate > 1.0:  # Base rate is 1%
            high_rate = rate
            break
    if high_rate is None:
        high_rate = 5.0  # Default fallback

    # Calculate total spend for min spend check (all categories except 'total')
    total_spend = sum(amount for cat, amount in user_spending.items() if cat != 'total')
    min_spend_met = (tier.min_spend is None) or (total_spend >= (tier.min_spend or 0))

    reward = 0
    details = []
    if min_spend_met:
        for cat, amount in user_spending.items():
            if cat == 'total':
                continue
            if cat in tier.reward_rates:
                rate = high_rate
            else:
                rate = 1.0
            reward += amount * (rate / 100)
            details.append({
                'Category': cat,
                'Amount': amount,
                'Rate': rate,
                'Reward': amount * (rate / 100)
            })
    else:
        for cat, amount in user_spending.items():
            if cat == 'total':
                continue
            rate = 1.0
            reward += amount * (rate / 100)
            details.append({
                'Category': cat,
                'Amount': amount,
                'Rate': rate,
                'Reward': amount * (rate / 100)
            })
    return reward, details


def calculate_miles_card_with_bonus_cap(user_spending, miles_to_sgd_rate, tier, bonus_categories):
    """
    Generic function for miles cards with a cap on bonus categories.
    - Applies the bonus rate to the first $cap of spending in the bonus categories (combined).
    - Applies the base rate to any bonus category spending above the cap.
    - Applies the base rate to all other categories (uncapped).
    """
    base_rate = tier.base_rate or 0
    cap = tier.cap if tier.cap is not None else float('inf')
    bonus_rate = None
    # Assume all bonus categories have the same bonus rate in this tier
    for cat in bonus_categories:
        if cat in tier.reward_rates:
            bonus_rate = tier.reward_rates[cat]
            break
    if bonus_rate is None:
        bonus_rate = base_rate
    # Calculate total bonus category spend
    bonus_spending = [(cat, user_spending.get(cat, 0)) for cat in bonus_categories]
    total_bonus_spend = sum(amt for _, amt in bonus_spending)
    # How much of the bonus spend is within cap?
    bonus_within_cap = min(total_bonus_spend, cap)
    bonus_above_cap = max(total_bonus_spend - cap, 0)
    # Allocate bonus spend within and above cap proportionally
    details = []
    reward = 0
    # First, handle bonus categories
    if total_bonus_spend > 0:
        for cat, amt in bonus_spending:
            if amt == 0:
                continue
            # Proportion of this category's spend within cap
            if bonus_within_cap > 0:
                prop_within = min(amt, bonus_within_cap) / total_bonus_spend
                amt_within = prop_within * bonus_within_cap
            else:
                amt_within = 0
            amt_above = amt - amt_within
            # Bonus rate for within cap, base rate for above cap
            reward_within = amt_within * bonus_rate * miles_to_sgd_rate
            reward_above = amt_above * base_rate * miles_to_sgd_rate
            reward += reward_within + reward_above
            if amt_within > 0:
                details.append({
                    'Category': cat,
                    'Amount': amt_within,
                    'Rate': bonus_rate,
                    'Reward': reward_within
                })
            if amt_above > 0:
                details.append({
                    'Category': cat,
                    'Amount': amt_above,
                    'Rate': base_rate,
                    'Reward': reward_above
                })
    # Now, handle all other categories
    for cat, amt in user_spending.items():
        if cat == 'total' or cat in bonus_categories:
            continue
        if amt == 0:
            continue
        reward_cat = amt * base_rate * miles_to_sgd_rate
        reward += reward_cat
        details.append({
            'Category': cat,
            'Amount': amt,
            'Rate': base_rate,
            'Reward': reward_cat
        })
    return reward, details


def calculate_uob_visa_signature_rewards(user_spending, miles_to_sgd_rate, tier):
    """
    UOB Visa Signature: 4mpd split into two categories, FCY and non-FCY bonus categories (Dining, Groceries, Petrol, SimplyGo, Entertainment, Retail all combined into 1).
    Minimum spend is split into the grouped categories, the $1000 minimum applies to both FCY and non-FCY, and the cap of $1200 to each as well.
    To maximise card, user needs to spend $1000 on each to apply bonus, and max of $1200 in each category.
    """
    # Define groups
    fcy_group = ['fcy']
    non_fcy_group = ['dining', 'groceries', 'petrol', 'simplygo', 'entertainment', 'retail']
    base_rate = tier.base_rate or 0.4
    bonus_rate = 4.0
    min_spend = tier.min_spend or 1000
    cap = tier.cap or 1200
    details = []
    reward = 0
    # FCY group
    fcy_spend = sum(user_spending.get(cat, 0) for cat in fcy_group)
    fcy_min_met = fcy_spend >= min_spend
    fcy_bonus = min(fcy_spend, cap) if fcy_min_met else 0
    fcy_base = fcy_spend - fcy_bonus
    if fcy_bonus > 0:
        reward_fcy_bonus = fcy_bonus * bonus_rate * miles_to_sgd_rate
        reward += reward_fcy_bonus
        details.append({'Category': 'fcy', 'Amount': fcy_bonus, 'Rate': bonus_rate, 'Reward': reward_fcy_bonus})
    if fcy_base > 0:
        reward_fcy_base = fcy_base * base_rate * miles_to_sgd_rate
        reward += reward_fcy_base
        details.append({'Category': 'fcy', 'Amount': fcy_base, 'Rate': base_rate, 'Reward': reward_fcy_base})
    # Non-FCY group
    non_fcy_spend = sum(user_spending.get(cat, 0) for cat in non_fcy_group)
    non_fcy_min_met = non_fcy_spend >= min_spend
    non_fcy_bonus = min(non_fcy_spend, cap) if non_fcy_min_met else 0
    non_fcy_base = non_fcy_spend - non_fcy_bonus
    # Allocate bonus/base for each category in non-FCY group
    group_bonus_left = non_fcy_bonus
    for cat in non_fcy_group:
        amt = user_spending.get(cat, 0)
        if amt == 0:
            continue
        amt_bonus = min(amt, group_bonus_left)
        amt_base = amt - amt_bonus
        if amt_bonus > 0:
            reward_bonus = amt_bonus * bonus_rate * miles_to_sgd_rate
            reward += reward_bonus
            details.append({'Category': cat, 'Amount': amt_bonus, 'Rate': bonus_rate, 'Reward': reward_bonus})
            group_bonus_left -= amt_bonus
        if amt_base > 0:
            reward_base = amt_base * base_rate * miles_to_sgd_rate
            reward += reward_base
            details.append({'Category': cat, 'Amount': amt_base, 'Rate': base_rate, 'Reward': reward_base})
    # All other categories
    for cat, amt in user_spending.items():
        if cat == 'total' or cat in fcy_group or cat in non_fcy_group:
            continue
        if amt == 0:
            continue
        reward_cat = amt * base_rate * miles_to_sgd_rate
        reward += reward_cat
        details.append({'Category': cat, 'Amount': amt, 'Rate': base_rate, 'Reward': reward_cat})
    return reward, details
