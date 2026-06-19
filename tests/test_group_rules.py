from __future__ import annotations

import pandas as pd

from src.tournament.rules import (
    apply_match,
    classify_teams,
    direct_qualifiers,
    empty_standings,
    rank_standings,
    standings_to_frame,
    third_place_qualifiers,
)


def _teams() -> pd.DataFrame:
    rows = []
    for group in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]:
        for index in range(1, 5):
            rows.append({"team_id": f"{group}{index}", "group": group})
    return pd.DataFrame(rows)


def test_apply_match_updates_points_and_goal_difference() -> None:
    standings = empty_standings(pd.DataFrame([{"team_id": "A1", "group": "A"}, {"team_id": "A2", "group": "A"}]))

    apply_match(standings, "A1", "A2", 3, 1)

    assert standings["A1"].points == 3
    assert standings["A1"].wins == 1
    assert standings["A1"].goal_difference == 2
    assert standings["A2"].losses == 1
    assert standings["A2"].goal_difference == -2


def test_draw_updates_both_teams_with_one_point() -> None:
    standings = empty_standings(pd.DataFrame([{"team_id": "A1", "group": "A"}, {"team_id": "A2", "group": "A"}]))

    apply_match(standings, "A1", "A2", 2, 2)

    assert standings["A1"].points == 1
    assert standings["A2"].points == 1
    assert standings["A1"].draws == 1
    assert standings["A2"].draws == 1


def test_rank_standings_uses_points_goal_difference_goals_for_and_team_id() -> None:
    standings = pd.DataFrame(
        [
            {"group": "A", "team_id": "A2", "points": 4, "goal_difference": 1, "goals_for": 3},
            {"group": "A", "team_id": "A1", "points": 4, "goal_difference": 2, "goals_for": 2},
            {"group": "A", "team_id": "A4", "points": 1, "goal_difference": -1, "goals_for": 1},
            {"group": "A", "team_id": "A3", "points": 4, "goal_difference": 2, "goals_for": 4},
        ]
    )

    ranked = rank_standings(standings)

    assert ranked["team_id"].tolist() == ["A3", "A1", "A2", "A4"]
    assert ranked["rank_current"].tolist() == [1, 2, 3, 4]


def test_direct_qualifiers_and_best_thirds_have_expected_sizes() -> None:
    standings = standings_to_frame(empty_standings(_teams()))
    standings["points"] = standings["team_id"].str.extract(r"(\d)").astype(int)
    standings["goals_for"] = standings["points"]
    standings["goal_difference"] = standings["points"]

    ranked = rank_standings(standings)

    assert len(direct_qualifiers(ranked)) == 24
    assert len(third_place_qualifiers(ranked)) == 8


def test_classify_teams_marks_32_group_qualifiers() -> None:
    standings = standings_to_frame(empty_standings(_teams()))
    standings["points"] = 0
    standings["goals_for"] = 0
    standings["goal_difference"] = 0

    classified = classify_teams(rank_standings(standings))

    assert int(classified["qualified_direct"].sum()) == 24
    assert int(classified["qualified_as_third"].sum()) == 8
    assert int(classified["qualified_group"].sum()) == 32
