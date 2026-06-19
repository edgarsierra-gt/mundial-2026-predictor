from __future__ import annotations

from math import log


def brier_score(probabilities: dict[str, float], actual: str) -> float:
    labels = {"1": "team_a_win", "X": "draw", "2": "team_b_win"}
    return sum((probabilities[key] - (1 if key == labels[actual] else 0)) ** 2 for key in labels.values())


def log_loss(probabilities: dict[str, float], actual: str, epsilon: float = 1e-12) -> float:
    labels = {"1": "team_a_win", "X": "draw", "2": "team_b_win"}
    return -log(max(probabilities[labels[actual]], epsilon))

