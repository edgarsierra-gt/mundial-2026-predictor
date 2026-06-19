from __future__ import annotations


def low_score_adjustment(goals_a: int, goals_b: int, lambda_a: float, lambda_b: float, rho: float) -> float:
    if rho == 0:
        return 1.0
    if goals_a == 0 and goals_b == 0:
        return 1 - (lambda_a * lambda_b * rho)
    if goals_a == 0 and goals_b == 1:
        return 1 + (lambda_a * rho)
    if goals_a == 1 and goals_b == 0:
        return 1 + (lambda_b * rho)
    if goals_a == 1 and goals_b == 1:
        return 1 - rho
    return 1.0

