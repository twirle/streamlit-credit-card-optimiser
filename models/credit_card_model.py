from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class CardTier(BaseModel):
    min_spend: Optional[float] = None
    cap: Optional[float] = None
    # e.g., {'dining': 6.0, 'groceries': 6.0}
    reward_rates: Dict[str, float] = Field(default_factory=dict)
    base_rate: Optional[float] = None
    description: Optional[str] = None  # e.g., 'Standard', 'High Tier', etc.
    # For future/unknown fields
    extra: Dict[str, Any] = Field(default_factory=dict)


class CreditCard(BaseModel):
    name: str
    issuer: str
    card_type: str  # e.g., 'Cashback', 'Miles'
    income_requirement: Optional[float] = None
    categories: List[str] = Field(default_factory=list)
    source: Optional[str] = None  # URL or reference
    tiers: List[CardTier] = Field(default_factory=list)
    # For future/unknown fields
    extra: Dict[str, Any] = Field(default_factory=dict)

    def add_tier(self, tier: CardTier):
        self.tiers.append(tier)
