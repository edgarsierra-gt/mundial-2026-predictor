from __future__ import annotations

from math import exp, factorial

import pandas as pd

from src.config import LAMBDA_MAX, LAMBDA_MIN, MAX_GOALS_MATRIX, RHO_DIXON_COLES
from src.model.dixon_coles import low_score_adjustment


def clamp_lambda(value: float) -> float:
    return min(max(float(value), LAMBDA_MIN), LAMBDA_MAX)


def poisson_pmf(k: int, lam: float) -> float:
    return (lam**k * exp(-lam)) / factorial(k)


def score_matrix(lambda_a: float, lambda_b: float, max_goals: int = MAX_GOALS_MATRIX) -> pd.DataFrame:
    lambda_a = clamp_lambda(lambda_a)
    lambda_b = clamp_lambda(lambda_b)
    rows = []
    for goals_a in range(max_goals + 1):
        for goals_b in range(max_goals + 1):
            probability = poisson_pmf(goals_a, lambda_a) * poisson_pmf(goals_b, lambda_b)
            probability *= low_score_adjustment(goals_a, goals_b, lambda_a, lambda_b, RHO_DIXON_COLES)
            rows.append({"goals_a": goals_a, "goals_b": goals_b, "probability": probability})
    matrix = pd.DataFrame(rows)
    total = float(matrix["probability"].sum())
    if total <= 0:
        raise ValueError("Score matrix has zero probability mass")
    matrix["probability"] = matrix["probability"] / total
    return matrix


def outcome_probabilities(matrix: pd.DataFrame) -> dict[str, float]:
    prob_a = float(matrix.loc[matrix["goals_a"] > matrix["goals_b"], "probability"].sum())
    prob_draw = float(matrix.loc[matrix["goals_a"] == matrix["goals_b"], "probability"].sum())
    prob_b = float(matrix.loc[matrix["goals_a"] < matrix["goals_b"], "probability"].sum())
    total = prob_a + prob_draw + prob_b
    return {
        "team_a_win": prob_a / total,
        "draw": prob_draw / total,
        "team_b_win": prob_b / total,
    }


def top_scores(matrix: pd.DataFrame, n: int = 5) -> list[dict[str, float | str]]:
    ordered = matrix.sort_values("probability", ascending=False).head(n)
    return [
        {
            "score": f"{int(row.goals_a)}-{int(row.goals_b)}",
            "probability": round(float(row.probability), 6),
        }
        for row in ordered.itertuples()
    ]

