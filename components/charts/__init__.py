"""
Charts Package

This package contains all chart-related components including
rewards charts, spending breakdown charts, and strategy comparison charts.
"""

from .rewards_chart import (
    create_rewards_comparison_chart,
    create_spending_breakdown_chart,
    create_strategy_comparison_chart
)

__all__ = [
    'create_rewards_comparison_chart',
    'create_spending_breakdown_chart',
    'create_strategy_comparison_chart'
]
