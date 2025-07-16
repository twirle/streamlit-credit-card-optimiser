"""
Tables Package

This package contains all table-related components including
results tables, combination tables, and data formatting.
"""

from .results_table import (
    display_results_table,
    display_combination_results_table,
    display_spending_allocation_table,
    create_detailed_spending_table
)

__all__ = [
    'display_results_table',
    'display_combination_results_table',
    'display_spending_allocation_table',
    'create_detailed_spending_table'
]
