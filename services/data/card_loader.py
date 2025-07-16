"""
Card Data Loader

This module handles loading and processing of credit card data
from CSV files with improved naming and structure.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import streamlit as st

from models.credit_card_model import (
    CreditCard, CardTier, CategoryRate, CardCategory
)


@st.cache_data(ttl=3600, max_entries=10)  # Cache for 1 hour
def _load_card_data_cached(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Cached function to load credit card data from CSV files
    
    Args:
        data_dir: Directory containing the CSV files
        
    Returns:
        Tuple of (available_cards, card_tiers, reward_rates, card_categories)
    """
    data_path = Path(data_dir)
    
    try:
        # Load all CSV files with optimized data types
        available_cards = pd.read_csv(
            data_path / "cards.csv",
            dtype={
                'card_id': 'int32',
                'name': 'string',
                'card_type': 'category',
                'issuer': 'category'
            }
        )
        
        card_tiers = pd.read_csv(
            data_path / "card_tiers.csv",
            dtype={
                'tier_id': 'int32',
                'card_id': 'int32',
                'min_spend': 'float32',
                'description': 'string'
            }
        )
        
        reward_rates = pd.read_csv(
            data_path / "category_rates.csv",
            dtype={
                'tier_id': 'int32',
                'category': 'category',
                'rate_value': 'float32',
                'rate_type': 'category',
                'cap_amount': 'float32',
                'cap_type': 'category'
            }
        )
        
        card_categories = pd.read_csv(
            data_path / "card_categories.csv",
            dtype={
                'card_id': 'int32',
                'category': 'category'
            }
        )

        # Rename columns to Title Case for consistency across the app
        available_cards = available_cards.rename(columns={
            'name': 'Card Name',
            'card_type': 'Card Type',
            'issuer': 'Issuer'
        })
        
        card_tiers = card_tiers.rename(columns={
            'min_spend': 'Min Spend',
            'description': 'Description'
        })
        
        reward_rates = reward_rates.rename(columns={
            'rate_value': 'Rate Value',
            'rate_type': 'Rate Type',
            'cap_amount': 'Cap Amount',
            'cap_type': 'Cap Type'
        })

        return available_cards, card_tiers, reward_rates, card_categories

    except FileNotFoundError as e:
        st.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        st.error(f"Error loading credit card data: {e}")
        raise


@st.cache_data(ttl=1800, max_entries=50)  # Cache for 30 minutes
def _build_lookup_tables_cached(available_cards: pd.DataFrame, card_categories: pd.DataFrame, 
                               card_tiers: pd.DataFrame, reward_rates: pd.DataFrame) -> Dict:
    """
    Cached function to build lookup tables
    
    Args:
        available_cards: DataFrame with card information
        card_categories: DataFrame with card categories
        card_tiers: DataFrame with card tiers
        reward_rates: DataFrame with reward rates
        
    Returns:
        Dictionary of lookup tables
    """
    # Build card name to ID lookup
    card_name_to_id = dict(zip(available_cards['Card Name'], available_cards['card_id']))
    
    # Build card ID to info lookup
    card_id_to_info = {}
    for _, row in available_cards.iterrows():
        card_id_to_info[row['card_id']] = {
            'name': row['Card Name'],
            'type': row['Card Type'],
            'issuer': row['Issuer']
        }

    # Build card ID to categories lookup (convert lists to tuples for hashability)
    card_id_to_categories = {}
    for _, row in card_categories.iterrows():
        card_id = row['card_id']
        if card_id not in card_id_to_categories:
            card_id_to_categories[card_id] = []
        card_id_to_categories[card_id].append(row['category'])
    
    # Convert lists to tuples for hashability
    card_id_to_categories = {k: tuple(v) for k, v in card_id_to_categories.items()}

    # Build card ID to tiers lookup (convert lists to tuples for hashability)
    card_id_to_tiers = {}
    for _, row in card_tiers.iterrows():
        card_id = row['card_id']
        if card_id not in card_id_to_tiers:
            card_id_to_tiers[card_id] = []
        card_id_to_tiers[card_id].append({
            'tier_id': int(row['tier_id']),
            'description': str(row['Description']),
            'min_spend': float(row['Min Spend'])
        })
    
    # Convert lists to tuples for hashability
    card_id_to_tiers = {k: tuple(v) for k, v in card_id_to_tiers.items()}

    # Build tier ID to rates lookup (convert lists to tuples for hashability)
    tier_id_to_rates = {}
    for _, row in reward_rates.iterrows():
        tier_id = row['tier_id']
        if tier_id not in tier_id_to_rates:
            tier_id_to_rates[tier_id] = []
        cap_amount = row['Cap Amount']
        cap_type = row['Cap Type']
        
        tier_id_to_rates[tier_id].append({
            'category': str(row['category']),
            'rate_value': float(row['Rate Value']),
            'rate_type': str(row['Rate Type']),
            'cap_amount': float(cap_amount) if cap_amount is not None and str(cap_amount) != 'nan' else None,
            'cap_type': str(cap_type) if cap_type is not None and str(cap_type) != 'nan' else None
        })
    
    # Convert lists to tuples for hashability
    tier_id_to_rates = {k: tuple(v) for k, v in tier_id_to_rates.items()}

    return {
        'card_name_to_id': card_name_to_id,
        'card_id_to_info': card_id_to_info,
        'card_id_to_categories': card_id_to_categories,
        'card_id_to_tiers': card_id_to_tiers,
        'tier_id_to_rates': tier_id_to_rates
    }


class CardLoader:
    """Service for loading and managing credit card data with improved naming"""

    def __init__(self, data_dir: str = "cardData"):
        self.data_dir = Path(data_dir)
        self._available_cards = None
        self._card_tiers = None
        self._reward_rates = None
        self._card_categories = None
        self._lookup_tables = None

    def load_all_card_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load normalized credit card data from CSV files with improved naming and optimized dtypes

        Returns:
            Tuple of (available_cards, card_tiers, reward_rates, card_categories)
        """
        # Use cached function for data loading
        available_cards, card_tiers, reward_rates, card_categories = _load_card_data_cached(str(self.data_dir))

        # Store for caching
        self._available_cards = available_cards
        self._card_tiers = card_tiers
        self._reward_rates = reward_rates
        self._card_categories = card_categories

        return available_cards, card_tiers, reward_rates, card_categories

    def build_lookup_tables(self) -> Dict:
        """
        Build optimized lookup tables for faster data access
        
        Returns:
            Dictionary of lookup tables
        """
        # Ensure data is loaded
        if self._available_cards is None:
            self.load_all_card_data()

        # Ensure all data is available
        if (self._available_cards is None or self._card_categories is None or 
            self._card_tiers is None or self._reward_rates is None):
            raise ValueError("Failed to load card data")

        return _build_lookup_tables_cached(self._available_cards, self._card_categories, self._card_tiers, self._reward_rates)

    def get_cards_by_type(self, card_type: str) -> pd.DataFrame:
        """
        Get cards filtered by type (Miles or Cashback)

        Args:
            card_type: Type of cards to filter ('Miles' or 'Cashback')

        Returns:
            DataFrame of filtered cards
        """
        if self._available_cards is None:
            self.load_all_card_data()

        filtered_cards = self._available_cards.query(
            '`Card Type` == @card_type')
        return filtered_cards if isinstance(filtered_cards, pd.DataFrame) else pd.DataFrame([filtered_cards])

    def get_card_tiers(self, card_id: int) -> pd.DataFrame:
        """
        Get all tiers for a specific card

        Args:
            card_id: ID of the card

        Returns:
            DataFrame of card tiers
        """
        if self._card_tiers is None:
            self.load_all_card_data()

        filtered_tiers = self._card_tiers.query('card_id == @card_id')
        return filtered_tiers if isinstance(filtered_tiers, pd.DataFrame) else pd.DataFrame([filtered_tiers])

    def get_reward_rates(self, tier_id: int) -> pd.DataFrame:
        """
        Get all category rates for a specific tier

        Args:
            tier_id: ID of the tier

        Returns:
            DataFrame of category rates
        """
        if self._reward_rates is None:
            self.load_all_card_data()

        filtered_rates = self._reward_rates.query('tier_id == @tier_id')
        return filtered_rates if isinstance(filtered_rates, pd.DataFrame) else pd.DataFrame([filtered_rates])

    def get_card_categories(self, card_id: int) -> List[str]:
        """
        Get all categories supported by a card

        Args:
            card_id: ID of the card

        Returns:
            List of category names
        """
        if self._card_categories is None:
            self.load_all_card_data()

        categories = self._card_categories.query(
            'card_id == @card_id')['category'].tolist()
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
        suitable_tiers = tiers.query('`Min Spend` <= @total_spending')

        if suitable_tiers.empty:
            return None

        # Get the tier with highest min_spend (best tier)
        max_min_spend = suitable_tiers['Min Spend'].max()
        best_tier_row = suitable_tiers.query(
            '`Min Spend` == @max_min_spend').iloc[0]

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
        if self._available_cards is None:
            self.load_all_card_data()

        card_row = self._available_cards.query('card_id == @card_id')

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
        if self._available_cards is None:
            self.load_all_card_data()

        cards = []
        for _, row in self._available_cards.iterrows():
            cards.append(CreditCard(
                card_id=row['card_id'],
                name=row['Card Name'],
                issuer=row['Issuer'],
                card_type=row['Card Type']
            ))

        return cards

    def get_cards_for_display(self) -> pd.DataFrame:
        """
        Get cards data formatted for display in tables

        Returns:
            DataFrame with cards sorted by type, issuer, and name
        """
        if self._available_cards is None:
            self.load_all_card_data()

        # Create a copy for display with proper sorting
        display_df = self._available_cards.copy()
        display_df = display_df.sort_values(
            ['Card Type', 'Issuer', 'Card Name'])

        return display_df


# Global card loader instance
@st.cache_resource
def get_card_loader() -> CardLoader:
    """Get cached card loader instance"""
    return CardLoader("cardData")
