from typing import Dict, Any, Tuple, List


def calculate_uob_visa_signature_rewards(user_spending: Dict[str, float], miles_to_sgd_rate: float, tier: Any) -> Tuple[float, List[Dict[str, Any]]]:
    """
    UOB Visa Signature: 4mpd split into two categories, FCY and non-FCY bonus categories (Dining, Groceries, Petrol, SimplyGo, Entertainment, Retail all combined into 1).
    Minimum spend is split into the grouped categories, the $1000 minimum applies to both FCY and non-FCY, and the cap of $1200 to each as well.
    To maximise card, user needs to spend $1000 on each to apply bonus, and max of $1200 in each category.
    Args:
        user_spending: Dict of category to amount spent.
        miles_to_sgd_rate: Conversion rate from miles to SGD.
        tier: The card tier object (should have .reward_rates, .cap, .base_rate, .min_spend).
    Returns:
        Tuple of (total reward, breakdown list of dicts per category)
    """
    fcy_group = ['fcy']
    non_fcy_group = ['dining', 'groceries', 'petrol',
                     'simplygo', 'entertainment', 'retail']
    base_rate = tier.base_rate or 0.4
    bonus_rate = 4.0
    min_spend = tier.min_spend or 1000
    cap = tier.cap or 1200
    details = []
    reward = 0
    fcy_spend = sum(user_spending.get(cat, 0) for cat in fcy_group)
    fcy_min_met = fcy_spend >= min_spend
    fcy_bonus = min(fcy_spend, cap) if fcy_min_met else 0
    fcy_base = fcy_spend - fcy_bonus
    if fcy_bonus > 0:
        reward_fcy_bonus = fcy_bonus * bonus_rate * miles_to_sgd_rate
        reward += reward_fcy_bonus
        details.append({'Category': 'fcy', 'Amount': fcy_bonus,
                       'Rate': bonus_rate, 'Reward': reward_fcy_bonus})
    if fcy_base > 0:
        reward_fcy_base = fcy_base * base_rate * miles_to_sgd_rate
        reward += reward_fcy_base
        details.append({'Category': 'fcy', 'Amount': fcy_base,
                       'Rate': base_rate, 'Reward': reward_fcy_base})
    non_fcy_spend = sum(user_spending.get(cat, 0) for cat in non_fcy_group)
    non_fcy_min_met = non_fcy_spend >= min_spend
    non_fcy_bonus = min(non_fcy_spend, cap) if non_fcy_min_met else 0
    non_fcy_base = non_fcy_spend - non_fcy_bonus
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
            details.append({'Category': cat, 'Amount': amt_bonus,
                           'Rate': bonus_rate, 'Reward': reward_bonus})
            group_bonus_left -= amt_bonus
        if amt_base > 0:
            reward_base = amt_base * base_rate * miles_to_sgd_rate
            reward += reward_base
            details.append({'Category': cat, 'Amount': amt_base,
                           'Rate': base_rate, 'Reward': reward_base})
    for cat, amt in user_spending.items():
        if cat == 'total' or cat in fcy_group or cat in non_fcy_group:
            continue
        if amt == 0:
            continue
        reward_cat = amt * base_rate * miles_to_sgd_rate
        reward += reward_cat
        details.append({'Category': cat, 'Amount': amt,
                       'Rate': base_rate, 'Reward': reward_cat})
    return reward, details
