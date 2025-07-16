"""
Credit Card Data Models and Schemas

This module defines the data structures and validation schemas
for credit card information used throughout the application.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import pandas as pd

@dataclass
class CreditCard:
    card_id: int
    name: str
    issuer: str
    card_type: str  # 'Miles' or 'Cashback'

    def __post_init__(self):
        if self.card_type not in ['Miles', 'Cashback']:
            raise ValueError("Card type must be 'Miles' or 'Cashback'")

@dataclass
class CardTier:
    tier_id: int
    card_id: int
    min_spend: float
    description: str = ""

@dataclass
class CategoryRate:
    tier_id: int
    category: str
    rate_value: float
    rate_type: str  # 'percentage' or 'mpd'
    cap_amount: Optional[float] = None
    cap_type: Optional[str] = None  # 'dollars_earned' or 'dollars_spent'

    def __post_init__(self):
        if self.rate_type not in ['percentage', 'mpd']:
            raise ValueError("Rate type must be 'percentage' or 'mpd'")
        if self.cap_type and self.cap_type not in ['dollars_earned', 'dollars_spent']:
            raise ValueError(
                "Cap type must be 'dollars_earned' or 'dollars_spent'")

@dataclass
class CardCategory:
    card_id: int
    category: str

@dataclass
class UserSpending:
    dining: float = 0.0
    groceries: float = 0.0
    petrol: float = 0.0
    transport: float = 0.0
    streaming: float = 0.0
    entertainment: float = 0.0
    utilities: float = 0.0
    online: float = 0.0
    travel: float = 0.0
    overseas: float = 0.0
    retail: float = 0.0
    departmental: float = 0.0
    other: float = 0.0

    @property
    def total(self) -> float:
        return sum([
            self.dining, self.groceries, self.petrol, self.transport,
            self.streaming, self.entertainment, self.utilities,
            self.online, self.travel, self.overseas, self.retail, 
            self.departmental, self.other
        ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'dining': self.dining,
            'groceries': self.groceries,
            'petrol': self.petrol,
            'transport': self.transport,
            'streaming': self.streaming,
            'entertainment': self.entertainment,
            'utilities': self.utilities,
            'online': self.online,
            'travel': self.travel,
            'overseas': self.overseas,
            'retail': self.retail,
            'departmental': self.departmental,
            'other': self.other,
            'total': self.total
        }

@dataclass
class RewardCalculation:
    card_name: str
    tier_description: str
    monthly_reward: float
    cap_reached: bool
    cap_difference: Optional[float] = None
    original_reward: float = 0.0
    min_spend_met: bool = True
    details: Optional[List[str]] = None

    def __post_init__(self):
        if self.details is None:
            self.details = []

@dataclass
class CardRewardBreakdown:
    card_id: int
    card_name: str
    tier_id: int
    tier_description: str
    category_rewards: Dict[str, float]
    total_reward: float
    cap_status: Dict[str, Any]
    min_spend_met: bool

def validate_credit_card_data(cards_df: pd.DataFrame, tiers_df: pd.DataFrame,
                              rates_df: pd.DataFrame, categories_df: pd.DataFrame) -> bool:
    required_cards_columns = ['card_id', 'name', 'issuer', 'card_type']
    required_tiers_columns = ['tier_id', 'card_id', 'min_spend']
    required_rates_columns = ['tier_id', 'category', 'rate_value', 'rate_type']
    required_categories_columns = ['card_id', 'category']

    for col in required_cards_columns:
        if col not in cards_df.columns:
            return False
    for col in required_tiers_columns:
        if col not in tiers_df.columns:
            return False
    for col in required_rates_columns:
        if col not in rates_df.columns:
            return False
    for col in required_categories_columns:
        if col not in categories_df.columns:
            return False
    if not all(cards_df['card_type'].isin(['Miles', 'Cashback'])):
        return False
    if not all(rates_df['rate_type'].isin(['percentage', 'mpd'])):
        return False
    card_ids = set(cards_df['card_id'])
    tier_card_ids = set(tiers_df['card_id'])
    rate_tier_ids = set(rates_df['tier_id'])
    category_card_ids = set(categories_df['card_id'])
    if not tier_card_ids.issubset(card_ids):
        return False
    if not category_card_ids.issubset(card_ids):
        return False
    return True 