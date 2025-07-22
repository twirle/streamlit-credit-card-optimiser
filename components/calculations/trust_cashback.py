from typing import Dict, Any, Tuple, List


def calculate_trust_cashback_rewards(user_spending: Dict[str, float], tier: Any) -> Tuple[float, List[Dict[str, Any]]]:
    """
    For Trust Cashback: When min spend is met, only the bonus category with the highest spending gets the high rate, all others get 1%. If min spend is not met, all categories get 1%.
    Args:
        user_spending: Dict of category to amount spent.
        tier: The card tier object (should have .reward_rates, .min_spend, .base_rate).
    Returns:
        Tuple of (total reward, breakdown list of dicts per category)
    """
    high_rate = None
    for rate in tier.reward_rates.values():
        if rate > 1.0:  # Base rate is 1%
            high_rate = rate
            break
    if high_rate is None:
        high_rate = 5.0  # Default fallback

    total_spend = sum(
        amount for cat, amount in user_spending.items() if cat != 'total')
    min_spend_met = (tier.min_spend is None) or (
        total_spend >= (tier.min_spend or 0))

    reward = 0
    details = []
    base_rate = 1.0
    bonus_cats = set(tier.reward_rates.keys())

    if min_spend_met:
        # Find the bonus category with the highest spending
        max_bonus_cat = None
        max_bonus_amt = -1
        for cat in bonus_cats:
            amt = user_spending.get(cat, 0)
            if amt > max_bonus_amt:
                max_bonus_amt = amt
                max_bonus_cat = cat
        for cat, amount in user_spending.items():
            if cat == 'total':
                continue
            if cat == max_bonus_cat and amount > 0:
                rate = high_rate
            else:
                rate = base_rate
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
            rate = base_rate
            reward += amount * (rate / 100)
            details.append({
                'Category': cat,
                'Amount': amount,
                'Rate': rate,
                'Reward': amount * (rate / 100)
            })
    return reward, details
