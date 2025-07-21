from components.calculations.trust_cashback import calculate_trust_cashback_rewards
from components.calculations.uob_ladys import calculate_uob_ladys_rewards
from components.calculations.uob_visa_signature import calculate_uob_visa_signature_rewards
from components.calculations.miles_with_bonus_cap import calculate_miles_card_with_bonus_cap

# Group definitions for UOB Lady's/Lady's Solitaire (shared for single and multi-card logic)
UOB_LADYS_GROUP_MAP = {
    'dining': ['dining'],
    'entertainment': ['entertainment'],
    'retail': ['retail'],
    'transport': ['transport', 'simplygo', 'petrol'],
    'travel': ['travel']
}
