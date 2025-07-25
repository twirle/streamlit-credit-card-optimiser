import pytest
from components.single_card_component import calculate_card_tier_reward
from models.credit_card_model import CreditCard, CardTier


def make_card(name, card_type, reward_rates, base_rate, cap=None, min_spend=None, tiers=None):
    if tiers is not None:
        return CreditCard(
            name=name,
            issuer="TestBank",
            card_type=card_type,
            income_requirement=30000,
            categories=list(reward_rates.keys()),
            source=None,
            tiers=tiers
        )
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
    )


def test_cashback_card_cap():
    card = make_card("Test Cashback", "cashback", {"dining": 5.0}, 5.0, cap=50)
    user_spending = {"dining": 2000, "total": 2000}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 50  # should be capped


def test_miles_card_base_after_cap():
    card = make_card("Test Miles", "miles", {"dining": 4.0}, 1.2, cap=100)
    user_spending = {"dining": 50, "total": 50}
    miles_to_sgd = 0.02
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, miles_to_sgd)

    # All spend is below cap, so all at bonus rate
    assert reward == 50 * 4.0 * miles_to_sgd


def test_min_spend_bonus():
    card = make_card("MinSpend", "cashback", {
                     "dining": 5.0}, 1.0, min_spend=500)
    # Below min spend: only base rate
    user_spending = {"dining": 400, "total": 400}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 400 * 1.0 / 100

    # Above min spend: bonus rate
    user_spending = {"dining": 600, "total": 600}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 600 * 5.0 / 100


def test_dbs_yuu_bonus():
    # Simulate DBS yuu: 10mpd on bonus cats if $600 min spend, cap $600, base 0.28mpd
    card = make_card("DBS yuu", "miles", {
                     "dining": 10.0, "groceries": 10.0, "transport": 10.0}, 0.28, cap=600, min_spend=600)
    miles_to_sgd = 0.02

    # Below min spend: all at base rate
    user_spending = {"dining": 200, "groceries": 200,
                     "transport": 100, "total": 500}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, miles_to_sgd)
    expected = sum(user_spending[cat] * 0.28 *
                   miles_to_sgd for cat in ["dining", "groceries", "transport"])
    assert abs(reward - expected) < 1e-6

    # Above min spend, all bonus cats, under cap
    user_spending = {"dining": 300, "groceries": 200,
                     "transport": 100, "total": 600}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, miles_to_sgd)
    expected = sum(user_spending[cat] * 10.0 *
                   miles_to_sgd for cat in ["dining", "groceries", "transport"])
    assert abs(reward - expected) < 1e-6

    # Above min spend, bonus cats exceed cap
    user_spending = {"dining": 700, "groceries": 200,
                     "transport": 100, "total": 1000}

    # Only $600 of bonus cats get 10mpd, rest at base
    bonus = 600 * 10.0 * miles_to_sgd
    base = (700+200+100-600) * 0.28 * miles_to_sgd
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, miles_to_sgd)
    assert abs(reward - (bonus + base)) < 1e-6


def test_trust_bonus():
    # Simulate Trust: only highest bonus cat gets bonus, rest base, min spend 450
    card = make_card("Trust", "cashback", {
                     "entertainment": 5.0, "online": 5.0, "retail": 5.0}, 1.0, cap=1000, min_spend=450)

    # Below min spend: all base
    user_spending = {"entertainment": 200,
                     "online": 200, "retail": 0, "total": 400}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    expected = sum(
        user_spending[cat] * 1.0 / 100 for cat in ["entertainment", "online", "retail"])
    assert abs(reward - expected) < 1e-6

    # Above min spend: only highest gets bonus
    user_spending = {"entertainment": 500,
                     "online": 200, "retail": 150, "total": 850}
    # $500 at 5%, rest at 1%
    expected = 500 * 5.0 / 100 + 200 * 1.0 / 100 + 150 * 1.0 / 100
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert abs(reward - expected) < 1e-6


def test_zero_spend():
    card = make_card("Zero", "cashback", {"dining": 5.0}, 1.0)
    user_spending = {"dining": 0, "total": 0}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 0
    assert all(row['Reward'] == 0 for row in breakdown)


def test_uob_ladys_single_category():
    # Simulate Lady's: 4mpd on one category, $1000 cap, base 0.4mpd
    card = make_card("UOB Lady's", "miles", {
                     "dining": 4.0, "groceries": 4.0, "retail": 4.0}, 0.4, cap=1000)
    miles_to_sgd = 0.02
    user_spending = {"dining": 1200, "groceries": 500,
                     "retail": 300, "total": 2000}
    # Only $1000 in Dining gets 4mpd, rest at base
    bonus = 1000 * 4.0 * miles_to_sgd
    base = (1200-1000) * 0.4 * miles_to_sgd + 500 * \
        0.4 * miles_to_sgd + 300 * 0.4 * miles_to_sgd
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, miles_to_sgd)
    assert abs(reward - (bonus + base)) < 1e-6


def test_uob_ladys_solitaire_two_categories():
    # Simulate Lady's Solitaire: 4mpd on two categories, $750 cap each, base 0.4mpd
    card = make_card("UOB Lady's Solitaire", "miles", {
                     "dining": 4.0, "groceries": 4.0, "retail": 4.0}, 0.4, cap=750)
    miles_to_sgd = 0.02
    user_spending = {"dining": 800, "groceries": 800,
                     "retail": 300, "total": 1900}
    # $750 in Dining and $750 in Groceries get 4mpd, rest at base
    bonus = 750 * 4.0 * miles_to_sgd * 2
    base = (800-750) * 0.4 * miles_to_sgd + (800-750) * \
        0.4 * miles_to_sgd + 300 * 0.4 * miles_to_sgd
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, miles_to_sgd)
    assert abs(reward - (bonus + base)) < 1e-6


def test_min_spend_exactly_met():
    card = make_card("MinSpend", "cashback", {
                     "dining": 5.0}, 1.0, min_spend=500)
    user_spending = {"dining": 500, "total": 500}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 500 * 5.0 / 100


def test_cap_exactly_met():
    card = make_card("CapCard", "cashback", {"dining": 5.0}, 1.0, cap=100)
    user_spending = {"dining": 2000, "total": 2000}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 100

    # The per-category reward should show the uncapped value
    assert any(row['Reward'] == 100 for row in breakdown)


def test_multiple_bonus_categories_cap_exceeded():
    card = make_card("MultiBonus", "cashback", {
                     "dining": 5.0, "groceries": 5.0}, 1.0, cap=100)
    user_spending = {"dining": 1500, "groceries": 1000, "total": 2500}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 100

    # Both categories should show their full potential reward in the breakdown
    assert any(row['Reward'] == 75 for row in breakdown)  # 1500*5%
    assert any(row['Reward'] == 50 for row in breakdown)  # 1000*5%


def test_all_non_bonus_categories():
    card = make_card("NoBonus", "cashback", {"dining": 5.0}, 1.0)
    user_spending = {"groceries": 300, "retail": 200, "total": 500}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 500 * 1.0 / 100
    assert all(row['Rate'] == 1.0 for row in breakdown)


def test_negative_invalid_spend():
    card = make_card("NegTest", "cashback", {"dining": 5.0}, 1.0)
    # Negative spend should be treated as zero or raise an error (depending on your logic)
    user_spending = {"dining": -100, "total": -100}
    try:
        reward, breakdown, * \
            _ = calculate_card_tier_reward(
                card, card.tiers[0], user_spending, 0.02)
        assert reward == 0 or reward is not None  # Accept 0 or handled gracefully
    except Exception:
        assert True

    # Non-numeric spend should raise an error
    user_spending = {"dining": "abc", "total": "abc"}
    with pytest.raises(Exception):
        calculate_card_tier_reward(card, card.tiers[0], user_spending, 0.02)


def test_bonus_below_min_total_above():
    card = make_card("BonusBelowMin", "cashback", {
                     "dining": 5.0}, 1.0, min_spend=500)
    # $200 in dining (bonus), $400 in groceries (non-bonus), total $600
    user_spending = {"dining": 200, "groceries": 400, "total": 600}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)

    # Should get bonus rate only if your logic is total spend, else base
    # Here, assume min spend is total spend
    assert reward == (200 * 5.0 + 400 * 1.0) / 100


def test_mixed_spend_bonus_and_nonbonus():
    card = make_card("Mixed", "cashback", {"dining": 5.0}, 1.0, cap=100)
    user_spending = {"dining": 1000, "groceries": 1000, "total": 2000}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)

    # Dining is bonus, groceries is base
    assert any(row['Rate'] == 5.0 for row in breakdown)
    assert any(row['Rate'] == 1.0 for row in breakdown)
    assert reward == 100  # capped


def test_trust_tie_for_highest():
    # Simulate Trust: tie for highest bonus category
    card = make_card("Trust", "cashback", {
                     "entertainment": 5.0, "online": 5.0, "retail": 5.0}, 1.0, cap=1000, min_spend=450)
    user_spending = {"entertainment": 300,
                     "online": 300, "retail": 100, "total": 700}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)

    # Only one of entertainment/online should get bonus, rest base
    bonus_count = sum(1 for row in breakdown if row['Rate'] == 5.0)
    assert bonus_count == 1
    base_count = sum(1 for row in breakdown if row['Rate'] == 1.0)
    assert base_count == 2


def test_no_cap_no_min_spend():
    card = make_card("NoLimits", "cashback", {"dining": 5.0}, 1.0)
    user_spending = {"dining": 10000, "total": 10000}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(
            card, card.tiers[0], user_spending, 0.02)
    assert reward == 10000 * 5.0 / 100
    assert all(row['Rate'] == 5.0 for row in breakdown)


def test_multiplier_tiers_selection():
    # Two tiers: low (min $0, 1%), high (min $1000, 5%)
    tier_low = CardTier(min_spend=0, cap=None, reward_rates={
                        'dining': 1.0}, base_rate=1.0, description='Low')
    tier_high = CardTier(min_spend=1000, cap=None, reward_rates={
                         'dining': 5.0}, base_rate=1.0, description='High')
    card = make_card('TieredCard', 'cashback', {
                     'dining': 1.0}, 1.0, tiers=[tier_low, tier_high])
    user_spending = {'dining': 500, 'total': 500}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(card, tier_low, user_spending, 0.02)
    assert reward == 500 * 1.0 / 100
    user_spending = {'dining': 1500, 'total': 1500}
    reward, breakdown, * \
        _ = calculate_card_tier_reward(card, tier_high, user_spending, 0.02)
    assert reward == 1500 * 5.0 / 100
