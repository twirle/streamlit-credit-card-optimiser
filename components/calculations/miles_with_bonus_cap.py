from typing import Dict, Any, Tuple, List


def calculate_miles_card_with_bonus_cap(user_spending: Dict[str, float], miles_to_sgd_rate: float, tier: Any, bonus_categories: List[str]) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Generic function for miles cards with a cap on bonus categories.
    - Applies the bonus rate to the first $cap of spending in the bonus categories (combined).
    - Applies the base rate to any bonus category spending above the cap.
    - Applies the base rate to all other categories (uncapped).
    Args:
        user_spending: Dict of category to amount spent.
        miles_to_sgd_rate: Conversion rate from miles to SGD.
        tier: The card tier object (should have .reward_rates, .cap, .base_rate).
        bonus_categories: List of bonus category names.
    Returns:
        Tuple of (total reward, breakdown list of dicts per category)
    """
    base_rate = tier.base_rate or 0
    cap = tier.cap if tier.cap is not None else float('inf')
    bonus_rate = None
    for cat in bonus_categories:
        if cat in tier.reward_rates:
            bonus_rate = tier.reward_rates[cat]
            break
    if bonus_rate is None:
        bonus_rate = base_rate
    bonus_spending = [(cat, user_spending.get(cat, 0))
                      for cat in bonus_categories]
    total_bonus_spend = sum(amt for _, amt in bonus_spending)
    bonus_within_cap = min(total_bonus_spend, cap)
    bonus_above_cap = max(total_bonus_spend - cap, 0)
    details = []
    reward = 0
    if total_bonus_spend > 0:
        for cat, amt in bonus_spending:
            if amt == 0:
                continue
            if bonus_within_cap > 0:
                prop_within = min(amt, bonus_within_cap) / total_bonus_spend
                amt_within = prop_within * bonus_within_cap
            else:
                amt_within = 0
            amt_above = amt - amt_within
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
