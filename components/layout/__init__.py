"""
Layout Package

This package contains all layout-related components including
summary dashboards, metrics, and insights.
"""

from .summary_dashboard import (
    create_summary_dashboard,
    display_miles_info
)

__all__ = [
    'create_summary_dashboard',
    'display_miles_info'
]
