"""
Unit tests for calculations module

This module contains tests for the reward calculation functions
in the services.calculations module.
"""

import pytest
import pandas as pd
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.calculations import (
    calculate_card_reward_details,
    calculate_category_reward,
    combine_two_cards_rewards
)


class TestCalculations:
    """Test class for calculation functions"""
    
    def setup_method(self):
        """Set up test data before each test"""
        self.sample_card = pd.Series({
            'Name': 'Test Card',
            'Issuer': 'Test Bank',
            'Type': 'Cashback',
            'Min Spend': 800,
            'Cap': 80,
            'Dining Rate': 6.0,
            'Groceries Rate': 6.0,
            'Petrol Rate': 8.0,
            'Base Rate': 0.2
        })
        
        self.sample_spending = {
            'dining': 300,
            'groceries': 400,
            'petrol': 200,
            'transport': 150,
            'streaming': 25,
            'entertainment': 50,
            'utilities': 150,
            'online': 250,
            'travel': 0,
            'overseas': 50,
            'other': 150,
            'total': 1725
        }
    
    def test_calculate_category_reward_cashback(self):
        """Test category reward calculation for cashback card"""
        reward = calculate_category_reward(
            self.sample_card, 'dining', 300, 0.02
        )
        expected = 300 * (6.0 / 100)  # 6% cashback
        assert reward == expected
    
    def test_calculate_category_reward_miles(self):
        """Test category reward calculation for miles card"""
        miles_card = self.sample_card.copy()
        miles_card['Type'] = 'Miles'
        miles_card['Dining Rate'] = 3.0  # 3 mpd
        
        reward = calculate_category_reward(
            miles_card, 'dining', 300, 0.02
        )
        expected = 300 * 3.0 * 0.02  # 3 mpd * miles value
        assert reward == expected
    
    def test_calculate_card_reward_details_min_spend_met(self):
        """Test card reward calculation when minimum spend is met"""
        reward, details, cap_reached, cap_diff, original_reward, min_spend_met = \
            calculate_card_reward_details(
                self.sample_card, self.sample_spending, 0.02
            )
        
        assert min_spend_met == True
        assert reward > 0
        assert len(details) > 0
    
    def test_calculate_card_reward_details_min_spend_not_met(self):
        """Test card reward calculation when minimum spend is not met"""
        low_spending = self.sample_spending.copy()
        low_spending['total'] = 500  # Below $800 minimum
        
        reward, details, cap_reached, cap_diff, original_reward, min_spend_met = \
            calculate_card_reward_details(
                self.sample_card, low_spending, 0.02
            )
        
        assert min_spend_met == False
        # Should use base rate
        expected_base_reward = 500 * (0.2 / 100)
        assert abs(reward - expected_base_reward) < 0.01
    
    def test_combine_two_cards_rewards(self):
        """Test combining rewards from two cards"""
        card1 = self.sample_card.copy()
        card2 = self.sample_card.copy()
        card2['Name'] = 'Test Card 2'
        card2['Dining Rate'] = 8.0  # Better dining rate
        
        result = combine_two_cards_rewards(
            card1, card2, self.sample_spending, 0.02
        )
        
        assert 'total_reward' in result
        assert 'card1_reward' in result
        assert 'card2_reward' in result
        assert 'allocation' in result
        assert result['total_reward'] > 0


if __name__ == "__main__":
    pytest.main([__file__]) 