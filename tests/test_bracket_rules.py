from __future__ import annotations

import numpy as np
import pandas as pd

from src.tournament.bracket import approximate_bracket_seed, first_round_pairs, simulate_bracket


def _classified_32() -> pd.DataFrame:
    rows = []
    for group in "ABCDEFGHIJKL":
        rows.append(
            {
                "team_id": f"{group}1",
                "group": group,
                "rank_current": 1,
                "points": 6,
                "goal_difference": 3,
                "goals_for": 4,
                "qualified_group": True,
                "qualified_as_third": False,
            }
        )
        rows.append(
            {
                "team_id": f"{group}2",
                "group": group,
                "rank_current": 2,
                "points": 4,
                "goal_difference": 1,
                "goals_for": 3,
                "qualified_group": True,
                "qualified_as_third": False,
            }
        )
        rows.append(
            {
                "team_id": f"{group}3",
                "group": group,
                "rank_current": 3,
                "points": 3,
                "goal_difference": 0,
                "goals_for": 2,
                "qualified_group": group <= "H",
                "qualified_as_third": group <= "H",
            }
        )
        rows.append(
            {
                "team_id": f"{group}4",
                "group": group,
                "rank_current": 4,
                "points": 0,
                "goal_difference": -4,
                "goals_for": 1,
                "qualified_group": False,
                "qualified_as_third": False,
            }
        )
    return pd.DataFrame(rows)


def _team_features(classified: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "team_id": row.team_id,
                "attack_index": 1.0,
                "defense_index": 1.0,
            }
            for row in classified.itertuples()
        ]
    )


def test_approximate_bracket_seed_has_32_unique_teams() -> None:
    seeded = approximate_bracket_seed(_classified_32())

    assert len(seeded) == 32
    assert len(set(seeded)) == 32


def test_first_round_pairs_creates_16_pairs_without_duplicates() -> None:
    seeded = approximate_bracket_seed(_classified_32())
    pairs = first_round_pairs(seeded)
    flattened = [team for pair in pairs for team in pair]

    assert len(pairs) == 16
    assert len(flattened) == 32
    assert len(set(flattened)) == 32


def test_simulate_bracket_round_sizes_are_valid() -> None:
    classified = _classified_32()
    result = simulate_bracket(classified, _team_features(classified), np.random.default_rng(1))

    assert len(result["round_of_32"]) == 32
    assert len(result["round_of_16"]) == 16
    assert len(result["quarterfinal"]) == 8
    assert len(result["semifinal"]) == 4
    assert len(result["final"]) == 2
    assert isinstance(result["champion"], str)
