"""
Inputs Package

This package contains all input-related components including
spending inputs, filters, and user controls.
"""

from .spending_inputs import create_spending_inputs
from .filters import create_filters

__all__ = [
    'create_spending_inputs',
    'create_filters'
] 