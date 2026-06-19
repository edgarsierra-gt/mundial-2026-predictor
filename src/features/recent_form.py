from __future__ import annotations

from math import exp, log

import pandas as pd

from src.config import HALF_LIFE_DAYS, MATCH_TYPE_WEIGHTS


def recency_weight(match_date: object, reference_date: pd.Timestamp | None = None) -> float:
    if reference_date is None:
        reference_date = pd.Timestamp.utcnow().tz_localize(None)
    parsed = pd.to_datetime(match_date, errors="coerce")
    if pd.isna(parsed):
        return 0.50
    days = max((reference_date - parsed).days, 0)
    return exp(-log(2) * days / HALF_LIFE_DAYS)


def match_type_weight(match_type: object) -> float:
    text = str(match_type or "unknown").strip().lower()
    return MATCH_TYPE_WEIGHTS.get(text, MATCH_TYPE_WEIGHTS["unknown"])


def add_history_weights(history: pd.DataFrame) -> pd.DataFrame:
    df = history.copy()
    reference = pd.Timestamp.utcnow().tz_localize(None)
    df["recency_weight"] = df["date"].apply(lambda value: recency_weight(value, reference))
    df["match_type_weight"] = df["match_type"].apply(match_type_weight)
    df["match_weight"] = df["recency_weight"] * df["match_type_weight"]
    return df

