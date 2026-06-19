from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

from src.config import MODEL_VERSION, N_SIMULATIONS, RANDOM_SEED
from src.model.poisson import score_matrix
from src.tournament.bracket import simulate_bracket
from src.tournament.groups import completed_group_table


def _prediction_lookup(predictions: pd.DataFrame) -> dict[str, dict[str, float]]:
    if predictions.empty:
        return {}
    latest = predictions.sort_values("generated_at").drop_duplicates("match_id", keep="last")
    return {
        str(row.match_id): {
            "lambda_a": float(row.lambda_a),
            "lambda_b": float(row.lambda_b),
        }
        for row in latest.itertuples()
    }


def _score_distributions(
    upcoming_matches: pd.DataFrame,
    predictions: pd.DataFrame,
) -> dict[str, dict[str, Any]]:
    lookup = _prediction_lookup(predictions)
    distributions: dict[str, dict[str, Any]] = {}
    for row in upcoming_matches.itertuples():
        prediction = lookup.get(str(row.match_id))
        if prediction is None:
            continue
        matrix = score_matrix(prediction["lambda_a"], prediction["lambda_b"])
        distributions[str(row.match_id)] = {
            "team_a_id": str(row.team_a_id),
            "team_b_id": str(row.team_b_id),
            "scores": matrix[["goals_a", "goals_b"]].to_numpy(dtype=int),
            "probabilities": matrix["probability"].to_numpy(dtype=float),
        }
    return distributions


def simulate_group_probabilities(
    teams: pd.DataFrame,
    matches_current: pd.DataFrame,
    upcoming_matches: pd.DataFrame,
    predictions: pd.DataFrame,
    n_simulations: int = N_SIMULATIONS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    if n_simulations <= 0:
        raise ValueError("n_simulations must be positive")

    rng = np.random.default_rng(seed)
    distributions = _score_distributions(upcoming_matches, predictions)
    if not distributions:
        raise ValueError("No score distributions available for simulation")

    counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    upcoming_ids = list(distributions.keys())

    for _ in range(n_simulations):
        simulated_results = []
        for match_id in upcoming_ids:
            distribution = distributions[match_id]
            sample_idx = int(rng.choice(len(distribution["scores"]), p=distribution["probabilities"]))
            goals_a, goals_b = distribution["scores"][sample_idx]
            simulated_results.append(
                (
                    distribution["team_a_id"],
                    distribution["team_b_id"],
                    int(goals_a),
                    int(goals_b),
                )
            )

        classified = completed_group_table(teams, matches_current, simulated_results)
        for row in classified.itertuples():
            team_counter = counters[str(row.team_id)]
            if int(row.rank_current) == 1:
                team_counter["group_winner"] += 1
            if int(row.rank_current) == 2:
                team_counter["group_runner_up"] += 1
            if bool(row.qualified_as_third):
                team_counter["qualified_as_third"] += 1
            if bool(row.qualified_group):
                team_counter["advanced"] += 1
            if bool(row.eliminated_group):
                team_counter["eliminated"] += 1

    team_names = teams.set_index("team_id")["name_es"].to_dict()
    team_groups = teams.set_index("team_id")["group"].to_dict()
    rows = []
    for team_id in sorted(counters):
        counter = counters[team_id]
        rows.append(
            {
                "team_id": team_id,
                "name": team_names.get(team_id, team_id),
                "group": team_groups.get(team_id),
                "prob_group_winner": counter["group_winner"] / n_simulations,
                "prob_group_runner_up": counter["group_runner_up"] / n_simulations,
                "prob_qualified_as_third": counter["qualified_as_third"] / n_simulations,
                "prob_eliminated_group": counter["eliminated"] / n_simulations,
                "prob_advance": counter["advanced"] / n_simulations,
                "model_version": MODEL_VERSION,
                "n_simulations": n_simulations,
            }
        )
    return pd.DataFrame(rows).sort_values(["group", "prob_advance", "team_id"], ascending=[True, False, True])


def simulate_tournament_probabilities(
    teams: pd.DataFrame,
    team_features: pd.DataFrame,
    matches_current: pd.DataFrame,
    upcoming_matches: pd.DataFrame,
    predictions: pd.DataFrame,
    n_simulations: int = N_SIMULATIONS,
    seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if n_simulations <= 0:
        raise ValueError("n_simulations must be positive")

    rng = np.random.default_rng(seed)
    distributions = _score_distributions(upcoming_matches, predictions)
    if not distributions:
        raise ValueError("No score distributions available for simulation")

    group_counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    round_counters: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    upcoming_ids = list(distributions.keys())
    bracket_cache: dict[tuple[str, str], dict[str, Any]] = {}

    for _ in range(n_simulations):
        simulated_results = []
        for match_id in upcoming_ids:
            distribution = distributions[match_id]
            sample_idx = int(rng.choice(len(distribution["scores"]), p=distribution["probabilities"]))
            goals_a, goals_b = distribution["scores"][sample_idx]
            simulated_results.append(
                (
                    distribution["team_a_id"],
                    distribution["team_b_id"],
                    int(goals_a),
                    int(goals_b),
                )
            )

        classified = completed_group_table(teams, matches_current, simulated_results)
        for row in classified.itertuples():
            team_id = str(row.team_id)
            team_counter = group_counters[team_id]
            if int(row.rank_current) == 1:
                team_counter["group_winner"] += 1
            if int(row.rank_current) == 2:
                team_counter["group_runner_up"] += 1
            if bool(row.qualified_as_third):
                team_counter["qualified_as_third"] += 1
            if bool(row.qualified_group):
                team_counter["advanced"] += 1
            if bool(row.eliminated_group):
                team_counter["eliminated"] += 1

        bracket = simulate_bracket(classified, team_features, rng, bracket_cache)
        for team_id in bracket["round_of_32"]:
            round_counters[str(team_id)]["round_of_32"] += 1
        for team_id in bracket["round_of_16"]:
            round_counters[str(team_id)]["round_of_16"] += 1
        for team_id in bracket["quarterfinal"]:
            round_counters[str(team_id)]["quarterfinal"] += 1
        for team_id in bracket["semifinal"]:
            round_counters[str(team_id)]["semifinal"] += 1
        for team_id in bracket["final"]:
            round_counters[str(team_id)]["final"] += 1
        round_counters[str(bracket["champion"])]["champion"] += 1

    team_names = teams.set_index("team_id")["name_es"].to_dict()
    team_groups = teams.set_index("team_id")["group"].to_dict()
    group_rows = []
    round_rows = []
    for team_id in sorted(teams["team_id"].astype(str).tolist()):
        group_counter = group_counters[team_id]
        round_counter = round_counters[team_id]
        group_rows.append(
            {
                "team_id": team_id,
                "name": team_names.get(team_id, team_id),
                "group": team_groups.get(team_id),
                "prob_group_winner": group_counter["group_winner"] / n_simulations,
                "prob_group_runner_up": group_counter["group_runner_up"] / n_simulations,
                "prob_qualified_as_third": group_counter["qualified_as_third"] / n_simulations,
                "prob_eliminated_group": group_counter["eliminated"] / n_simulations,
                "prob_advance": group_counter["advanced"] / n_simulations,
                "model_version": MODEL_VERSION,
                "n_simulations": n_simulations,
            }
        )
        round_rows.append(
            {
                "team_id": team_id,
                "name": team_names.get(team_id, team_id),
                "group": team_groups.get(team_id),
                "prob_round_of_32": round_counter["round_of_32"] / n_simulations,
                "prob_round_of_16": round_counter["round_of_16"] / n_simulations,
                "prob_quarterfinal": round_counter["quarterfinal"] / n_simulations,
                "prob_semifinal": round_counter["semifinal"] / n_simulations,
                "prob_final": round_counter["final"] / n_simulations,
                "prob_champion": round_counter["champion"] / n_simulations,
                "model_version": MODEL_VERSION,
                "n_simulations": n_simulations,
                "bracket_mode": "approximate_stable_seed",
            }
        )

    group_probabilities = pd.DataFrame(group_rows).sort_values(
        ["group", "prob_advance", "team_id"],
        ascending=[True, False, True],
    )
    round_probabilities = pd.DataFrame(round_rows).sort_values(
        ["prob_champion", "prob_final", "prob_semifinal", "team_id"],
        ascending=[False, False, False, True],
    )
    return group_probabilities, round_probabilities
