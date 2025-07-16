"""
Core Reward Calculator

This module contains the core reward calculation logic for credit cards,
excluding UOB Lady's specific optimizations and combination logic.
"""

import pandas as pd
from typing import List, Dict, Optional
import streamlit as st

from models.credit_card_model import (
    UserSpending, RewardCalculation, CardRewardBreakdown
)
from services.data.card_loader import get_card_loader


class RewardCalculator:
    """Core service for calculating credit card rewards"""

    def __init__(self):
        self.card_loader = get_card_loader()

    def calculate_card_rewards(self, card_id: int, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> RewardCalculation:
        """
        Calculate rewards for a single card (excluding UOB Lady's special logic)

        Args:
            card_id: ID of the card
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD (default 0.02)

        Returns:
            RewardCalculation object with results
        """
        # Get card info
        card = self.card_loader.get_card_info(card_id)
        if not card:
            raise ValueError(f"Card with ID {card_id} not found")

        # Get best tier for spending
        best_tier = self.card_loader.get_best_tier_for_spending(card_id, spending.total)
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
        rates_df = self.card_loader.get_reward_rates(best_tier.tier_id)
        
        # Filter out categories with 0 rates (0% or 0mpd)
        rates_df = rates_df[rates_df['Rate Value'] > 0].copy()

        # Calculate rewards by category with shared cap handling
        category_rewards = {}
        total_reward = 0.0
        cap_status = {"reached": False, "amount": 0.0, "difference": 0.0}
        details = []
        original_reward = 0.0

        # Group categories by cap_group
        cap_groups = {}
        uncapped_categories = []
        
        for _, rate_row in rates_df.iterrows():
            category = str(rate_row['category'])
            cap_group = rate_row.get('cap_group', None)
            
            # Handle NaN values and empty strings
            if cap_group and pd.notna(cap_group) and str(cap_group).strip():
                cap_group_str = str(cap_group).strip()
                if cap_group_str not in cap_groups:
                    cap_groups[cap_group_str] = []
                cap_groups[cap_group_str].append(rate_row)
            else:
                uncapped_categories.append(rate_row)

        # Process uncapped categories first
        for rate_row in uncapped_categories:
            category = str(rate_row['category'])
            rate_value = float(rate_row['Rate Value'])
            rate_type = str(rate_row['Rate Type'])
            cap_amount = rate_row.get('Cap Amount')
            cap_type = rate_row.get('Cap Type')
            
            # Get spending for this category
            category_spending = getattr(spending, category.lower(), 0.0)
            
            if category_spending > 0:
                reward = self._calculate_category_reward(
                    category_spending, rate_value, rate_type, miles_to_sgd_rate
                )
                
                # Apply individual cap if exists
                if cap_amount is not None:
                    reward = self._apply_cap(reward, category_spending, cap_amount, cap_type, rate_value, rate_type, miles_to_sgd_rate)
                
                category_rewards[category] = reward
                total_reward += reward
                original_reward += reward
                
                # Add to details
                self._add_to_details(details, category, category_spending, rate_value, rate_type, reward, miles_to_sgd_rate)

        # Process capped groups
        for cap_group, group_rates in cap_groups.items():
            group_rewards = {}
            group_total_reward = 0.0
            group_total_original = 0.0
            group_details = []
            
            # Find the cap row (usually has cap_amount set)
            cap_row = None
            category_rows = []
            
            for rate_row in group_rates:
                if pd.notna(rate_row.get('Cap Amount')):
                    cap_row = rate_row
                else:
                    category_rows.append(rate_row)
            
            # Calculate rewards for each category in the group
            for rate_row in category_rows:
                category = str(rate_row['category'])
                rate_value = float(rate_row['Rate Value'])
                rate_type = str(rate_row['Rate Type'])
                
                category_spending = getattr(spending, category.lower(), 0.0)
                
                if category_spending > 0:
                    reward = self._calculate_category_reward(
                        category_spending, rate_value, rate_type, miles_to_sgd_rate
                    )
                    group_rewards[category] = reward
                    group_total_reward += reward
                    group_total_original += reward
                    
                    # Add to group details
                    self._add_to_details(group_details, category, category_spending, rate_value, rate_type, reward, miles_to_sgd_rate)
            
            # Apply shared cap if exists
            if cap_row is not None and group_total_reward > 0:
                cap_amount = float(cap_row['Cap Amount'])
                cap_type = str(cap_row['Cap Type'])
                
                if group_total_reward > cap_amount:
                    # Cap reached - distribute proportionally
                    cap_ratio = cap_amount / group_total_reward
                    group_total_reward = cap_amount
                    cap_status["reached"] = True
                    cap_status["amount"] = cap_amount
                    cap_status["difference"] = group_total_original - cap_amount
                    
                    # Update individual category rewards proportionally
                    for category in group_rewards:
                        group_rewards[category] *= cap_ratio
                    
                    # Update details to reflect capping
                    group_details = []
                    for rate_row in category_rows:
                        category = str(rate_row['category'])
                        if category in group_rewards:
                            category_spending = getattr(spending, category.lower(), 0.0)
                            rate_value = float(rate_row['Rate Value'])
                            rate_type = str(rate_row['Rate Type'])
                            reward = group_rewards[category]
                            self._add_to_details(group_details, category, category_spending, rate_value, rate_type, reward, miles_to_sgd_rate)
            
            # Add group rewards to total
            category_rewards.update(group_rewards)
            total_reward += group_total_reward
            original_reward += group_total_original
            details.extend(group_details)

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

    def _calculate_category_reward(self, category_spending: float, rate_value: float, rate_type: str, miles_to_sgd_rate: float) -> float:
        """Calculate reward for a single category"""
        if rate_type == 'percentage':
            return (category_spending * rate_value) / 100
        else:  # mpd
            miles_earned = category_spending * rate_value
            return miles_earned * miles_to_sgd_rate

    def _apply_cap(self, reward: float, category_spending: float, cap_amount: float, cap_type: str, rate_value: float, rate_type: str, miles_to_sgd_rate: float) -> float:
        """Apply cap to a single category reward"""
        if cap_type == 'dollars_earned':
            if reward > cap_amount:
                return cap_amount
        elif cap_type == 'dollars_spent':
            if category_spending > cap_amount:
                capped_spending = cap_amount
                return self._calculate_category_reward(capped_spending, rate_value, rate_type, miles_to_sgd_rate)
        return reward

    def _add_to_details(self, details: list, category: str, category_spending: float, rate_value: float, rate_type: str, reward: float, miles_to_sgd_rate: float):
        """Add category calculation to details list"""
        if rate_type == 'percentage':
            details.append(f"{category}: ${category_spending:.2f} × {rate_value}% = ${reward:.2f}")
        else:  # mpd
            miles_earned = category_spending * rate_value
            details.append(f"{category}: ${category_spending:.2f} × {rate_value} mpd = {miles_earned:.0f} miles × ${miles_to_sgd_rate:.3f} = ${reward:.2f}")

    def calculate_all_cards_rewards(self, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
        """
        Calculate rewards for all available cards

        Args:
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD

        Returns:
            List of RewardCalculation objects
        """
        all_cards = self.card_loader.get_all_cards()
        results = []
        
        for card in all_cards:
            try:
                result = self.calculate_card_rewards(card.card_id, spending, miles_to_sgd_rate)
                results.append(result)
            except Exception as e:
                # Log error and continue with other cards
                print(f"Error calculating rewards for card {card.name}: {e}")
                continue
        
        return results

    def calculate_filtered_cards_rewards(self, selected_cards_df: pd.DataFrame, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> List[RewardCalculation]:
        """
        Calculate rewards for filtered cards

        Args:
            selected_cards_df: DataFrame of selected cards
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD

        Returns:
            List of RewardCalculation objects
        """
        results = []
        
        for _, card_row in selected_cards_df.iterrows():
            try:
                # Find card ID by name
                all_cards = self.card_loader.get_all_cards()
                card_id = None
                for card in all_cards:
                    if card.name == card_row['Card Name']:
                        card_id = card.card_id
                        break
                
                if card_id is not None:
                    result = self.calculate_card_rewards(card_id, spending, miles_to_sgd_rate)
                    results.append(result)
            except Exception as e:
                print(f"Error calculating rewards for card {card_row['Card Name']}: {e}")
                continue
        
        return results

    def get_best_cards(self, results: List[RewardCalculation], limit: int = 5) -> List[RewardCalculation]:
        """
        Get top performing cards from results

        Args:
            results: List of RewardCalculation objects
            limit: Number of top cards to return

        Returns:
            List of top RewardCalculation objects
        """
        # Sort by monthly reward (descending)
        sorted_results = sorted(results, key=lambda x: x.monthly_reward, reverse=True)
        
        # Get unique cards (keep best tier for each card)
        unique_cards = {}
        for result in sorted_results:
            if result.card_name not in unique_cards:
                unique_cards[result.card_name] = result
        
        # Return top cards
        top_cards = list(unique_cards.values())
        return top_cards[:limit]

    def get_detailed_breakdown(self, card_id: int, spending: UserSpending) -> CardRewardBreakdown:
        """
        Get detailed breakdown for a specific card

        Args:
            card_id: ID of the card
            spending: User spending data

        Returns:
            CardRewardBreakdown object
        """
        # Get card info
        card = self.card_loader.get_card_info(card_id)
        if not card:
            raise ValueError(f"Card with ID {card_id} not found")

        # Get best tier
        best_tier = self.card_loader.get_best_tier_for_spending(card_id, spending.total)
        if not best_tier:
            return CardRewardBreakdown(
                card_id=card_id,
                card_name=card.name,
                tier_id=0,
                tier_description="No suitable tier",
                category_rewards={},
                total_reward=0.0,
                cap_status={"reached": False, "amount": 0.0, "difference": 0.0},
                min_spend_met=False
            )

        # Get rates and calculate breakdown
        rates_df = self.card_loader.get_reward_rates(best_tier.tier_id)
        
        # Filter out categories with 0 rates (0% or 0mpd)
        rates_df = rates_df[rates_df['Rate Value'] > 0].copy()
        
        category_rewards = {}
        total_reward = 0.0

        for _, rate_row in rates_df.iterrows():
            category = str(rate_row['category'])
            rate_value = float(rate_row['Rate Value'])
            rate_type = str(rate_row['Rate Type'])
            
            category_spending = getattr(spending, category.lower(), 0.0)
            
            if category_spending > 0:
                if rate_type == 'percentage':
                    reward = (category_spending * rate_value) / 100
                else:  # mpd
                    miles_earned = category_spending * rate_value
                    reward = miles_earned * 0.02  # Default miles rate
                
                category_rewards[category] = reward
                total_reward += reward

        return CardRewardBreakdown(
            card_id=card_id,
            card_name=card.name,
            tier_id=best_tier.tier_id,
            tier_description=best_tier.description,
            category_rewards=category_rewards,
            total_reward=total_reward,
            cap_status={"reached": False, "amount": 0.0, "difference": 0.0},
            min_spend_met=True
        )


# Global calculator instance
@st.cache_resource
def get_reward_calculator() -> RewardCalculator:
    """Get cached reward calculator instance"""
    return RewardCalculator() 