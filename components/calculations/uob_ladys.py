from typing import Dict, Any, Tuple, List

UOB_LADYS_GROUP_MAP = {
    'dining': ['dining'],
    'entertainment': ['entertainment'],
    'retail': ['retail'],
    'transport': ['transport', 'simplygo', 'petrol'],
    'travel': ['travel']
}


def calculate_uob_ladys_rewards(user_spending: Dict[str, float], miles_to_sgd_rate: float, tier: Any, is_solitaire: bool = False) -> Tuple[float, List[Dict[str, Any]]]:
    """
    For UOB Lady's: Only one eligible group (Dining, Entertainment, Retail, Transport, Travel) gets 4 mpd, capped per group. Lady's Solitaire: two groups, each capped.
    Transport group includes Transport, SimplyGo, Petrol.
    Args:
        user_spending: Dict of category to amount spent.
        miles_to_sgd_rate: Conversion rate from miles to SGD.
        tier: The card tier object (should have .reward_rates, .cap, .base_rate).
        is_solitaire: If True, Lady's Solitaire logic (two groups get bonus).
    Returns:
        Tuple of (total reward, breakdown list of dicts per category)
    """
    group_map = UOB_LADYS_GROUP_MAP
    base_rate = tier.base_rate or 0.4
    bonus_rate = 4.0
    cap = tier.cap if tier.cap is not None else float('inf')
    group_spend = {g: sum(user_spending.get(cat, 0)
                          for cat in cats) for g, cats in group_map.items()}
    n_groups = 2 if is_solitaire else 1
    top_groups = sorted(group_spend, key=lambda g: group_spend[g], reverse=True)[
        :n_groups]
    group_bonus_left = {g: min(group_spend[g], cap) for g in top_groups}

    details = []
    reward = 0
    for g, cats in group_map.items():
        for cat in cats:
            amt = user_spending.get(cat, 0)
            if amt == 0:
                continue
            if g in top_groups:
                amt_bonus = min(amt, group_bonus_left[g])
                amt_base = amt - amt_bonus
                if amt_bonus > 0:
                    reward_bonus = amt_bonus * bonus_rate * miles_to_sgd_rate
                    reward += reward_bonus
                    details.append({'Category': cat, 'Amount': amt_bonus,
                                   'Rate': bonus_rate, 'Reward': reward_bonus})
                    group_bonus_left[g] -= amt_bonus
                if amt_base > 0:
                    reward_base = amt_base * base_rate * miles_to_sgd_rate
                    reward += reward_base
                    details.append(
                        {'Category': cat, 'Amount': amt_base, 'Rate': base_rate, 'Reward': reward_base})
            else:
                reward_base = amt * base_rate * miles_to_sgd_rate
                reward += reward_base
                details.append({'Category': cat, 'Amount': amt,
                               'Rate': base_rate, 'Reward': reward_base})
    return reward, details
