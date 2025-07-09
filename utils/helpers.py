"""
Utility functions for the credit card optimizer application

This module contains helper functions that are used across
multiple components of the application.
"""

import re
from typing import Dict, Any, List, Optional
import pandas as pd


def format_currency(amount: float, currency: str = "SGD") -> str:
    """
    Format currency amount with proper formatting
    
    Args:
        amount: The amount to format
        currency: Currency code (default: SGD)
        
    Returns:
        str: Formatted currency string
    """
    if currency == "SGD":
        return f"${amount:,.2f}"
    else:
        return f"{currency} {amount:,.2f}"


def parse_rate_from_string(rate_string: str) -> Optional[float]:
    """
    Parse rate from string (e.g., "5%", "2.5 mpd")
    
    Args:
        rate_string: String containing rate information
        
    Returns:
        float: Parsed rate value or None if parsing fails
    """
    if pd.isna(rate_string) or not rate_string:
        return None
    
    # Remove whitespace and convert to string
    rate_str = str(rate_string).strip()
    
    # Extract numeric value
    match = re.search(r'(\d+(?:\.\d+)?)', rate_str)
    if match:
        return float(match.group(1))
    
    return None


def calculate_percentage_difference(value1: float, value2: float) -> float:
    """
    Calculate percentage difference between two values
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        float: Percentage difference
    """
    if value2 == 0:
        return 0.0
    
    return ((value1 - value2) / value2) * 100


def validate_spending_data(spending_data: Dict[str, Any]) -> bool:
    """
    Validate user spending data
    
    Args:
        spending_data: Dictionary containing spending data
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_categories = [
        'dining', 'groceries', 'petrol', 'transport', 'streaming',
        'entertainment', 'utilities', 'online', 'travel', 'overseas', 
        'retail', 'departmental', 'other'
    ]
    
    # Check all required categories exist
    for category in required_categories:
        if category not in spending_data:
            return False
    
    # Check all values are numeric and non-negative
    for category, value in spending_data.items():
        if category != 'total':  # Skip total as it's calculated
            try:
                float_value = float(value)
                if float_value < 0:
                    return False
            except (ValueError, TypeError):
                return False
    
    return True


def get_top_cards_by_category(cards_df: pd.DataFrame, category: str, top_n: int = 5) -> pd.DataFrame:
    """
    Get top cards for a specific spending category
    
    Args:
        cards_df: DataFrame containing card information
        category: Spending category to filter by
        top_n: Number of top cards to return
        
    Returns:
        pd.DataFrame: Top cards for the category
    """
    category_rate_map = {
        'dining': 'Dining Rate',
        'groceries': 'Groceries Rate',
        'petrol': 'Petrol Rate',
        'transport': 'Transport Rate',
        'streaming': 'Streaming Rate',
        'entertainment': 'Entertainment Rate',
        'utilities': 'Utilities Rate',
        'online': 'Online Rate',
        'travel': 'Travel Rate',
        'overseas': 'Overseas Rate',
        'retail': 'Retail Rate',
        'departmental': 'Departmental Rate'
    }
    
    rate_column = category_rate_map.get(category)
    if not rate_column or rate_column not in cards_df.columns:
        return pd.DataFrame()
    
    # Filter cards with rates for this category
    valid_cards = cards_df[cards_df[rate_column].notna() & (cards_df[rate_column] > 0)]
    
    # Sort by rate and return top N
    return valid_cards.nlargest(top_n, rate_column)[['Name', 'Issuer', rate_column, 'Type']]


def sanitize_card_name(card_name: str) -> str:
    """
    Sanitize card name for display and comparison
    
    Args:
        card_name: Original card name
        
    Returns:
        str: Sanitized card name
    """
    # Remove special characters and extra spaces
    sanitized = re.sub(r'[^\w\s-]', '', card_name)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def calculate_annual_benefit(monthly_reward: float) -> float:
    """
    Calculate annual benefit from monthly reward
    
    Args:
        monthly_reward: Monthly reward amount
        
    Returns:
        float: Annual benefit
    """
    return monthly_reward * 12


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """
    Format value as percentage
    
    Args:
        value: Value to format
        decimal_places: Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    return f"{value:.{decimal_places}f}%" 