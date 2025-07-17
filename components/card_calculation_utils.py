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

# Future card-specific calculation functions can be added here. 