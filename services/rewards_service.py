"""
Main Rewards Service

This module provides a unified interface for all reward calculation functionality,
combining single card calculations, UOB Lady's optimization, and multi-card combinations.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
import streamlit as st

from models.credit_card_model import UserSpending, RewardCalculation
from .rewards.calculator import get_reward_calculator
from .rewards.uob_ladys_optimizer import get_uob_ladys_optimizer
from .rewards.combination_optimizer import get_combination_optimizer


@st.cache_data(ttl=900, max_entries=100)  # Cache for 15 minutes
def _calculate_single_card_reward_cached(card_id: int, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> RewardCalculation:
    """
    Cached function to calculate rewards for a single card
    
    Args:
        card_id: ID of the card
        spending: User spending data
        miles_to_sgd_rate: Conversion rate from miles to SGD
        
    Returns:
        RewardCalculation object with results
    """
    # Special handling for UOB Lady's card
    if card_id == 15:  # UOB Lady's card ID
        uob_optimizer = get_uob_ladys_optimizer()
        return uob_optimizer.calculate_uob_ladys_rewards(card_id, spending, miles_to_sgd_rate)

    # Use standard calculator for other cards
    calculator = get_reward_calculator()
    return calculator.calculate_card_rewards(card_id, spending, miles_to_sgd_rate)


@st.cache_data(ttl=600, max_entries=200)  # Cache for 10 minutes
def _calculate_filtered_cards_rewards_cached(selected_cards_df: pd.DataFrame, spending: UserSpending, 
                                           miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
    """
    Cached function to calculate rewards for filtered cards with optimized performance
    
    Args:
        selected_cards_df: DataFrame of selected cards
        spending: User spending data
        miles_to_sgd_rate: Conversion rate from miles to SGD
        
    Returns:
        List of RewardCalculation objects
    """
    results = []

    # Get lookup tables for faster card name to ID conversion
    from services.data.card_loader import get_card_loader
    card_loader = get_card_loader()
    lookup_tables = card_loader.build_lookup_tables()
    card_name_to_id = lookup_tables['card_name_to_id']

    # Process cards in batches for better performance
    batch_size = 10
    for i in range(0, len(selected_cards_df), batch_size):
        batch = selected_cards_df.iloc[i:i+batch_size]
        
        for _, card_row in batch.iterrows():
            try:
                card_name = str(card_row['Card Name'])
                card_id = card_name_to_id.get(card_name)

                if card_id is not None:
                    result = _calculate_single_card_reward_cached(
                        card_id, spending, miles_to_sgd_rate)
                    results.append(result)
            except Exception as e:
                print(
                    f"Error calculating rewards for card {card_row['Card Name']}: {e}")
                continue

    return results


@st.cache_data(ttl=300, max_entries=50)  # Cache for 5 minutes
def _find_best_card_combinations_cached(filtered_cards_df: pd.DataFrame, user_spending_data: dict,
                                       miles_to_sgd_rate: float, detailed_results_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Cached function to find the best two-card combinations for maximizing rewards
    
    Args:
        filtered_cards_df: DataFrame of available cards
        user_spending_data: User spending data (dict)
        miles_to_sgd_rate: Miles to SGD conversion rate
        detailed_results_df: Detailed results from single card calculations
        
    Returns:
        List of combination results
    """
    combination_optimizer = get_combination_optimizer()
    return combination_optimizer.find_best_combinations(
        filtered_cards_df, user_spending_data, miles_to_sgd_rate, detailed_results_df
    )


@st.cache_data(ttl=300, max_entries=100)  # Cache for 5 minutes
def _combine_two_cards_rewards_cached(card1_data: dict, card2_data: dict,
                                     user_spending_data: dict, miles_to_sgd_rate: float) -> Dict[str, Any]:
    """
    Cached function to calculate rewards for a combination of two cards
    
    Args:
        card1_data: First card data
        card2_data: Second card data
        user_spending_data: User spending data (dict)
        miles_to_sgd_rate: Miles to SGD conversion rate
        
    Returns:
        Dictionary with combination results
    """
    combination_optimizer = get_combination_optimizer()
    return combination_optimizer.combine_two_cards_rewards(
        card1_data, card2_data, user_spending_data, miles_to_sgd_rate
    )


class RewardsService:
    """Main service for all reward calculation functionality"""

    def __init__(self):
        self.calculator = get_reward_calculator()
        self.uob_optimizer = get_uob_ladys_optimizer()
        self.combination_optimizer = get_combination_optimizer()
        self._lookup_tables = None

    @property
    def lookup_tables(self):
        """Get or build lookup tables"""
        if self._lookup_tables is None:
            from services.data.card_loader import get_card_loader
            card_loader = get_card_loader()
            self._lookup_tables = card_loader.build_lookup_tables()
        return self._lookup_tables

    def calculate_single_card_reward(self, card_id: int, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> RewardCalculation:
        """
        Calculate rewards for a single card (with UOB Lady's special handling)

        Args:
            card_id: ID of the card
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD

        Returns:
            RewardCalculation object with results
        """
        return _calculate_single_card_reward_cached(card_id, spending, miles_to_sgd_rate)

    def calculate_filtered_cards_rewards(self, selected_cards_df: pd.DataFrame, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
        """
        Calculate rewards for filtered cards with optimized performance

        Args:
            selected_cards_df: DataFrame of selected cards
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD

        Returns:
            List of RewardCalculation objects
        """
        return _calculate_filtered_cards_rewards_cached(selected_cards_df, spending, miles_to_sgd_rate)

    def get_top_cards_from_results(self, results: List[RewardCalculation], limit: int = 5) -> List[RewardCalculation]:
        """
        Get top performing cards from results

        Args:
            results: List of RewardCalculation objects
            limit: Number of top cards to return

        Returns:
            List of top RewardCalculation objects
        """
        return self.calculator.get_best_cards(results, limit)

    def find_best_card_combinations(self, filtered_cards_df: pd.DataFrame, user_spending_data: dict,
                                    miles_to_sgd_rate: float, detailed_results_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Find the best two-card combinations for maximizing rewards

        Args:
            filtered_cards_df: DataFrame of available cards
            user_spending_data: User spending data (dict)
            miles_to_sgd_rate: Miles to SGD conversion rate
            detailed_results_df: Detailed results from single card calculations

        Returns:
            List of combination results
        """
        return _find_best_card_combinations_cached(filtered_cards_df, user_spending_data, miles_to_sgd_rate, detailed_results_df)

    def combine_two_cards_rewards(self, card1_data: dict, card2_data: dict,
                                  user_spending_data: dict, miles_to_sgd_rate: float) -> Dict[str, Any]:
        """
        Calculate rewards for a combination of two cards

        Args:
            card1_data: First card data
            card2_data: Second card data
            user_spending_data: User spending data (dict)
            miles_to_sgd_rate: Miles to SGD conversion rate

        Returns:
            Dictionary with combination results
        """
        return _combine_two_cards_rewards_cached(card1_data, card2_data, user_spending_data, miles_to_sgd_rate)

    def get_detailed_breakdown(self, card_id: int, spending: UserSpending):
        """
        Get detailed breakdown for a specific card

        Args:
            card_id: ID of the card
            spending: User spending data

        Returns:
            CardRewardBreakdown object
        """
        return self.calculator.get_detailed_breakdown(card_id, spending)


# Global rewards service instance
@st.cache_resource
def get_rewards_service() -> RewardsService:
    """Get cached rewards service instance"""
    return RewardsService()
