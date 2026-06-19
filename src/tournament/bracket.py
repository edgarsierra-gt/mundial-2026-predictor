from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.config import G_EFF
from src.model.poisson import clamp_lambda, score_matrix


ROUND_COLUMNS = [
    "reached_round_of_32",
    "reached_round_of_16",
    "reached_quarterfinal",
    "reached_semifinal",
    "reached_final",
    "champion",
]


def approximate_bracket_seed(classified_standings: pd.DataFrame) -> list[str]:
    qualified = classified_standings.loc[classified_standings["qualified_group"]].copy()
    winners = qualified.loc[qualified["rank_current"] == 1].sort_values("group")
    runners_up = qualified.loc[qualified["rank_current"] == 2].sort_values("group")
    thirds = qualified.loc[qualified["qualified_as_third"]].sort_values(
        ["points", "goal_difference", "goals_for", "team_id"],
        ascending=[False, False, False, True],
    )
    seeded = pd.concat([winners, runners_up, thirds], ignore_index=True)
    if len(seeded) != 32:
        raise ValueError(f"Expected 32 qualified teams, got {len(seeded)}")
    return seeded["team_id"].astype(str).tolist()


def first_round_pairs(seeded_teams: list[str]) -> list[tuple[str, str]]:
    if len(seeded_teams) != 32:
        raise ValueError("Round of 32 requires exactly 32 seeded teams")
    return [(seeded_teams[index], seeded_teams[-(index + 1)]) for index in range(16)]


def _team_feature_lookup(team_features: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {
        str(row.team_id): {
            "attack_index": float(row.attack_index),
            "defense_index": float(row.defense_index),
        }
        for row in team_features.itertuples()
    }


def _match_distribution(
    team_a_id: str,
    team_b_id: str,
    features: dict[str, dict[str, float]],
    cache: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    key = (team_a_id, team_b_id)
    if key in cache:
        return cache[key]
    team_a = features[team_a_id]
    team_b = features[team_b_id]
    lambda_a = clamp_lambda((G_EFF / 2) * team_a["attack_index"] * team_b["defense_index"])
    lambda_b = clamp_lambda((G_EFF / 2) * team_b["attack_index"] * team_a["defense_index"])
    matrix = score_matrix(lambda_a, lambda_b)
    payload = {
        "scores": matrix[["goals_a", "goals_b"]].to_numpy(dtype=int),
        "probabilities": matrix["probability"].to_numpy(dtype=float),
        "advance_a_if_draw": _advance_probability_if_draw(lambda_a, lambda_b),
    }
    cache[key] = payload
    return payload


def _advance_probability_if_draw(lambda_a: float, lambda_b: float) -> float:
    total = lambda_a + lambda_b
    if total <= 0:
        return 0.5
    return min(max(lambda_a / total, 0.05), 0.95)


def simulate_knockout_match(
    team_a_id: str,
    team_b_id: str,
    features: dict[str, dict[str, float]],
    rng: np.random.Generator,
    cache: dict[tuple[str, str], dict[str, Any]],
) -> str:
    distribution = _match_distribution(team_a_id, team_b_id, features, cache)
    sample_idx = int(rng.choice(len(distribution["scores"]), p=distribution["probabilities"]))
    goals_a, goals_b = distribution["scores"][sample_idx]
    if goals_a > goals_b:
        return team_a_id
    if goals_b > goals_a:
        return team_b_id
    return team_a_id if rng.random() < distribution["advance_a_if_draw"] else team_b_id


def simulate_bracket(
    classified_standings: pd.DataFrame,
    team_features: pd.DataFrame,
    rng: np.random.Generator,
    cache: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, list[str] | str]:
    cache = cache if cache is not None else {}
    features = _team_feature_lookup(team_features)
    seeded = approximate_bracket_seed(classified_standings)
    round_of_32 = seeded

    current_pairs = first_round_pairs(round_of_32)
    round_of_16 = [
        simulate_knockout_match(team_a, team_b, features, rng, cache)
        for team_a, team_b in current_pairs
    ]
    quarterfinal = _simulate_round(round_of_16, features, rng, cache)
    semifinal = _simulate_round(quarterfinal, features, rng, cache)
    final = _simulate_round(semifinal, features, rng, cache)
    champion = _simulate_round(final, features, rng, cache)[0]

    return {
        "round_of_32": round_of_32,
        "round_of_16": round_of_16,
        "quarterfinal": quarterfinal,
        "semifinal": semifinal,
        "final": final,
        "champion": champion,
    }


def _simulate_round(
    teams: list[str],
    features: dict[str, dict[str, float]],
    rng: np.random.Generator,
    cache: dict[tuple[str, str], dict[str, Any]],
) -> list[str]:
    if len(teams) % 2 != 0:
        raise ValueError("Knockout rounds require an even number of teams")
    winners = []
    for index in range(0, len(teams), 2):
        winners.append(simulate_knockout_match(teams[index], teams[index + 1], features, rng, cache))
    return winners
