"""
Card Data Validator

This module handles validation of credit card data structure and integrity.
"""

import pandas as pd
from typing import Tuple


class CardDataValidator:
    """Validates credit card data structure and integrity"""

    @staticmethod
    def validate_card_data(available_cards: pd.DataFrame, card_tiers: pd.DataFrame,
                          reward_rates: pd.DataFrame, card_categories: pd.DataFrame) -> bool:
        """
        Validate credit card data structure and relationships

        Args:
            available_cards: DataFrame of available cards
            card_tiers: DataFrame of card tiers
            reward_rates: DataFrame of reward rates
            card_categories: DataFrame of card categories

        Returns:
            bool: True if data is valid, False otherwise
        """
        # Check required columns exist
        required_cards_columns = ['card_id', 'name', 'issuer', 'card_type']
        required_tiers_columns = ['tier_id', 'card_id', 'min_spend']
        required_rates_columns = ['tier_id', 'category', 'rate_value', 'rate_type']
        required_categories_columns = ['card_id', 'category']

        # Validate cards DataFrame
        for col in required_cards_columns:
            if col not in available_cards.columns:
                return False
        
        # Validate tiers DataFrame
        for col in required_tiers_columns:
            if col not in card_tiers.columns:
                return False
        
        # Validate rates DataFrame
        for col in required_rates_columns:
            if col not in reward_rates.columns:
                return False
        
        # Validate categories DataFrame
        for col in required_categories_columns:
            if col not in card_categories.columns:
                return False

        # Validate data types and values
        if not all(available_cards['card_type'].isin(['Miles', 'Cashback'])):
            return False
        
        if not all(reward_rates['rate_type'].isin(['percentage', 'mpd'])):
            return False

        # Validate referential integrity
        card_ids = set(available_cards['card_id'])
        tier_card_ids = set(card_tiers['card_id'])
        rate_tier_ids = set(reward_rates['tier_id'])
        category_card_ids = set(card_categories['card_id'])
        
        if not tier_card_ids.issubset(card_ids):
            return False
        
        if not category_card_ids.issubset(card_ids):
            return False

        return True

    @staticmethod
    def validate_spending_data(spending_data: dict) -> Tuple[bool, str]:
        """
        Validate user spending data

        Args:
            spending_data: Dictionary containing spending data

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_categories = [
            'dining', 'groceries', 'petrol', 'transport', 'streaming',
            'entertainment', 'utilities', 'online', 'travel', 'overseas', 
            'retail', 'departmental', 'other'
        ]
        
        # Check all required categories exist
        for category in required_categories:
            if category not in spending_data:
                return False, f"Missing required category: {category}"
        
        # Check all values are numeric and non-negative
        for category, value in spending_data.items():
            if category != 'total':  # Skip total as it's calculated
                try:
                    float_value = float(value)
                    if float_value < 0:
                        return False, f"Negative value not allowed for {category}: {value}"
                except (ValueError, TypeError):
                    return False, f"Invalid numeric value for {category}: {value}"
        
        return True, "Data is valid" 