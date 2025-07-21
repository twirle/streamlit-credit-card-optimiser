import streamlit as st
from typing import Any, Dict, Optional, Tuple

# --- Session State Keys ---
USER_SPENDING_KEY = "user_spending_data"
MILES_VALUE_CENTS_KEY = "miles_value_cents"
MILES_TO_SGD_RATE_KEY = "miles_to_sgd_rate"
SELECTED_CARD_DISPLAY_KEY = "selected_card_display"
SELECTED_MULTI_CARD1_KEY = "selected_multi_card1"
SELECTED_MULTI_CARD2_KEY = "selected_multi_card2"

# --- Getters/Setters ---


def get_user_spending() -> Dict[str, float]:
    """Get the user's spending data from session state."""
    return st.session_state.get(USER_SPENDING_KEY, {})


def set_user_spending(data: Dict[str, float]) -> None:
    """Set the user's spending data in session state."""
    st.session_state[USER_SPENDING_KEY] = data


def get_selected_card_display() -> Optional[str]:
    """Get the selected card display string for breakdown from session state."""
    return st.session_state.get(SELECTED_CARD_DISPLAY_KEY)


def set_selected_card_display(value: str) -> None:
    """Set the selected card display string for breakdown in session state."""
    st.session_state[SELECTED_CARD_DISPLAY_KEY] = value


def get_selected_multi_cards() -> Tuple[Optional[str], Optional[str]]:
    """Get the selected card names for the multi-card breakdown from session state."""
    return (
        st.session_state.get(SELECTED_MULTI_CARD1_KEY),
        st.session_state.get(SELECTED_MULTI_CARD2_KEY)
    )


def set_selected_multi_cards(card1: str, card2: str) -> None:
    """Set the selected card names for the multi-card breakdown in session state."""
    st.session_state[SELECTED_MULTI_CARD1_KEY] = card1
    st.session_state[SELECTED_MULTI_CARD2_KEY] = card2

# --- Initialization helpers ---


def initialize_spending_state(defaults: Dict[str, float]) -> None:
    """Initialize user spending and related session state keys if not already set."""
    if USER_SPENDING_KEY not in st.session_state:
        st.session_state[USER_SPENDING_KEY] = defaults.copy()
    if MILES_VALUE_CENTS_KEY not in st.session_state:
        st.session_state[MILES_VALUE_CENTS_KEY] = 2.0
    if MILES_TO_SGD_RATE_KEY not in st.session_state:
        st.session_state[MILES_TO_SGD_RATE_KEY] = 0.02
