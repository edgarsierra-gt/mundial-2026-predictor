from __future__ import annotations

from math import log


RESULT_LABELS = {
    "1": "team_a_win",
    "X": "draw",
    "2": "team_b_win",
    "team_a_win": "team_a_win",
    "draw": "draw",
    "team_b_win": "team_b_win",
}


def normalize_actual_result(actual: str) -> str:
    if actual not in RESULT_LABELS:
        raise ValueError(f"Unknown actual result: {actual}")
    return RESULT_LABELS[actual]


def brier_score(probabilities: dict[str, float], actual: str) -> float:
    actual_label = normalize_actual_result(actual)
    return sum(
        (probabilities[key] - (1 if key == actual_label else 0)) ** 2
        for key in ["team_a_win", "draw", "team_b_win"]
    )


def log_loss(probabilities: dict[str, float], actual: str, epsilon: float = 1e-12) -> float:
    actual_label = normalize_actual_result(actual)
    return -log(max(probabilities[actual_label], epsilon))


def predicted_result(probabilities: dict[str, float]) -> str:
    return max(probabilities, key=probabilities.get)


def exact_score_hit(predicted_score: str | None, team_a_goals: int, team_b_goals: int) -> bool:
    return predicted_score == f"{team_a_goals}-{team_b_goals}"


def goals_error(lambda_a: float, lambda_b: float, total_goals_real: int) -> float:
    return (lambda_a + lambda_b) - total_goals_real
