def calculate_uob_ladys_rewards(user_spending, miles_to_sgd_rate, tier):
    """
    For UOB Lady's: Only one eligible category (dining, entertainment, retail, travel) gets 4 mpd, the rest get 0.4 mpd.
    The category with the highest user spending is selected for 4 mpd.
    """
    eligible = ['dining', 'entertainment', 'retail', 'travel']
    max_cat = max(eligible, key=lambda cat: user_spending.get(cat, 0))
    reward = 0
    details = []
    for cat, amount in user_spending.items():
        if cat == 'total':
            continue
        if cat == max_cat:
            rate = 4.0
        else:
            rate = 0.4
        reward += amount * rate * miles_to_sgd_rate
        details.append({
            'Category': cat,
            'Amount': amount,
            'Rate': rate,
            'Reward': amount * rate * miles_to_sgd_rate
        })
    return reward, details


def calculate_trust_cashback_rewards(user_spending, tier):
    """
    For Trust Cashback: Only one category gets the high cashback rate, others get 1%.
    The eligible categories are: dining, shopping (retail+online+groceries), travel, transport (including petrol), entertainment (including streaming).
    The category with the highest user spending is selected for the high rate.
    """
    # Define category groupings for Trust Cashback
    category_groups = {
        'dining': ['dining'],
        'shopping': ['retail', 'online', 'groceries'],
        'travel': ['travel'],
        'transport': ['transport', 'petrol'],
        'entertainment': ['entertainment', 'streaming']
    }
    
    # Calculate total spending for each group
    group_totals = {}
    for group_name, categories in category_groups.items():
        group_totals[group_name] = sum(user_spending.get(cat, 0) for cat in categories)
    
    # Find the group with highest spending
    max_group = max(group_totals.keys(), key=lambda g: group_totals[g])
    
    # Get the high rate from tier (should be the same for all categories in CSV)
    high_rate = None
    for rate in tier.reward_rates.values():
        if rate > 1.0:  # Base rate is 1%
            high_rate = rate
            break
    
    if high_rate is None:
        high_rate = 5.0  # Default fallback
    
    # Check if minimum spend is met in bonus categories
    # Minimum spend includes ALL bonus categories, not just the highest one
    all_bonus_spend = sum(group_totals.values())  # Total spending across all bonus categories
    min_spend_met = (tier.min_spend is None) or (all_bonus_spend >= tier.min_spend)
    
    reward = 0
    details = []
    
    # Process each category
    for cat, amount in user_spending.items():
        if cat == 'total':
            continue
            
        # Determine which group this category belongs to
        category_group = None
        for group_name, categories in category_groups.items():
            if cat in categories:
                category_group = group_name
                break
        
        # Apply rate based on group and minimum spend requirement
        if min_spend_met and category_group == max_group:
            rate = high_rate
        else:
            rate = 1.0  # Base rate for other categories or if min spend not met
            
        reward += amount * (rate / 100)  # Convert percentage to decimal
        details.append({
            'Category': cat,
            'Amount': amount,
            'Rate': rate,
            'Reward': amount * (rate / 100)
        })
    
    return reward, details

# Future card-specific calculation functions can be added here. 