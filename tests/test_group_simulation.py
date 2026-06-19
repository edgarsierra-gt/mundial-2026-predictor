from __future__ import annotations

import pandas as pd

from src.tournament.monte_carlo import simulate_group_probabilities, simulate_tournament_probabilities


def test_group_simulation_exports_probabilities_in_range() -> None:
    teams = pd.DataFrame(
        [
            {"team_id": "A1", "name_es": "A1", "group": "A"},
            {"team_id": "A2", "name_es": "A2", "group": "A"},
            {"team_id": "A3", "name_es": "A3", "group": "A"},
            {"team_id": "A4", "name_es": "A4", "group": "A"},
        ]
    )
    matches_current = pd.DataFrame(
        [
            {
                "match_id": "m1",
                "team_a_id": "A1",
                "team_b_id": "A2",
                "team_a_goals": 1,
                "team_b_goals": 0,
            }
        ]
    )
    upcoming = pd.DataFrame(
        [
            {"match_id": "m2", "team_a_id": "A3", "team_b_id": "A4"},
            {"match_id": "m3", "team_a_id": "A1", "team_b_id": "A3"},
        ]
    )
    predictions = pd.DataFrame(
        [
            {"match_id": "m2", "generated_at": "2026-06-19T00:00:00Z", "lambda_a": 1.2, "lambda_b": 0.9},
            {"match_id": "m3", "generated_at": "2026-06-19T00:00:00Z", "lambda_a": 1.4, "lambda_b": 1.1},
        ]
    )

    probabilities = simulate_group_probabilities(
        teams=teams,
        matches_current=matches_current,
        upcoming_matches=upcoming,
        predictions=predictions,
        n_simulations=25,
        seed=7,
    )

    assert set(probabilities["team_id"]) == {"A1", "A2", "A3", "A4"}
    for column in [
        "prob_group_winner",
        "prob_group_runner_up",
        "prob_qualified_as_third",
        "prob_eliminated_group",
        "prob_advance",
    ]:
        assert probabilities[column].between(0, 1).all()


def test_tournament_simulation_round_totals_are_valid() -> None:
    teams = []
    matches_current = []
    upcoming = []
    predictions = []
    match_index = 1
    for group in "ABCDEFGHIJKL":
        for index in range(1, 5):
            teams.append({"team_id": f"{group}{index}", "name_es": f"{group}{index}", "group": group})
        group_teams = [f"{group}{index}" for index in range(1, 5)]
        for team_a, team_b in [(group_teams[0], group_teams[1]), (group_teams[2], group_teams[3])]:
            match_id = f"m{match_index}"
            upcoming.append({"match_id": match_id, "team_a_id": team_a, "team_b_id": team_b})
            predictions.append(
                {
                    "match_id": match_id,
                    "generated_at": "2026-06-19T00:00:00Z",
                    "lambda_a": 1.0,
                    "lambda_b": 1.0,
                }
            )
            match_index += 1
    team_features = pd.DataFrame(
        [
            {"team_id": team["team_id"], "attack_index": 1.0, "defense_index": 1.0}
            for team in teams
        ]
    )

    _, rounds = simulate_tournament_probabilities(
        teams=pd.DataFrame(teams),
        team_features=team_features,
        matches_current=pd.DataFrame(
            matches_current,
            columns=["match_id", "team_a_id", "team_b_id", "team_a_goals", "team_b_goals"],
        ),
        upcoming_matches=pd.DataFrame(upcoming),
        predictions=pd.DataFrame(predictions),
        n_simulations=20,
        seed=11,
    )

    assert round(float(rounds["prob_round_of_32"].sum()), 6) == 32.0
    assert round(float(rounds["prob_round_of_16"].sum()), 6) == 16.0
    assert round(float(rounds["prob_quarterfinal"].sum()), 6) == 8.0
    assert round(float(rounds["prob_semifinal"].sum()), 6) == 4.0
    assert round(float(rounds["prob_final"].sum()), 6) == 2.0
    assert round(float(rounds["prob_champion"].sum()), 6) == 1.0
