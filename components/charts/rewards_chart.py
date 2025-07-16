"""
Rewards Chart Component

This module handles all chart creation functionality including
rewards comparison charts and spending breakdown charts.
"""

import streamlit as st
import plotly.express as px
import pandas as pd


def create_rewards_comparison_chart(display_results_df: pd.DataFrame, miles_value_cents: float):
    """
    Create enhanced rewards comparison chart with better styling
    
    Args:
        display_results_df: DataFrame with card results
        miles_value_cents: Miles value in cents
        
    Returns:
        Plotly figure object or None
    """
    if len(display_results_df) > 0:
        chart_data = display_results_df.head(10).sort_values(
            'Monthly Reward', ascending=True)

        # Enhanced color scheme
        color_map = {
            'Miles': '#1f77b4',  # Blue for miles
            'Cashback': '#ff7f0e'  # Orange for cashback
        }

        # Create chart without color parameter to avoid grouping
        chart_params = {
            'x': 'Monthly Reward',
            'y': 'Card Name',
            'title': f"Monthly Reward Comparison (Miles @ {miles_value_cents:.1f}¢ each)",
            'labels': {
                'Monthly Reward': 'Monthly Reward ($)', 'Card Name': 'Credit Card'},
            'orientation': 'h',
            'hover_data': ['Issuer', 'Categories', 'Card Type']
        }

        fig = px.bar(chart_data, **chart_params)

        # Apply colors manually to avoid grouping
        if 'Card Type' in chart_data.columns:
            # Create color array based on card type
            colors = [color_map.get(card_type, '#808080') for card_type in chart_data['Card Type']]
            
            # Update bar colors and hover template
            fig.update_traces(
                marker_color=colors,
                hovertemplate="<b>%{y}</b><br>" +
                "Monthly Reward: $%{x:.2f}<br>" +
                "Issuer: %{customdata[0]}<br>" +
                "Categories: %{customdata[1]}<br>" +
                "Card Type: %{customdata[2]}<br>" +
                "<extra></extra>"
            )
        else:
            # Enhanced hover template without card type
            fig.update_traces(
                hovertemplate="<b>%{y}</b><br>" +
                "Monthly Reward: $%{x:.2f}<br>" +
                "Issuer: %{customdata[0]}<br>" +
                "Categories: %{customdata[1]}<br>" +
                "<extra></extra>"
            )

        # Enhanced layout
        fig.update_layout(
            height=600,  # Increased height to accommodate 10 cards
            title_x=0.5,
            title_font_size=16,
            showlegend=False,  # No legend since we're using manual colors
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20)
        )

        return fig
    return None


def create_spending_breakdown_chart(user_spending_data: dict):
    """
    Create spending breakdown pie chart
    
    Args:
        user_spending_data: Dictionary with spending data
        
    Returns:
        Plotly figure object or None
    """
    # Prepare spending data for chart
    spending_categories = {
        'Dining': user_spending_data['dining'],
        'Groceries': user_spending_data['groceries'],
        'Petrol': user_spending_data['petrol'],
        'Transport': user_spending_data['transport'],
        'Streaming': user_spending_data['streaming'],
        'Entertainment': user_spending_data['entertainment'],
        'Utilities': user_spending_data['utilities'],
        'Online': user_spending_data['online'],
        'Travel': user_spending_data['travel'],
        'Overseas': user_spending_data['overseas'],
        'Retail': user_spending_data['retail'],
        'Departmental': user_spending_data['departmental'],
        'Other': user_spending_data['other']
    }

    # Filter out zero spending categories
    spending_categories = {k: v for k, v in spending_categories.items() if v > 0}

    if spending_categories:
        categories = list(spending_categories.keys())
        amounts = list(spending_categories.values())
        spending_df = pd.DataFrame({
            'Category': categories,
            'Amount': amounts
        })

        fig = px.pie(
            spending_df,
            values='Amount',
            names='Category',
            title="Monthly Spending Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig.update_layout(
            title_x=0.5,
            showlegend=True,
            height=400
        )

        return fig
    return None


def create_strategy_comparison_chart(combinations_df: pd.DataFrame, best_single_reward: float, best_single_name: str):
    """
    Create strategy comparison chart for single vs multi-card strategies
    
    Args:
        combinations_df: DataFrame with combination results
        best_single_reward: Best single card reward
        best_single_name: Name of best single card
        
    Returns:
        Plotly figure object
    """
    comparison_strategies = []

    # Add best single card
    comparison_strategies.append({
        'Strategy': f"{best_single_name} (Single)",
        'Monthly Reward': best_single_reward,
        'Strategy Type': 'Single Card'
    })

    # Add top 10 combinations
    for _, combination_data in combinations_df.head(10).iterrows():
        comparison_strategies.append({
            'Strategy': combination_data['Card Name'],
            'Monthly Reward': combination_data['Monthly Reward'],
            'Strategy Type': 'Combination'
        })

    comparison_strategies_df = pd.DataFrame(comparison_strategies)
    comparison_strategies_df = comparison_strategies_df.sort_values(
        'Monthly Reward', ascending=True)

    comparison_chart = px.bar(
        comparison_strategies_df,
        x='Monthly Reward',
        y='Strategy',
        color='Strategy Type',
        title="Single Card vs Multi-Card Strategies",
        labels={'Monthly Reward': 'Monthly Reward'},
        orientation='h'
    )
    comparison_chart.update_layout(height=400)
    return comparison_chart 