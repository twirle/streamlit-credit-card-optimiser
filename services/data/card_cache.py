"""
Card Data Cache

This module handles caching of credit card data for improved performance.
"""

import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd


class CardDataCache:
    """Manages caching of credit card data for improved performance"""

    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_cached_card_data() -> Dict[str, pd.DataFrame]:
        """
        Get cached credit card data
        
        Returns:
            Dictionary containing cached DataFrames
        """
        from .card_loader import CardLoader
        
        loader = CardLoader()
        available_cards, card_tiers, reward_rates, card_categories = loader.load_all_card_data()
        
        return {
            'available_cards': available_cards,
            'card_tiers': card_tiers,
            'reward_rates': reward_rates,
            'card_categories': card_categories
        }

    @staticmethod
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def get_cached_cards_by_type(card_type: str) -> pd.DataFrame:
        """
        Get cached cards filtered by type
        
        Args:
            card_type: Type of cards to filter ('Miles' or 'Cashback')
            
        Returns:
            DataFrame of filtered cards
        """
        from .card_loader import CardLoader
        
        loader = CardLoader()
        return loader.get_cards_by_type(card_type)

    @staticmethod
    @st.cache_data(ttl=1800)  # Cache for 30 minutes
    def get_cached_card_categories(card_id: int) -> list:
        """
        Get cached card categories
        
        Args:
            card_id: ID of the card
            
        Returns:
            List of category names
        """
        from .card_loader import CardLoader
        
        loader = CardLoader()
        return loader.get_card_categories(card_id)

    @staticmethod
    def clear_cache():
        """Clear all cached card data"""
        st.cache_data.clear() 