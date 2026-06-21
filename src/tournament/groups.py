from __future__ import annotations

import pandas as pd

from src.tournament.rules import apply_match, classify_teams, empty_standings, rank_standings, standings_to_frame


def build_tournament_schedule(matches_current: pd.DataFrame, upcoming_matches: pd.DataFrame) -> pd.DataFrame:
    known_match_no = [int(value) for value in matches_current.get("match_no", []) if pd.notna(value)]
    next_completed_no = max(known_match_no, default=0) + 1

    completed_rows = []
    for row in matches_current.itertuples():
        # Results ingested via 00_ingest_results.py leave match_no blank on
        # purpose, so match_id stays identical to the one already frozen in
        # predictions_frozen.csv. Assign a display-only sequential number here.
        if pd.notna(row.match_no):
            match_no = int(row.match_no)
        else:
            match_no = next_completed_no
            next_completed_no += 1
        completed_rows.append(
            {
                "match_id": row.match_id,
                "match_no": match_no,
                "stage": "group",
                "group": row.group,
                "date": row.date,
                "team_a_id": row.team_a_id,
                "team_b_id": row.team_b_id,
                "status": "completed",
                "winner_advances_to": None,
                "loser_advances_to": None,
                "source_url": getattr(row, "source_url", None),
            }
        )

    next_match_no = max([item["match_no"] for item in completed_rows], default=0) + 1
    scheduled_rows = []
    for offset, row in enumerate(upcoming_matches.itertuples()):
        scheduled_rows.append(
            {
                "match_id": row.match_id,
                "match_no": next_match_no + offset,
                "stage": "group",
                "group": row.group,
                "date": row.date,
                "team_a_id": row.team_a_id,
                "team_b_id": row.team_b_id,
                "status": getattr(row, "status", "scheduled"),
                "winner_advances_to": None,
                "loser_advances_to": None,
                "source_url": getattr(row, "source_url", None),
            }
        )

    return pd.DataFrame(completed_rows + scheduled_rows)


def build_match_results_real(matches_current: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for row in matches_current.itertuples():
        if int(row.team_a_goals) > int(row.team_b_goals):
            actual_result = "team_a_win"
        elif int(row.team_a_goals) == int(row.team_b_goals):
            actual_result = "draw"
        else:
            actual_result = "team_b_win"
        rows.append(
            {
                "match_id": row.match_id,
                "date": row.date,
                "team_a_id": row.team_a_id,
                "team_b_id": row.team_b_id,
                "team_a_goals": int(row.team_a_goals),
                "team_b_goals": int(row.team_b_goals),
                "actual_result": actual_result,
                "total_goals_real": int(row.team_a_goals) + int(row.team_b_goals),
                "source_url": getattr(row, "source_url", None),
                "verified_at": pd.Timestamp.utcnow().isoformat(),
                "data_status": getattr(row, "data_status", "verified"),
            }
        )
    return pd.DataFrame(rows)


def build_current_standings(teams: pd.DataFrame, matches_current: pd.DataFrame) -> pd.DataFrame:
    standings = empty_standings(teams)
    for row in matches_current.itertuples():
        apply_match(
            standings,
            str(row.team_a_id),
            str(row.team_b_id),
            int(row.team_a_goals),
            int(row.team_b_goals),
        )
    ranked = rank_standings(standings_to_frame(standings))
    ranked["status"] = "active"
    ranked["updated_at"] = pd.Timestamp.utcnow().isoformat()
    return ranked


def completed_group_table(
    teams: pd.DataFrame,
    matches_current: pd.DataFrame,
    simulated_results: list[tuple[str, str, int, int]],
) -> pd.DataFrame:
    standings = empty_standings(teams)
    for row in matches_current.itertuples():
        apply_match(
            standings,
            str(row.team_a_id),
            str(row.team_b_id),
            int(row.team_a_goals),
            int(row.team_b_goals),
        )
    for team_a_id, team_b_id, team_a_goals, team_b_goals in simulated_results:
        apply_match(standings, team_a_id, team_b_id, team_a_goals, team_b_goals)
    return classify_teams(rank_standings(standings_to_frame(standings)))
