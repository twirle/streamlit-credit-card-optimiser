import pytest
from components.multi_card_component import allocate_spending_two_cards
from models.credit_card_model import CreditCard, CardTier


def make_card(name, card_type, reward_rates, base_rate, cap=None, min_spend=None):
    tier = CardTier(
        min_spend=min_spend,
        cap=cap,
        reward_rates=reward_rates,
        base_rate=base_rate,
        description="Test Tier"
    )
    return CreditCard(
        name=name,
        issuer="TestBank",
        card_type=card_type,
        income_requirement=30000,
        categories=list(reward_rates.keys()),
        source=None,
        tiers=[tier]
    ), tier


def test_optimal_allocation_cashback():
    card1, tier1 = make_card("Card1", "cashback", {"dining": 5.0}, 1.0, cap=50)
    card2, tier2 = make_card("Card2", "cashback", {
                             "dining": 2.0}, 1.0, cap=100)
    user_spending = {"dining": 2000, "total": 2000}
    reward1, breakdown1, reward2, breakdown2, total = allocate_spending_two_cards(
        card1, tier1, card2, tier2, user_spending, 0.02)

    # All spend should go to card1 until its cap, then to card2
    assert reward1 == 50
    assert reward2 == (2000 * 0.02) - 50
    assert total == reward1 + reward2


def test_dbs_yuu_allocation():
    card1, tier1 = make_card("DBS yuu", "miles", {
                             "dining": 10.0, "groceries": 10.0, "transport": 10.0}, 0.28, cap=600, min_spend=600)
    card2, tier2 = make_card("Other Miles", "miles", {"dining": 4.0}, 1.2)
    user_spending = {"dining": 700, "groceries": 100,
                     "transport": 0, "total": 800}
    reward1, breakdown1, reward2, breakdown2, total = allocate_spending_two_cards(
        card1, tier1, card2, tier2, user_spending, 0.02)

    # Yuu should get $600 of bonus spend, rest to other card
    yuu_bonus = 600 * 10.0 * 0.02
    other_bonus = (700 + 100 - 600) * 4.0 * 0.02
    assert abs(reward1 - yuu_bonus) < 1e-6
    assert abs(reward2 - other_bonus) < 1e-6
    assert abs(total - (yuu_bonus + other_bonus)) < 1e-6

# Add more tests for Trust, UOB Lady's, etc.
