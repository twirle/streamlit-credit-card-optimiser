"""
Components Package

This package contains all UI components organized by functionality:
- inputs: User input components (spending, filters)
- charts: Chart and visualization components
- tables: Table display components
- layout: Layout and dashboard components
- cards: Card analysis and recommendation components
"""

# Import from modular components
from .inputs import create_spending_inputs, create_filters
from .layout import create_summary_dashboard, display_miles_info
from .charts import (
    create_rewards_comparison_chart,
    create_spending_breakdown_chart,
    create_strategy_comparison_chart
)
from .tables import (
    display_results_table,
    display_combination_results_table,
    display_spending_allocation_table,
    create_detailed_spending_table
)
from .cards import (
    display_top_card_recommendation,
    display_card_calculation_details,
    render_detailed_card_breakdown
)

# Import refactored main components
from .single_card_component import render_single_card_component
from .combination_card_component import render_combination_component

__all__ = [
    # Input components
    'create_spending_inputs',
    'create_filters',
    
    # Layout components
    'create_summary_dashboard',
    'display_miles_info',
    
    # Chart components
    'create_rewards_comparison_chart',
    'create_spending_breakdown_chart',
    'create_strategy_comparison_chart',
    
    # Table components
    'display_results_table',
    'display_combination_results_table',
    'display_spending_allocation_table',
    'create_detailed_spending_table',
    
    # Card components
    'display_top_card_recommendation',
    'display_card_calculation_details',
    'render_detailed_card_breakdown',
    
    # Main components
    'render_single_card_component',
    'render_combination_component'
] 