"""
Reward Calculation Service

This module handles all credit card reward calculations including
single card calculations and optimal card combinations.
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
import streamlit as st

from models.credit_card_model import (
    UserSpending, RewardCalculation, CardRewardBreakdown,
    CreditCard, CardTier, CategoryRate
)
from services.data_loader import DataLoader, get_data_loader


class RewardCalculator:
    """Service for calculating credit card rewards"""

    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader

    def calculate_single_card_reward(self, card_id: int, spending: UserSpending) -> RewardCalculation:
        """
        Calculate rewards for a single card

        Args:
            card_id: ID of the card
            spending: User spending data

        Returns:
            RewardCalculation object with results
        """
        # Get card info
        card = self.data_loader.get_card_info(card_id)
        if not card:
            raise ValueError(f"Card with ID {card_id} not found")

        # Get best tier for spending
        best_tier = self.data_loader.get_best_tier_for_spending(
            card_id, spending.total)
        if not best_tier:
            return RewardCalculation(
                card_name=card.name,
                tier_description="No suitable tier",
                monthly_reward=0.0,
                cap_reached=False,
                min_spend_met=False,
                details=[f"Minimum spend not met for any tier"]
            )

        # Get category rates for this tier
        rates_df = self.data_loader.get_category_rates(best_tier.tier_id)

        # Calculate rewards by category
        category_rewards = {}
        total_reward = 0.0
        cap_status = {"reached": False, "amount": 0.0, "difference": 0.0}
        details = []

        for _, rate_row in rates_df.iterrows():
            category = rate_row['category']
            rate_value = rate_row['rate_value']
            rate_type = rate_row['rate_type']
            cap_amount = rate_row.get('cap_amount')
            cap_type = rate_row.get('cap_type')

            # Get spending for this category
            category_spending = getattr(spending, category.lower(), 0.0)

            if category_spending > 0:
                # Calculate reward for this category
                if rate_type == 'percentage':
                    reward = (category_spending * rate_value) / 100
                else:  # mpd
                    reward = category_spending * rate_value

                # Apply cap if applicable
                if cap_amount and cap_type:
                    if cap_type == 'dollars_earned':
                        # Cap is on dollars earned (for cashback)
                        if reward > cap_amount:
                            reward = cap_amount
                            cap_status["reached"] = True
                            cap_status["amount"] = cap_amount
                            cap_status["difference"] = reward - cap_amount
                    else:  # dollars_spent
                        # Cap is on dollars spent (for miles)
                        if category_spending > cap_amount:
                            capped_spending = cap_amount
                            if rate_type == 'percentage':
                                reward = (capped_spending * rate_value) / 100
                            else:
                                reward = capped_spending * rate_value
                            cap_status["reached"] = True
                            cap_status["amount"] = cap_amount
                            cap_status["difference"] = category_spending - \
                                cap_amount

                category_rewards[category] = reward
                total_reward += reward

                details.append(
                    f"{category}: ${category_spending:.2f} × {rate_value}{'%' if rate_type == 'percentage' else ' mpd'} = ${reward:.2f}")

        return RewardCalculation(
            card_name=card.name,
            tier_description=best_tier.description,
            monthly_reward=total_reward,
            cap_reached=cap_status["reached"],
            cap_difference=cap_status["difference"] if cap_status["reached"] else None,
            min_spend_met=True,
            details=details
        )

    def calculate_all_cards_rewards(self, spending: UserSpending) -> List[RewardCalculation]:
        """
        Calculate rewards for all available cards

        Args:
            spending: User spending data

        Returns:
            List of RewardCalculation objects
        """
        all_cards = self.data_loader.get_all_cards()
        results = []

        for card in all_cards:
            try:
                result = self.calculate_single_card_reward(
                    card.card_id, spending)
                results.append(result)
            except Exception as e:
                st.warning(f"Error calculating rewards for {card.name}: {e}")
                continue

        return results

    def get_top_cards(self, spending: UserSpending, limit: int = 5) -> List[RewardCalculation]:
        """
        Get top performing cards based on rewards

        Args:
            spending: User spending data
            limit: Number of top cards to return

        Returns:
            List of top RewardCalculation objects
        """
        all_results = self.calculate_all_cards_rewards(spending)

        # Sort by monthly reward (descending)
        sorted_results = sorted(
            all_results, key=lambda x: x.monthly_reward, reverse=True)

        return sorted_results[:limit]

    def calculate_card_combination_reward(self, card_ids: List[int], spending: UserSpending) -> Dict[str, any]:
        """
        Calculate rewards for a combination of cards

        Args:
            card_ids: List of card IDs to combine
            spending: User spending data

        Returns:
            Dictionary with combination results
        """
        if not card_ids:
            return {
                "total_reward": 0.0,
                "card_rewards": [],
                "details": []
            }

        card_rewards = []
        total_reward = 0.0
        details = []

        for card_id in card_ids:
            try:
                result = self.calculate_single_card_reward(card_id, spending)
                card_rewards.append(result)
                total_reward += result.monthly_reward
                if result.details:
                    details.extend(result.details)
            except Exception as e:
                st.warning(
                    f"Error calculating rewards for card {card_id}: {e}")
                continue

        return {
            "total_reward": total_reward,
            "card_rewards": card_rewards,
            "details": details
        }

    def get_optimal_combination(self, spending: UserSpending, max_cards: int = 3) -> Dict[str, any]:
        """
        Find optimal combination of cards for maximum rewards

        Args:
            spending: User spending data
            max_cards: Maximum number of cards to consider

        Returns:
            Dictionary with optimal combination results
        """
        all_cards = self.data_loader.get_all_cards()

        if len(all_cards) <= max_cards:
            # If we have fewer cards than max, just return all
            card_ids = [card.card_id for card in all_cards]
            return self.calculate_card_combination_reward(card_ids, spending)

        # For now, return top performing single cards
        # TODO: Implement more sophisticated combination logic
        top_cards = self.get_top_cards(spending, max_cards)
        card_ids = []

        for result in top_cards:
            # Find card ID from card name (this is a temporary solution)
            for card in all_cards:
                if card.name == result.card_name:
                    card_ids.append(card.card_id)
                    break

        return self.calculate_card_combination_reward(card_ids, spending)

    def get_detailed_breakdown(self, card_id: int, spending: UserSpending) -> CardRewardBreakdown:
        """
        Get detailed breakdown of rewards for a specific card

        Args:
            card_id: ID of the card
            spending: User spending data

        Returns:
            CardRewardBreakdown object
        """
        card = self.data_loader.get_card_info(card_id)
        if not card:
            raise ValueError(f"Card with ID {card_id} not found")

        best_tier = self.data_loader.get_best_tier_for_spending(
            card_id, spending.total)
        if not best_tier:
            return CardRewardBreakdown(
                card_id=card_id,
                card_name=card.name,
                tier_id=0,
                tier_description="No suitable tier",
                category_rewards={},
                total_reward=0.0,
                cap_status={"reached": False,
                            "amount": 0.0, "difference": 0.0},
                min_spend_met=False
            )

        rates_df = self.data_loader.get_category_rates(best_tier.tier_id)
        category_rewards = {}
        total_reward = 0.0
        cap_status = {"reached": False, "amount": 0.0, "difference": 0.0}

        for _, rate_row in rates_df.iterrows():
            category = rate_row['category']
            rate_value = rate_row['rate_value']
            rate_type = rate_row['rate_type']
            cap_amount = rate_row.get('cap_amount')
            cap_type = rate_row.get('cap_type')

            category_spending = getattr(spending, category.lower(), 0.0)

            if category_spending > 0:
                if rate_type == 'percentage':
                    reward = (category_spending * rate_value) / 100
                else:
                    reward = category_spending * rate_value

                if cap_amount and cap_type:
                    if cap_type == 'dollars_earned' and reward > cap_amount:
                        reward = cap_amount
                        cap_status["reached"] = True
                        cap_status["amount"] = cap_amount
                        cap_status["difference"] = reward - cap_amount
                    elif cap_type == 'dollars_spent' and category_spending > cap_amount:
                        capped_spending = cap_amount
                        if rate_type == 'percentage':
                            reward = (capped_spending * rate_value) / 100
                        else:
                            reward = capped_spending * rate_value
                        cap_status["reached"] = True
                        cap_status["amount"] = cap_amount
                        cap_status["difference"] = category_spending - \
                            cap_amount

                category_rewards[category] = reward
                total_reward += reward

        return CardRewardBreakdown(
            card_id=card_id,
            card_name=card.name,
            tier_id=best_tier.tier_id,
            tier_description=best_tier.description,
            category_rewards=category_rewards,
            total_reward=total_reward,
            cap_status=cap_status,
            min_spend_met=True
        )


# Global calculator instance
@st.cache_resource
def get_reward_calculator() -> RewardCalculator:
    """Get cached reward calculator instance"""
    data_loader = get_data_loader()
    return RewardCalculator(data_loader)


def find_best_card_combinations(filtered_cards_df, user_spending_data, miles_to_sgd_rate, detailed_results_df):
    """
    Find the best two-card combinations for maximizing rewards

    Args:
        filtered_cards_df: DataFrame of available cards
        user_spending_data: User spending data
        miles_to_sgd_rate: Miles to SGD conversion rate
        detailed_results_df: Detailed results from single card calculations

    Returns:
        List of combination results
    """
    combinations = []

    # Get top performing cards for combinations
    top_cards = filtered_cards_df.head(10)  # Consider top 10 cards

    for i, card1 in top_cards.iterrows():
        for j, card2 in top_cards.iterrows():
            if i >= j:  # Avoid duplicate combinations
                continue

            # Create combination name
            combination_name = f"{card1['Name']} + {card2['Name']}"

            # Calculate combined rewards
            combined_result = combine_two_cards_rewards(
                card1, card2, user_spending_data, miles_to_sgd_rate
            )

            if combined_result['total_reward'] > 0:
                combinations.append({
                    'Card Name': combination_name,
                    'Issuer': f"{card1['Issuer']} + {card2['Issuer']}",
                    'Categories': combined_result.get('categories', ''),
                    'Monthly Reward': combined_result['total_reward'],
                    'Card1': card1['Name'],
                    'Card2': card2['Name']
                })

    # Sort by monthly reward (descending)
    combinations.sort(key=lambda x: x['Monthly Reward'], reverse=True)

    return combinations[:10]  # Return top 10 combinations


def combine_two_cards_rewards(card1_data, card2_data, user_spending_data, miles_to_sgd_rate):
    """
    Calculate rewards for a combination of two cards

    Args:
        card1_data: First card data
        card2_data: Second card data
        user_spending_data: User spending data
        miles_to_sgd_rate: Miles to SGD conversion rate

    Returns:
        Dictionary with combination results
    """
    # Get calculator instance
    calculator = get_reward_calculator()

    # Find card IDs by name
    data_loader = get_data_loader()
    all_cards = data_loader.get_all_cards()

    card1_id = None
    card2_id = None

    for card in all_cards:
        if card.name == card1_data['Name']:
            card1_id = card.card_id
        if card.name == card2_data['Name']:
            card2_id = card.card_id

    if card1_id is None or card2_id is None:
        return {
            'total_reward': 0.0,
            'allocation': {},
            'categories': '',
            'details': []
        }

    # Calculate individual card rewards
    card1_result = calculator.calculate_single_card_reward(
        card1_id, user_spending_data)
    card2_result = calculator.calculate_single_card_reward(
        card2_id, user_spending_data)

    # Simple combination: sum the rewards
    total_reward = card1_result.monthly_reward + card2_result.monthly_reward

    # Get categories for both cards
    card1_categories = data_loader.get_card_categories(card1_id)
    card2_categories = data_loader.get_card_categories(card2_id)
    all_categories = list(set(card1_categories + card2_categories))

    # Create allocation data (simplified - equal split for now)
    allocation = {
        card1_data['Name']: {
            'reward': card1_result.monthly_reward,
            'categories': card1_categories,
            'details': card1_result.details or []
        },
        card2_data['Name']: {
            'reward': card2_result.monthly_reward,
            'categories': card2_categories,
            'details': card2_result.details or []
        }
    }

    return {
        'total_reward': total_reward,
        'allocation': allocation,
        'categories': ', '.join(all_categories),
        'details': (card1_result.details or []) + (card2_result.details or [])
    }
