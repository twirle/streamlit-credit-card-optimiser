"""
UOB Lady's Card Optimizer

This module handles the specific optimization logic for UOB Lady's card,
which can select one category for 4mpd rewards while other categories get 0.4mpd.
"""

from typing import Optional
from models.credit_card_model import UserSpending, RewardCalculation
from services.data.card_loader import get_card_loader
from .calculator import get_reward_calculator


class UOBLadysOptimizer:
    """Handles UOB Lady's card specific optimization logic"""

    def __init__(self):
        self.card_loader = get_card_loader()
        self.calculator = get_reward_calculator()

    def find_largest_eligible_category(self, spending: UserSpending) -> tuple[str, float]:
        """
        Find the largest spending category that's eligible for UOB Lady's 4mpd rewards
        
        Args:
            spending: User spending data
            
        Returns:
            Tuple of (category_name, spending_amount)
        """
        # UOB Lady's eligible categories (4mpd categories)
        eligible_categories = ['Dining', 'Transport', 'Entertainment', 'Retail', 'Travel']
        
        largest_category = 'Other'
        largest_spending = 0.0
        
        for category in eligible_categories:
            category_spending = getattr(spending, category.lower(), 0.0)
            if category_spending > largest_spending:
                largest_spending = category_spending
                largest_category = category
        
        return largest_category, largest_spending

    def find_optimal_category_for_single_card(self, spending: UserSpending, miles_to_sgd_rate: float = 0.02) -> str:
        """
        Find the most efficient category for UOB Lady's card based on spending and potential reward.
        Prioritizes the largest spending category for maximum 4mpd value.
        
        Args:
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD
            
        Returns:
            Category name that would provide the highest reward
        """
        # Find the largest eligible category
        largest_category, largest_spending = self.find_largest_eligible_category(spending)
        
        # If we have a large spending category, prioritize it
        if largest_spending > 0:
            return largest_category
        
        # Fallback to original logic for smaller amounts
        eligible_categories = ['Dining', 'Transport', 'Entertainment', 'Retail', 'Travel']
        best_category = 'Other'
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

    def find_optimal_category_with_other_card(self, other_card_id: int, spending: UserSpending, 
                                             miles_to_sgd_rate: float = 0.02) -> str:
        """
        Find the optimal category for UOB Lady's card when used with another card.
        Prioritizes the largest spending category for maximum 4mpd value.
        
        Args:
            other_card_id: ID of the other card in the combination
            spending: User spending data
            miles_to_sgd_rate: Miles to SGD conversion rate
            
        Returns:
            Optimal category name for UOB Lady's card
        """
        # Find the largest spending category among eligible categories
        largest_category, largest_spending = self.find_largest_eligible_category(spending)
        
        # If no eligible categories have spending, fall back to default logic
        if largest_spending == 0.0:
            return self.find_optimal_category_for_single_card(spending, miles_to_sgd_rate)
        
        # Get the other card's breakdown to see what categories it covers well
        other_card_breakdown = self.calculator.get_detailed_breakdown(other_card_id, spending)
        
        # Check if the largest category is already well-covered by the other card
        other_card_rate = other_card_breakdown.category_rewards.get(largest_category, 0.0)
        
        # Calculate UOB Lady's potential reward on the largest category
        uob_potential_reward = largest_spending * 4.0 * miles_to_sgd_rate
        
        # If the other card doesn't cover the largest category well, prioritize it
        if other_card_rate < uob_potential_reward * 0.8:  # Other card provides less than 80% of UOB Lady's value
            return largest_category
        
        # If the largest category is well-covered, find the next best option
        eligible_categories = ['Dining', 'Transport', 'Entertainment', 'Retail', 'Travel']
        best_category = largest_category  # Default to largest category
        best_value = uob_potential_reward
        
        for category in eligible_categories:
            category_spending = getattr(spending, category.lower(), 0.0)
            if category_spending > 0:
                # Check if the other card already covers this category well
                other_card_rate = other_card_breakdown.category_rewards.get(category, 0.0)
                
                # Calculate potential reward for UOB Lady's on this category
                miles_earned = category_spending * 4.0
                potential_reward = miles_earned * miles_to_sgd_rate
                
                # If the other card doesn't cover this category well, consider it
                if other_card_rate < potential_reward * 0.8:
                    if potential_reward > best_value:
                        best_value = potential_reward
                        best_category = category
        
        return best_category

    def calculate_uob_ladys_rewards(self, card_id: int, spending: UserSpending, 
                                   miles_to_sgd_rate: float = 0.02, 
                                   selected_category: Optional[str] = None) -> RewardCalculation:
        """
        Calculate rewards for UOB Lady's card with intelligent category selection
        
        Args:
            card_id: ID of the UOB Lady's card (should be 15)
            spending: User spending data
            miles_to_sgd_rate: Conversion rate from miles to SGD
            selected_category: Optional category to use (for multi-card optimization)
            
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

        # Determine the optimal category if not provided
        if selected_category is None:
            selected_category = self.find_optimal_category_for_single_card(spending, miles_to_sgd_rate)

        # Calculate rewards with the selected category getting 4mpd, others getting 0.4mpd
        total_reward = 0.0
        cap_status = {"reached": False, "amount": 0.0, "difference": 0.0}
        details = []
        original_reward = 0.0

        # Get all categories that UOB Lady's supports
        card_categories = self.card_loader.get_card_categories(card_id)
        
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


# Global UOB Lady's optimizer instance
def get_uob_ladys_optimizer() -> UOBLadysOptimizer:
    """Get UOB Lady's optimizer instance"""
    return UOBLadysOptimizer() 