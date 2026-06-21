from __future__ import annotations

import pandas as pd

from src.ingest.load_new_results import ingest_new_results

EMPTY_MATCHES_CURRENT = pd.DataFrame(
    columns=["match_id", "date", "team_a_id", "team_b_id", "team_a_goals", "team_b_goals"]
)


def _teams() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"team_id": "USA", "name_es": "Estados Unidos"},
            {"team_id": "AUS", "name_es": "Australia"},
        ]
    )


def _upcoming() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": "2026-06-19_USA_AUS",
                "date": "2026-06-19",
                "time_local": "1:00 PM",
                "group": "D",
                "team_a_id": "USA",
                "team_b_id": "AUS",
                "team_a_name": "Estados Unidos",
                "team_b_name": "Australia",
                "status": "scheduled",
                "venue": "Lumen Field",
                "source_url": "manual_user_provided_2026-06-19",
            }
        ]
    )


def test_ingest_matches_same_orientation_and_removes_from_upcoming() -> None:
    new_results = pd.DataFrame(
        [{"date": "2026-06-19", "team_a_id": "USA", "team_b_id": "AUS", "team_a_goals": 1, "team_b_goals": 2}]
    )

    matches_current, upcoming, remaining, summary = ingest_new_results(
        new_results, _upcoming(), EMPTY_MATCHES_CURRENT, _teams()
    )

    assert upcoming.empty
    assert remaining.empty
    assert len(summary) == 1

    row = matches_current.iloc[0]
    assert row["match_id"] == "2026-06-19_USA_AUS"
    assert row["team_a_goals"] == 1
    assert row["team_b_goals"] == 2
    assert row["winner_team_id"] == "AUS"
    assert row["result_1x2"] == "2"
    assert row["data_status"] == "verified"


def test_ingest_flips_goals_when_teams_reported_in_reverse_order() -> None:
    new_results = pd.DataFrame(
        [{"date": "2026-06-19", "team_a_id": "AUS", "team_b_id": "USA", "team_a_goals": 2, "team_b_goals": 1}]
    )

    matches_current, upcoming, remaining, summary = ingest_new_results(
        new_results, _upcoming(), EMPTY_MATCHES_CURRENT, _teams()
    )

    row = matches_current.iloc[0]
    assert row["team_a_id"] == "USA"
    assert row["team_a_goals"] == 1
    assert row["team_b_id"] == "AUS"
    assert row["team_b_goals"] == 2
    assert upcoming.empty


def test_unmatched_result_is_kept_for_retry_instead_of_dropped() -> None:
    new_results = pd.DataFrame(
        [{"date": "2026-06-19", "team_a_id": "ZZZ", "team_b_id": "AUS", "team_a_goals": 1, "team_b_goals": 0}]
    )

    matches_current, upcoming, remaining, summary = ingest_new_results(
        new_results, _upcoming(), EMPTY_MATCHES_CURRENT, _teams()
    )

    assert summary == []
    assert matches_current.empty
    assert len(upcoming) == 1
    assert len(remaining) == 1
    assert remaining.iloc[0]["team_a_id"] == "ZZZ"


def test_optional_stat_columns_are_blank_when_not_provided() -> None:
    new_results = pd.DataFrame(
        [{"date": "2026-06-19", "team_a_id": "USA", "team_b_id": "AUS", "team_a_goals": 1, "team_b_goals": 2}]
    )

    matches_current, _, _, _ = ingest_new_results(new_results, _upcoming(), EMPTY_MATCHES_CURRENT, _teams())

    row = matches_current.iloc[0]
    assert row["team_a_xg"] is None
    assert row["total_xg"] is None
