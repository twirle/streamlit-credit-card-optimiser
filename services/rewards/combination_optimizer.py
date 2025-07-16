"""
Card Combination Optimizer

This module handles the optimization logic for multi-card combinations,
including intelligent category allocation and UOB Lady's optimization.
"""

import pandas as pd
from typing import List, Dict, Any
from models.credit_card_model import UserSpending
from services.data.card_loader import get_card_loader
from .calculator import get_reward_calculator
from .uob_ladys_optimizer import get_uob_ladys_optimizer


class CombinationOptimizer:
    """Handles multi-card combination optimization"""

    def __init__(self):
        self.card_loader = get_card_loader()
        self.calculator = get_reward_calculator()
        self.uob_optimizer = get_uob_ladys_optimizer()

    def find_best_combinations(self, filtered_cards_df: pd.DataFrame, user_spending_data: dict, 
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
        combinations = []

        # Use all available cards for combinations (no limit)
        all_cards = filtered_cards_df.to_dict('records')

        # First, prioritize UOB Lady's combinations since they can be highly valuable
        uob_ladys_combinations = []
        other_combinations = []

        for i, card1 in enumerate(all_cards):
            for j, card2 in enumerate(all_cards):
                if i >= j:  # Avoid duplicate combinations
                    continue

                # Create combination name
                combination_name = f"{card1['Card Name']} + {card2['Card Name']}"

                # Calculate combined rewards
                combined_result = self.combine_two_cards_rewards(
                    card1, card2, user_spending_data, miles_to_sgd_rate
                )

                if combined_result['total_reward'] > 0:
                    combination_data = {
                        'Card Name': combination_name,
                        'Issuer': f"{card1['Issuer']} + {card2['Issuer']}",
                        'Categories': combined_result.get('categories', ''),
                        'Monthly Reward': combined_result['total_reward'],
                        'Card1': card1['Card Name'],
                        'Card2': card2['Card Name']
                    }

                    # Check if this combination includes UOB Lady's
                    if 'UOB Lady' in combination_name:
                        uob_ladys_combinations.append(combination_data)
                    else:
                        other_combinations.append(combination_data)

        # Sort both lists by monthly reward (descending)
        uob_ladys_combinations.sort(key=lambda x: x['Monthly Reward'], reverse=True)
        other_combinations.sort(key=lambda x: x['Monthly Reward'], reverse=True)

        # Combine lists with UOB Lady's combinations first
        combinations = uob_ladys_combinations + other_combinations

        return combinations  # Return all combinations (no limit)

    def calculate_optimal_spending_allocation(self, card1_id: int, card2_id: int, 
                                            spending: UserSpending, miles_to_sgd_rate: float,
                                            is_uob_ladys_card1: bool, is_uob_ladys_card2: bool) -> Dict[str, Any]:
        """
        Calculate optimal spending allocation between two cards to avoid double-counting
        
        Args:
            card1_id: First card ID
            card2_id: Second card ID
            spending: User spending data
            miles_to_sgd_rate: Miles to SGD conversion rate
            is_uob_ladys_card1: Whether first card is UOB Lady's
            is_uob_ladys_card2: Whether second card is UOB Lady's
            
        Returns:
            Dictionary with allocation results
        """
        # Initialize spending allocation
        card1_spending = UserSpending()
        card2_spending = UserSpending()
        
        # Get card categories
        card1_categories = self.card_loader.get_card_categories(card1_id)
        card2_categories = self.card_loader.get_card_categories(card2_id)
        
        # Determine UOB Lady's categories if applicable
        uob_ladys_category1 = None
        uob_ladys_category2 = None
        
        if is_uob_ladys_card1:
            uob_ladys_category1 = self.uob_optimizer.find_optimal_category_with_other_card(
                card2_id, spending, miles_to_sgd_rate
            )
        
        if is_uob_ladys_card2:
            uob_ladys_category2 = self.uob_optimizer.find_optimal_category_with_other_card(
                card1_id, spending, miles_to_sgd_rate
            )
        
        # Allocate spending category by category
        categories = ['dining', 'groceries', 'petrol', 'transport', 'streaming', 
                     'entertainment', 'utilities', 'online', 'travel', 'overseas', 
                     'retail', 'departmental', 'other']
        
        for category in categories:
            category_spending = getattr(spending, category, 0.0)
            if category_spending <= 0:
                continue
                
            # Determine which card should get this category
            card1_value = self.calculate_category_value_for_card(
                card1_id, category, category_spending, miles_to_sgd_rate, 
                is_uob_ladys_card1, uob_ladys_category1, spending.total
            )
            
            card2_value = self.calculate_category_value_for_card(
                card2_id, category, category_spending, miles_to_sgd_rate,
                is_uob_ladys_card2, uob_ladys_category2, spending.total
            )
            
            # Allocate to the card that provides higher value
            if card1_value >= card2_value:
                setattr(card1_spending, category, category_spending)
            else:
                setattr(card2_spending, category, category_spending)
        
        return {
            'card1_spending': card1_spending,
            'card2_spending': card2_spending,
            'uob_ladys_category1': uob_ladys_category1,
            'uob_ladys_category2': uob_ladys_category2
        }

    def calculate_category_value_for_card(self, card_id: int, category: str, 
                                         spending: float, miles_to_sgd_rate: float,
                                         is_uob_ladys: bool, uob_ladys_category: str | None = None, 
                                         total_spending: float = 2000.0) -> float:
        """
        Calculate the value a card would provide for a specific category
        
        Args:
            card_id: Card ID
            category: Category name
            spending: Spending amount
            miles_to_sgd_rate: Miles to SGD conversion rate
            is_uob_ladys: Whether this is UOB Lady's card
            uob_ladys_category: UOB Lady's selected category (if applicable)
            
        Returns:
            Value in SGD
        """
        if spending <= 0:
            return 0.0
            
        # For UOB Lady's, use 4mpd for selected category, 0.4mpd for others
        if is_uob_ladys and uob_ladys_category:
            category_title = category.title()
            if category_title == uob_ladys_category:
                rate_value = 4.0  # 4mpd for selected category
                rate_type = 'mpd'
            else:
                rate_value = 0.4  # 0.4mpd for other categories
                rate_type = 'mpd'
        else:
            # Get actual card rates for this category
            try:
                # Get the card's best tier for total spending
                best_tier = self.card_loader.get_best_tier_for_spending(card_id, total_spending)
                if best_tier:
                    # Get rates for this tier
                    rates_df = self.card_loader.get_reward_rates(best_tier.tier_id)
                    # Filter out 0 rates
                    rates_df = rates_df[rates_df['Rate Value'] > 0].copy()
                    
                    # Find the rate for this specific category
                    category_rate = rates_df[rates_df['category'].str.lower() == category.lower()].copy()
                    if len(category_rate) > 0:
                        rate_value = float(category_rate.iloc[0]['Rate Value'])
                        rate_type = str(category_rate.iloc[0]['Rate Type'])
                    else:
                        # If category not found, use 0 rate
                        rate_value = 0.0
                        rate_type = 'mpd'
                else:
                    # No suitable tier found
                    rate_value = 0.0
                    rate_type = 'mpd'
            except Exception as e:
                # Fallback to 0 rate if there's an error
                print(f"Error getting rate for card {card_id}, category {category}: {e}")
                rate_value = 0.0
                rate_type = 'mpd'
            
        # Calculate value
        if rate_type == 'percentage':
            value = spending * (rate_value / 100)
        else:  # mpd
            value = spending * rate_value * miles_to_sgd_rate
            
        return value

    def calculate_card_rewards_with_allocation(self, card_id: int, allocated_spending: UserSpending,
                                              miles_to_sgd_rate: float, is_uob_ladys: bool,
                                              uob_ladys_category: str | None = None):
        """
        Calculate rewards for a card using allocated spending
        
        Args:
            card_id: Card ID
            allocated_spending: Allocated spending for this card
            miles_to_sgd_rate: Miles to SGD conversion rate
            is_uob_ladys: Whether this is UOB Lady's card
            uob_ladys_category: UOB Lady's selected category (if applicable)
            
        Returns:
            RewardCalculation object
        """
        if is_uob_ladys:
            return self.uob_optimizer.calculate_uob_ladys_rewards(
                card_id, allocated_spending, miles_to_sgd_rate, uob_ladys_category
            )
        else:
            return self.calculator.calculate_card_rewards(card_id, allocated_spending, miles_to_sgd_rate)

    def combine_two_cards_rewards(self, card1_data: dict, card2_data: dict, 
                                 user_spending_data: dict, miles_to_sgd_rate: float) -> Dict[str, Any]:
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
        # Convert user_spending_data dict to UserSpending object
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
        all_cards = self.card_loader.get_all_cards()

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

        # Calculate optimal spending allocation between the two cards
        allocation_result = self.calculate_optimal_spending_allocation(
            card1_id, card2_id, spending_model, miles_to_sgd_rate,
            is_uob_ladys_card1, is_uob_ladys_card2
        )

        # Calculate rewards using the allocated spending
        card1_result = self.calculate_card_rewards_with_allocation(
            card1_id, allocation_result['card1_spending'], miles_to_sgd_rate,
            is_uob_ladys_card1, allocation_result.get('uob_ladys_category1')
        )

        card2_result = self.calculate_card_rewards_with_allocation(
            card2_id, allocation_result['card2_spending'], miles_to_sgd_rate,
            is_uob_ladys_card2, allocation_result.get('uob_ladys_category2')
        )

        # Calculate total reward
        total_reward = card1_result.monthly_reward + card2_result.monthly_reward

        # Get categories for both cards
        card1_categories = self.card_loader.get_card_categories(card1_id)
        card2_categories = self.card_loader.get_card_categories(card2_id)
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

    def calculate_card_combination_reward(self, card_ids: List[int], spending: UserSpending) -> Dict[str, Any]:
        """
        Calculate rewards for a combination of cards

        Args:
            card_ids: List of card IDs
            spending: User spending data

        Returns:
            Dictionary with combination results
        """
        if len(card_ids) != 2:
            raise ValueError("Currently only supports 2-card combinations")

        # Get card data
        card1 = self.card_loader.get_card_info(card_ids[0])
        card2 = self.card_loader.get_card_info(card_ids[1])

        if not card1 or not card2:
            raise ValueError("One or both cards not found")

        # Convert to dict format for compatibility
        card1_data = {
            'Card Name': card1.name,
            'Issuer': card1.issuer,
            'Card Type': card1.card_type
        }
        card2_data = {
            'Card Name': card2.name,
            'Issuer': card2.issuer,
            'Card Type': card2.card_type
        }

        # Convert spending to dict format
        spending_dict = spending.to_dict()
        spending_dict.pop('total', None)  # Remove total key

        return self.combine_two_cards_rewards(card1_data, card2_data, spending_dict, 0.02)

    def get_optimal_combination(self, spending: UserSpending, max_cards: int = 3) -> Dict[str, Any]:
        """
        Find the optimal card combination for given spending

        Args:
            spending: User spending data
            max_cards: Maximum number of cards in combination

        Returns:
            Dictionary with optimal combination results
        """
        if max_cards != 2:
            raise ValueError("Currently only supports 2-card combinations")

        # Get all cards
        all_cards = self.card_loader.get_all_cards()
        
        # Convert to DataFrame format
        cards_df = pd.DataFrame([
            {
                'Card Name': card.name,
                'Issuer': card.issuer,
                'Card Type': card.card_type
            }
            for card in all_cards
        ])

        # Convert spending to dict format
        spending_dict = spending.to_dict()
        spending_dict.pop('total', None)  # Remove total key

        # Find best combinations
        combinations = self.find_best_combinations(
            cards_df, spending_dict, 0.02, pd.DataFrame()
        )

        if combinations:
            return {
                'optimal_combination': combinations[0],
                'all_combinations': combinations[:10]  # Top 10
            }
        else:
            return {
                'optimal_combination': None,
                'all_combinations': []
            }


# Global combination optimizer instance
def get_combination_optimizer() -> CombinationOptimizer:
    """Get combination optimizer instance"""
    return CombinationOptimizer() 