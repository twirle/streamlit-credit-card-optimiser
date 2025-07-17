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

## Limitations

Currently missing out on initial bonuses like sign-up bonuses and cashbacks.
2-card comparisons still slightly buggy and work in progress.
Credit card data still limited on 15 or so cards, to be expanded.

### Current Multi-Card Logic

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
        If both cards reward the category:
      - If one card has a higher rate:
      - Assign as much spending as possible to the higher-rate card (up to its cap), then the remainder to the other card (up to its cap).
      - If both have the same rate: - Assign to the card with the higher cap first, or split evenly if both caps are high enough.
        If neither card rewards the category:
      - Assign to either card at its base rate (if applicable).

4.  Special Handling for UOB Lady’s

    - If UOB Lady’s is one of the cards:

      - Only one eligible category (dining, entertainment, retail, travel) gets the high rate (4 mpd), and it should be the category with the highest spending (that is also eligible).

      - For that category, assign as much spending as possible to UOB Lady’s (up to its cap), then the remainder to the other card.

      - For other categories, UOB Lady’s gets the base rate (0.4 mpd).

5.  Apply Caps

    - For each card, track the total reward and ensure no card exceeds its monthly cap.
    - If a card’s cap is reached, assign any remaining spending in that category to the other card (if possible).

6.  Calculate Rewards and Build Breakdown

    - For each card, sum up the rewards for each category.
    - Build a breakdown for each card showing category, amount assigned, rate, reward.

7.  Return Combined Results

    - Return the total combined reward, and the breakdowns for each card.
