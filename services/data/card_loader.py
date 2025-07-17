import pandas as pd
from pathlib import Path
from models.credit_card_model import CreditCard, CardTier
from typing import List, Dict

CARD_CSV_PATH = Path(__file__).parent.parent.parent / "credit_cards.csv"

CATEGORY_COLUMNS = [
    "Dining Rate", "Groceries Rate", "Petrol Rate", "Transport Rate", "Streaming Rate", "Entertainment Rate", "Utilities Rate", "Retail Rate", "Departmental Rate", "Online Rate", "Travel Rate", "Overseas Rate"
]


def _to_float(val):
    if val is not None and not pd.isna(val):
        try:
            return float(val)
        except Exception:
            return None
    return None

def _to_str(val):
    if val is not None and not pd.isna(val):
        return str(val)
    return ""

def load_cards_and_models() -> List[CreditCard]:
    df = pd.read_csv(CARD_CSV_PATH)
    colset = set(df.columns)
    cards: Dict[str, CreditCard] = {}
    for _, row in df.iterrows():
        name = _to_str(row["Name"])
        issuer = _to_str(row["Issuer"])
        card_type = _to_str(row["Type"])
        income_requirement = None
        if "Income Requirement" in colset:
            val = row["Income Requirement"]
            income_requirement = _to_float(val)
        categories = []
        if "Categories" in colset:
            val = _to_str(row["Categories"])
            if val:
                categories = [c.strip() for c in val.split(",") if c.strip()]
        source = None
        if "Source" in colset:
            val = _to_str(row["Source"])
            if val:
                source = val
        # Build reward rates dict
        reward_rates = {}
        for cat in CATEGORY_COLUMNS:
            if cat in colset:
                val = row[cat]
                fval = _to_float(val)
                if fval is not None:
                    reward_rates[cat.replace(" Rate", "").lower()] = fval
        base_rate = None
        if "Base Rate" in colset:
            val = row["Base Rate"]
            base_rate = _to_float(val)
        min_spend = None
        if "Min Spend" in colset:
            val = row["Min Spend"]
            min_spend = _to_float(val)
        cap = None
        if "Cap" in colset:
            val = row["Cap"]
            cap = _to_float(val)
        description = None
        if "Tier" in colset:
            val = _to_str(row["Tier"])
            if val:
                description = val
        tier = CardTier(
            min_spend=min_spend,
            cap=cap,
            reward_rates=reward_rates,
            base_rate=base_rate,
            description=description
        )
        if name not in cards:
            cards[name] = CreditCard(
                name=name,
                issuer=issuer,
                card_type=card_type,
                income_requirement=income_requirement,
                categories=categories,
                source=source,
                tiers=[tier]
            )
        else:
            cards[name].add_tier(tier)
    return list(cards.values())


def load_card_dataframes() -> Dict[str, pd.DataFrame]:
    df = pd.read_csv(CARD_CSV_PATH)
    # Optionally, build more DataFrames here (e.g., tiers_df, categories_df)
    return {"Cards DataFrame": df}
