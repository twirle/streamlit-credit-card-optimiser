# Streamlit Credit Card Optimizer

## Overview

The Streamlit Credit Card Optimizer is a web application designed to help Singaporeans find the best credit card strategies based on their spending patterns. The application calculates potential rewards from various credit cards and provides insights into the best combinations of cards to maximize benefits.

Live dashboard can be found [here](https://app-credit-card-optimiser-2vcrpskqeuohjezjkqhgbj.streamlit.app/).

## Setup Instructions

**Run the application**:

```
pip install -r requirements.txt
streamlit run app.py
```

## Usage

Users can input their monthly spending across various categories.
Application will calculate the rewards in realtime as spending amounts in different categories for individual credit cards and suggest optimal combinations to maximize rewards.
Users can view detailed breakdowns of how rewards are calculated and the impact of spending patterns on potential earnings.
Monthly spending chart included as well

## How the Algorithm Works

The optimizer uses a rules-based and combinatorial approach to maximize your rewards:

- **Single Card Calculation**: For each card, the app:
  - Applies category-specific reward rates and caps as defined by the card’s terms.
  - Handles special rules (e.g., UOB Lady’s: only one group gets the high rate, Lady’s Solitaire: two groups, DBS yuu: bonus rates with minimum spend, etc).
  - If a card has a monthly cap, the breakdown and reward rate reflect both the uncapped and capped values for full transparency.

- **Multi-Card Optimization**: For two-card scenarios, the app:
  - Tries all possible valid assignments of eligible categories/groups to each card, especially for cards with group-based rules (e.g., Lady’s, Lady’s Solitaire).
  - Allocates spending to the card that gives the highest reward for each category, up to any caps, and then assigns the remainder to the other card.
  - Handles edge cases where both cards are strong in the same category, ensuring the overall reward is maximized (not just for one card).
  - Ensures that the sum of spending across both cards matches your actual spending (no double-counting).
  - Displays both uncapped and capped rewards/rates in the breakdown if a cap is hit.

### Edge Cases Handled
- **Category/Group Caps**: Cards with per-category or per-group caps (e.g., UOB Lady’s, Lady’s Solitaire, DBS yuu) are handled precisely, with bonus rates applied only up to the cap and base rates after.
- **Group Assignment for Lady’s Cards**: The optimizer tries all possible group assignments for Lady’s and Lady’s Solitaire to find the split that gives the highest total reward, even if it means Lady’s takes a less-contested group.
- **Minimum Spend Tiers**: Cards with minimum spend requirements (e.g., DBS yuu, Trust Cashback) automatically switch to the correct tier and rates based on your input.
- **Reward Capping in Breakdown**: If a card’s monthly reward is capped, the breakdown table and reward rate show both the uncapped and capped values for clarity.
- **Multi-Card Allocation**: No spending is double-counted; each dollar is only assigned to one card, and the allocation is optimized for maximum total reward.
- **Special Card Rules**: Card-specific quirks (e.g., Trust Cashback’s group logic, UOB Visa Signature’s split categories) are implemented as per the latest terms.

## Limitations

Ignores initial bonuses like sign-up bonuses and cashbacks.
2-card comparisons still not fully optimised and a work in progress.

## Current Multi-Card Logic (Technical Outline)

1.  Gather Card and Tier Data
    - For each card, get:
      - The reward rates for each category (from the best tier for the user’s spending).
      - The cap for each tier.
      - Any special logic (e.g., UOB Lady’s: only one eligible category gets the high rate).
2.  Build a Category-to-Card Mapping
    - For each spending category:
      - Identify which of the two cards reward that category, and at what rate.
      - If both reward it, note both rates and caps.
3.  Allocate Spending for Each Category
    - If only one card rewards the category:
      - Assign all spending for that category to that card (up to its cap).
      - If both cards reward the category:
        - Assign as much spending as possible to the higher-rate card (up to its cap), then the remainder to the other card (up to its cap).
      - If both have the same rate:
        - Assign to the card with the higher cap first, or split evenly if both caps are high enough.
      - If neither card rewards the category:
        - Assign to either card at its base rate (if applicable).
4.  Special Handling for UOB Lady’s
    - If UOB Lady’s is one of the cards:
      - Only one eligible group (dining, entertainment, retail, transport, travel) gets the high rate (4 mpd), and it should be the group with the highest spending (that is also eligible).
      - For that group, assign as much spending as possible to UOB Lady’s (up to its cap), then the remainder to the other card.
      - For other groups, UOB Lady’s gets the base rate (0.4 mpd).
5.  Apply Caps
    - For each card, track the total reward and ensure no card exceeds its monthly cap.
    - If a card’s cap is reached, assign any remaining spending in that category to the other card (if possible).
6.  Calculate Rewards and Build Breakdown
    - For each card, sum up the rewards for each category.
    - Build a breakdown for each card showing category, amount assigned, rate, reward.
7.  Return Combined Results
    - Return the total combined reward, and the breakdowns for each card.
