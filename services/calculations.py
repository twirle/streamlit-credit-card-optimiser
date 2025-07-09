"""
Reward Calculation Service

This module handles all credit card reward calculations including
single card calculations and optimal card combinations.
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
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

    def find_most_efficient_category_for_uob_ladys(self, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> str:
        """
        Find the most efficient category for UOB Lady's card based on spending and potential reward
        
        Args:
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD
            
        Returns:
            Category name that would provide the highest reward
        """
        # UOB Lady's eligible categories (4mpd categories)
        eligible_categories = ['Dining', 'Transport', 'Entertainment', 'Retail', 'Travel']
        
        best_category = 'Other'  # Default fallback
        best_reward = 0.0
        
        for category in eligible_categories:
            category_spending = getattr(spending, category.lower(), 0.0)
            if category_spending > 0:
                # Calculate potential reward: 4mpd for this category
                miles_earned = category_spending * 4.0
                potential_reward = miles_earned * miles_to_sgd_rate
                
                if potential_reward > best_reward:
                    best_reward = potential_reward
                    best_category = category
        
        return best_category

    def calculate_uob_ladys_reward_with_optimization(self, card_id: int, spending: UserSpending, 
                                                   miles_to_sgd_rate: float = 0.02, 
                                                   selected_category: Optional[str] = None) -> RewardCalculation:
        """
        Calculate rewards for UOB Lady's card with intelligent category selection
        
        Args:
            card_id: ID of the UOB Lady's card
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD
            selected_category: Optional category to use (for multi-card optimization)
            
        Returns:
            RewardCalculation object with results
        """
        # Get card info
        card = self.data_loader.get_card_info(card_id)
        if not card:
            raise ValueError(f"Card with ID {card_id} not found")

        # Get best tier for spending
        best_tier = self.data_loader.get_best_tier_for_spending(card_id, spending.total)
        if not best_tier:
            return RewardCalculation(
                card_name=card.name,
                tier_description="No suitable tier",
                monthly_reward=0.0,
                cap_reached=False,
                min_spend_met=False,
                details=[f"Minimum spend not met for any tier"]
            )

        # Determine the optimal category if not provided
        if selected_category is None:
            selected_category = self.find_most_efficient_category_for_uob_ladys(spending, miles_to_sgd_rate)

        # Calculate rewards with the selected category getting 4mpd, others getting 0.4mpd
        total_reward = 0.0
        cap_status = {"reached": False, "amount": 0.0, "difference": 0.0}
        details = []
        original_reward = 0.0

        # Get all categories that UOB Lady's supports
        card_categories = self.data_loader.get_card_categories(card_id)
        
        for category in card_categories:
            category_spending = getattr(spending, category.lower(), 0.0)
            
            if category_spending > 0:
                # Determine rate based on whether this is the selected category
                if category == selected_category:
                    rate_value = 4.0  # 4mpd for selected category
                else:
                    rate_value = 0.4  # 0.4mpd for other categories
                
                # Calculate reward
                miles_earned = category_spending * rate_value
                reward = miles_earned * miles_to_sgd_rate
                original_reward += reward
                
                # Apply cap (UOB Lady's has $1000 cap on spending)
                cap_amount = 1000.0
                if category_spending > cap_amount:
                    capped_spending = cap_amount
                    miles_earned = capped_spending * rate_value
                    reward = miles_earned * miles_to_sgd_rate
                    cap_status["reached"] = True
                    cap_status["amount"] = cap_amount
                    cap_status["difference"] = category_spending - cap_amount
                
                total_reward += reward
                
                # Add to details
                details.append(
                    f"{category}: ${category_spending:.2f} × {rate_value} mpd = {miles_earned:.0f} miles × ${miles_to_sgd_rate:.3f} = ${reward:.2f}"
                )

        return RewardCalculation(
            card_name=card.name,
            tier_description=f"{best_tier.description} (Selected: {selected_category})",
            monthly_reward=total_reward,
            cap_reached=cap_status["reached"],
            cap_difference=cap_status["difference"] if cap_status["reached"] else None,
            original_reward=original_reward,
            min_spend_met=True,
            details=details
        )

    def calculate_single_card_reward(self, card_id: int, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> RewardCalculation:
        """
        Calculate rewards for a single card

        Args:
            card_id: ID of the card
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD (default 0.02)

        Returns:
            RewardCalculation object with results
        """
        # Special handling for UOB Lady's card
        if card_id == 15:  # UOB Lady's card ID
            return self.calculate_uob_ladys_reward_with_optimization(card_id, spending, miles_to_sgd_rate)

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
        original_reward = 0.0

        # Check if there is an 'All' category
        all_row = rates_df[rates_df['category'].str.lower() == 'all']
        if not all_row.empty:
            # Use the first 'All' row (should only be one)
            rate_row = all_row.iloc[0]
            rate_value = float(rate_row['Rate Value'])
            rate_type = str(rate_row['Rate Type'])
            cap_amount = rate_row.get('Cap Amount')
            cap_type = rate_row.get('Cap Type')
            # Sum all spending categories except 'total'
            all_spending = sum([v for k, v in spending.to_dict().items() if k != 'total'])
            if all_spending > 0:
                if rate_type == 'percentage':
                    reward = (all_spending * rate_value) / 100
                else:
                    miles_earned = all_spending * rate_value
                    reward = miles_earned * miles_to_sgd_rate
                original_reward += reward
                # Apply cap if applicable
                if cap_amount and cap_type:
                    if cap_type == 'dollars_earned':
                        if reward > cap_amount:
                            reward = cap_amount
                            cap_status["reached"] = True
                            cap_status["amount"] = cap_amount
                            cap_status["difference"] = reward - cap_amount
                    else:
                        if all_spending > cap_amount:
                            capped_spending = cap_amount
                            if rate_type == 'percentage':
                                reward = (capped_spending * rate_value) / 100
                            else:
                                miles_earned = capped_spending * rate_value
                                reward = miles_earned * miles_to_sgd_rate
                            cap_status["reached"] = True
                            cap_status["amount"] = cap_amount
                            cap_status["difference"] = all_spending - cap_amount
                category_rewards['All'] = reward
                total_reward += reward
                if rate_type == 'percentage':
                    details.append(f"All: ${all_spending:.2f} × {rate_value}% = ${reward:.2f}")
                else:
                    miles_earned = all_spending * rate_value
                    details.append(f"All: ${all_spending:.2f} × {rate_value} mpd = {miles_earned:.0f} miles × ${miles_to_sgd_rate:.3f} = ${reward:.2f}")
        else:
            # Normal per-category logic
            for _, rate_row in rates_df.iterrows():
                category = str(rate_row['category'])
                rate_value = float(rate_row['Rate Value'])
                rate_type = str(rate_row['Rate Type'])
                cap_amount = rate_row.get('Cap Amount')
                cap_type = rate_row.get('Cap Type')

                # Get spending for this category
                category_spending = getattr(spending, category.lower(), 0.0)

                if category_spending > 0:
                    # Calculate reward for this category
                    if rate_type == 'percentage':
                        reward = (category_spending * rate_value) / 100
                    else:  # mpd
                        miles_earned = category_spending * rate_value
                        reward = miles_earned * miles_to_sgd_rate

                    original_reward += reward

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
                                    miles_earned = capped_spending * rate_value
                                    reward = miles_earned * miles_to_sgd_rate
                                cap_status["reached"] = True
                                cap_status["amount"] = cap_amount
                                cap_status["difference"] = category_spending - \
                                    cap_amount

                    category_rewards[category] = reward
                    total_reward += reward

                    if rate_type == 'percentage':
                        details.append(
                            f"{category}: ${category_spending:.2f} × {rate_value}% = ${reward:.2f}")
                    else:  # mpd
                        miles_earned = category_spending * rate_value
                        details.append(
                            f"{category}: ${category_spending:.2f} × {rate_value} mpd = {miles_earned:.0f} miles × ${miles_to_sgd_rate:.3f} = ${reward:.2f}")

        return RewardCalculation(
            card_name=card.name,
            tier_description=best_tier.description,
            monthly_reward=total_reward,
            cap_reached=cap_status["reached"],
            cap_difference=cap_status["difference"] if cap_status["reached"] else None,
            original_reward=original_reward,
            min_spend_met=True,
            details=details
        )

    def calculate_all_cards_rewards(self, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
        """
        Calculate rewards for all available cards

        Args:
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD (default 0.02)

        Returns:
            List of RewardCalculation objects
        """
        all_cards = self.data_loader.get_all_cards()
        results = []

        for card in all_cards:
            try:
                result = self.calculate_single_card_reward(
                    card.card_id, spending, miles_to_sgd_rate)
                results.append(result)
            except Exception as e:
                st.warning(f"Error calculating rewards for {card.name}: {e}")
                continue

        return results

    def get_top_cards(self, spending: UserSpending, limit: int = 5, miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
        """
        Get top performing cards based on rewards

        Args:
            spending: User spending data
            limit: Number of top cards to return
            miles_to_sgd_rate: Conversion rate from miles to SGD (default 0.02)

        Returns:
            List of top RewardCalculation objects
        """
        all_results = self.calculate_all_cards_rewards(spending, miles_to_sgd_rate)

        # Sort by monthly reward (descending)
        sorted_results = sorted(
            all_results, key=lambda x: x.monthly_reward, reverse=True)

        return sorted_results[:limit]

    def calculate_filtered_cards_rewards(self, filtered_cards_df, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
        """
        Calculate rewards for filtered cards only

        Args:
            filtered_cards_df: DataFrame of filtered cards
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD (default 0.02)

        Returns:
            List of RewardCalculation objects for filtered cards
        """
        results = []

        for _, card_row in filtered_cards_df.iterrows():
            try:
                card_id = int(card_row['card_id'])
                result = self.calculate_single_card_reward(
                    card_id, spending, miles_to_sgd_rate)
                results.append(result)
            except Exception as e:
                st.warning(f"Error calculating rewards for {card_row['Card Name']}: {e}")
                continue

        return results

    def get_top_cards_from_results(self, results: List[RewardCalculation], limit: int = 5) -> List[RewardCalculation]:
        """
        Get top performing cards from existing results

        Args:
            results: List of RewardCalculation objects
            limit: Number of top cards to return

        Returns:
            List of top RewardCalculation objects
        """
        # Sort by monthly reward (descending)
        sorted_results = sorted(
            results, key=lambda x: x.monthly_reward, reverse=True)

        return sorted_results[:limit]

    def calculate_card_combination_reward(self, card_ids: List[int], spending: UserSpending) -> Dict[str, Any]:
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

    def get_optimal_combination(self, spending: UserSpending, max_cards: int = 3) -> Dict[str, Any]:
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
            category = str(rate_row['category'])
            rate_value = float(rate_row['Rate Value'])
            rate_type = str(rate_row['Rate Type'])
            cap_amount = rate_row.get('Cap Amount')
            cap_type = rate_row.get('Cap Type')

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
                            miles_earned = capped_spending * rate_value
                            reward = miles_earned * rate_value
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

    # Use all available cards for combinations (no limit)
    all_cards = filtered_cards_df

    for i, card1 in all_cards.iterrows():
        for j, card2 in all_cards.iterrows():
            if i >= j:  # Avoid duplicate combinations
                continue

            # Create combination name
            combination_name = f"{card1['Card Name']} + {card2['Card Name']}"

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
                    'Card1': card1['Card Name'],
                    'Card2': card2['Card Name']
                })

    # Sort by monthly reward (descending)
    combinations.sort(key=lambda x: x['Monthly Reward'], reverse=True)

    return combinations  # Return all combinations (no limit)


def combine_two_cards_rewards(card1_data, card2_data, user_spending_data, miles_to_sgd_rate):
    """
    Calculate rewards for a combination of two cards with intelligent optimization for UOB Lady's card

    Args:
        card1_data: First card data
        card2_data: Second card data
        user_spending_data: User spending data (dict)
        miles_to_sgd_rate: Miles to SGD conversion rate

    Returns:
        Dictionary with combination results
    """
    # Get calculator instance
    calculator = get_reward_calculator()

    # Convert user_spending_data dict to UserSpending object
    from models.credit_card_model import UserSpending
    spending_model = UserSpending(
        dining=user_spending_data.get('dining', 0.0),
        groceries=user_spending_data.get('groceries', 0.0),
        petrol=user_spending_data.get('petrol', 0.0),
        transport=user_spending_data.get('transport', 0.0),
        streaming=user_spending_data.get('streaming', 0.0),
        entertainment=user_spending_data.get('entertainment', 0.0),
        utilities=user_spending_data.get('utilities', 0.0),
        online=user_spending_data.get('online', 0.0),
        travel=user_spending_data.get('travel', 0.0),
        overseas=user_spending_data.get('overseas', 0.0),
        retail=user_spending_data.get('retail', 0.0),
        departmental=user_spending_data.get('departmental', 0.0),
        other=user_spending_data.get('other', 0.0)
    )

    # Find card IDs by name
    data_loader = get_data_loader()
    all_cards = data_loader.get_all_cards()

    card1_id = None
    card2_id = None

    for card in all_cards:
        if card.name == card1_data['Card Name']:
            card1_id = card.card_id
        if card.name == card2_data['Card Name']:
            card2_id = card.card_id

    if card1_id is None or card2_id is None:
        return {
            'total_reward': 0.0,
            'allocation': {},
            'categories': '',
            'details': []
        }

    # Check if either card is UOB Lady's (card_id 15)
    is_uob_ladys_card1 = card1_id == 15
    is_uob_ladys_card2 = card2_id == 15

    # Calculate individual card rewards
    if is_uob_ladys_card1:
        # For UOB Lady's, we need to optimize category selection based on the other card
        optimal_category = find_optimal_category_for_uob_ladys_with_other_card(
            card2_id, spending_model, miles_to_sgd_rate, data_loader, calculator
        )
        card1_result = calculator.calculate_uob_ladys_reward_with_optimization(
            card1_id, spending_model, miles_to_sgd_rate, optimal_category
        )
    else:
        card1_result = calculator.calculate_single_card_reward(
            card1_id, spending_model, miles_to_sgd_rate)

    if is_uob_ladys_card2:
        # For UOB Lady's, we need to optimize category selection based on the other card
        optimal_category = find_optimal_category_for_uob_ladys_with_other_card(
            card1_id, spending_model, miles_to_sgd_rate, data_loader, calculator
        )
        card2_result = calculator.calculate_uob_ladys_reward_with_optimization(
            card2_id, spending_model, miles_to_sgd_rate, optimal_category
        )
    else:
        card2_result = calculator.calculate_single_card_reward(
            card2_id, spending_model, miles_to_sgd_rate)

    # Simple combination: sum the rewards
    total_reward = card1_result.monthly_reward + card2_result.monthly_reward

    # Get categories for both cards
    card1_categories = data_loader.get_card_categories(card1_id)
    card2_categories = data_loader.get_card_categories(card2_id)
    all_categories = list(set(card1_categories + card2_categories))

    # Create allocation data
    allocation = {
        card1_data['Card Name']: {
            'reward': card1_result.monthly_reward,
            'categories': card1_categories,
            'details': card1_result.details or []
        },
        card2_data['Card Name']: {
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


def find_optimal_category_for_uob_ladys_with_other_card(other_card_id: int, spending: UserSpending, 
                                                       miles_to_sgd_rate: float, data_loader, calculator) -> str:
    """
    Find the optimal category for UOB Lady's card when used with another card
    
    Args:
        other_card_id: ID of the other card in the combination
        spending: User spending data
        miles_to_sgd_rate: Miles to SGD conversion rate
        data_loader: Data loader instance
        calculator: Reward calculator instance
        
    Returns:
        Optimal category name for UOB Lady's card
    """
    # UOB Lady's eligible categories (4mpd categories)
    eligible_categories = ['Dining', 'Transport', 'Entertainment', 'Retail', 'Travel']
    
    # Get the other card's breakdown to see what categories it covers well
    other_card_breakdown = calculator.get_detailed_breakdown(other_card_id, spending)
    
    best_category = 'Other'  # Default fallback
    best_additional_reward = 0.0
    
    for category in eligible_categories:
        category_spending = getattr(spending, category.lower(), 0.0)
        if category_spending > 0:
            # Check if the other card already covers this category well
            other_card_rate = other_card_breakdown.category_rewards.get(category, 0.0)
            
            # Calculate potential reward for UOB Lady's on this category
            miles_earned = category_spending * 4.0
            potential_reward = miles_earned * miles_to_sgd_rate
            
            # Calculate additional value (UOB Lady's 4mpd vs other card's rate)
            additional_value = potential_reward - other_card_rate
            
            if additional_value > best_additional_reward:
                best_additional_reward = additional_value
                best_category = category
    
    return best_category
