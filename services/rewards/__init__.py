"""
Rewards Service Package

This package provides comprehensive reward calculation functionality for credit cards,
including single card calculations, UOB Lady's optimization, and multi-card combinations.
"""

from .calculator import get_reward_calculator, RewardCalculator
from .uob_ladys_optimizer import get_uob_ladys_optimizer, UOBLadysOptimizer
from .combination_optimizer import get_combination_optimizer, CombinationOptimizer

__all__ = [
    'get_reward_calculator',
    'RewardCalculator',
    'get_uob_ladys_optimizer',
    'UOBLadysOptimizer',
    'get_combination_optimizer',
    'CombinationOptimizer'
] 