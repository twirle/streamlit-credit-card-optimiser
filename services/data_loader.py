"""
Data Loading Service

This module handles loading and processing of credit card data
from various sources including CSV files and APIs.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import streamlit as st

from models.credit_card_model import (
    CreditCard, CardTier, CategoryRate, CardCategory,
    validate_credit_card_data
)


class DataLoader:
    """Service for loading and managing credit card data"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._cards_df = None
        self._tiers_df = None
        self._rates_df = None
        self._categories_df = None

    def load_credit_card_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load normalized credit card data from CSV files

        Returns:
            Tuple of (cards_df, tiers_df, rates_df, categories_df)
        """
        try:
            # Load all CSV files
            cards_df = pd.read_csv(self.data_dir / "cards.csv")
            tiers_df = pd.read_csv(self.data_dir / "card_tiers.csv")
            rates_df = pd.read_csv(self.data_dir / "category_rates.csv")
            categories_df = pd.read_csv(self.data_dir / "card_categories.csv")

            # Validate data using original column names
            if not validate_credit_card_data(cards_df, tiers_df, rates_df, categories_df):
                raise ValueError("Invalid credit card data structure")

            # Rename columns to Title Case for consistency across the app
            cards_df = cards_df.rename(columns={
                'name': 'Card Name',
                'card_type': 'Card Type',
                'issuer': 'Issuer'
            })
            
            tiers_df = tiers_df.rename(columns={
                'min_spend': 'Min Spend',
                'description': 'Description'
            })
            
            rates_df = rates_df.rename(columns={
                'rate_value': 'Rate Value',
                'rate_type': 'Rate Type',
                'cap_amount': 'Cap Amount',
                'cap_type': 'Cap Type'
            })

            # Store for caching
            self._cards_df = cards_df
            self._tiers_df = tiers_df
            self._rates_df = rates_df
            self._categories_df = categories_df

            return cards_df, tiers_df, rates_df, categories_df

        except FileNotFoundError as e:
            st.error(f"Data file not found: {e}")
            raise
        except Exception as e:
            st.error(f"Error loading credit card data: {e}")
            raise

    def get_cards_by_type(self, card_type: str) -> pd.DataFrame:
        """
        Get cards filtered by type (Miles or Cashback)

        Args:
            card_type: Type of cards to filter ('Miles' or 'Cashback')

        Returns:
            DataFrame of filtered cards
        """
        if self._cards_df is None:
            self.load_credit_card_data()

        return self._cards_df[self._cards_df['Card Type'] == card_type]

    def get_card_tiers(self, card_id: int) -> pd.DataFrame:
        """
        Get all tiers for a specific card

        Args:
            card_id: ID of the card

        Returns:
            DataFrame of card tiers
        """
        if self._tiers_df is None:
            self.load_credit_card_data()

        return self._tiers_df[self._tiers_df['card_id'] == card_id]

    def get_category_rates(self, tier_id: int) -> pd.DataFrame:
        """
        Get all category rates for a specific tier

        Args:
            tier_id: ID of the tier

        Returns:
            DataFrame of category rates
        """
        if self._rates_df is None:
            self.load_credit_card_data()

        return self._rates_df[self._rates_df['tier_id'] == tier_id]

    def get_card_categories(self, card_id: int) -> List[str]:
        """
        Get all categories supported by a card

        Args:
            card_id: ID of the card

        Returns:
            List of category names
        """
        if self._categories_df is None:
            self.load_credit_card_data()

        categories = self._categories_df[self._categories_df['card_id']
                                         == card_id]['category'].tolist()
        return categories

    def get_best_tier_for_spending(self, card_id: int, total_spending: float) -> Optional[CardTier]:
        """
        Find the best tier for a card based on total spending

        Args:
            card_id: ID of the card
            total_spending: Total monthly spending

        Returns:
            Best CardTier object or None if no suitable tier
        """
        tiers = self.get_card_tiers(card_id)

        # Filter tiers where min_spend is met
        suitable_tiers = tiers[tiers['Min Spend'] <= total_spending]

        if suitable_tiers.empty:
            return None

        # Get the tier with highest min_spend (best tier)
        best_tier_row = suitable_tiers.loc[suitable_tiers['Min Spend'].idxmax(
        )]

        return CardTier(
            tier_id=best_tier_row['tier_id'],
            card_id=best_tier_row['card_id'],
            min_spend=best_tier_row['Min Spend'],
            description=best_tier_row['Description']
        )

    def get_card_info(self, card_id: int) -> Optional[CreditCard]:
        """
        Get complete card information

        Args:
            card_id: ID of the card

        Returns:
            CreditCard object or None if not found
        """
        if self._cards_df is None:
            self.load_credit_card_data()

        card_row = self._cards_df[self._cards_df['card_id'] == card_id]

        if card_row.empty:
            return None

        row = card_row.iloc[0]
        return CreditCard(
            card_id=row['card_id'],
            name=row['Card Name'],
            issuer=row['Issuer'],
            card_type=row['Card Type']
        )

    def get_all_cards(self) -> List[CreditCard]:
        """
        Get all available cards

        Returns:
            List of CreditCard objects
        """
        if self._cards_df is None:
            self.load_credit_card_data()

        cards = []
        for _, row in self._cards_df.iterrows():
            cards.append(CreditCard(
                card_id=row['card_id'],
                name=row['Card Name'],
                issuer=row['Issuer'],
                card_type=row['Card Type']
            ))

        return cards


# Global data loader instance
@st.cache_resource
def get_data_loader() -> DataLoader:
    """Get cached data loader instance"""
    return DataLoader()
