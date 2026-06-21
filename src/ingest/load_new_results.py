from __future__ import annotations

import pandas as pd

NEW_RESULTS_COLUMNS = [
    "date",
    "team_a_id",
    "team_b_id",
    "team_a_goals",
    "team_b_goals",
    "team_a_possession",
    "team_b_possession",
    "team_a_shots",
    "team_b_shots",
    "team_a_shots_on_target",
    "team_b_shots_on_target",
    "team_a_xg",
    "team_b_xg",
    "team_a_corners",
    "team_b_corners",
    "team_a_yellow_cards",
    "team_b_yellow_cards",
    "team_a_red_cards",
    "team_b_red_cards",
    "team_a_formation",
    "team_b_formation",
    "source_url",
]

REQUIRED_COLUMNS = ["date", "team_a_id", "team_b_id", "team_a_goals", "team_b_goals"]

MATCHES_CURRENT_COLUMNS = [
    "match_id",
    "match_no",
    "date",
    "group",
    "team_a_id",
    "team_a_name",
    "team_a_goals",
    "team_b_id",
    "team_b_name",
    "team_b_goals",
    "total_goals",
    "goal_diff",
    "winner_team_id",
    "result_1x2",
    "team_a_possession",
    "team_b_possession",
    "team_a_shots",
    "team_b_shots",
    "team_a_shots_on_target",
    "team_b_shots_on_target",
    "team_a_xg",
    "team_b_xg",
    "total_xg",
    "xg_diff",
    "team_a_big_chances",
    "team_b_big_chances",
    "team_a_corners",
    "team_b_corners",
    "team_a_yellow_cards",
    "team_b_yellow_cards",
    "team_a_red_cards",
    "team_b_red_cards",
    "team_a_formation",
    "team_b_formation",
    "source_url",
    "data_status",
]


def empty_new_results_template() -> pd.DataFrame:
    return pd.DataFrame(columns=NEW_RESULTS_COLUMNS)


def _optional(row: pd.Series, column: str):
    value = row.get(column)
    return None if value is None or pd.isna(value) else value


def _find_upcoming_row(upcoming: pd.DataFrame, date: str, team_a_id: str, team_b_id: str):
    same_order = upcoming[
        (upcoming["date"] == date) & (upcoming["team_a_id"] == team_a_id) & (upcoming["team_b_id"] == team_b_id)
    ]
    if not same_order.empty:
        return same_order.iloc[0], False

    swapped_order = upcoming[
        (upcoming["date"] == date) & (upcoming["team_a_id"] == team_b_id) & (upcoming["team_b_id"] == team_a_id)
    ]
    if not swapped_order.empty:
        return swapped_order.iloc[0], True

    return None, False


def _derive_result(goals_a: int, goals_b: int, team_a_id: str, team_b_id: str) -> tuple[str, str | None]:
    if goals_a > goals_b:
        return "1", team_a_id
    if goals_a < goals_b:
        return "2", team_b_id
    return "X", None


def ingest_new_results(
    new_results: pd.DataFrame,
    upcoming: pd.DataFrame,
    matches_current: pd.DataFrame,
    teams: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict]]:
    """Fold finished matches reported in `new_results` into `matches_current`,
    preserving the team_a/team_b orientation already frozen in `upcoming`
    (and therefore in predictions_frozen.csv), and remove the matched rows
    from `upcoming` so they stop appearing as "today/upcoming" predictions.

    Returns (updated_matches_current, updated_upcoming, unmatched_new_results, ingested_summary).
    """
    teams_by_id = teams.set_index("team_id").to_dict(orient="index")
    upcoming = upcoming.copy()

    appended_rows = []
    matched_index_labels = []
    unmatched_positions = []
    summary = []

    for position in new_results.index:
        row = new_results.loc[position]
        date = str(row["date"]).strip()
        team_a_id = str(row["team_a_id"]).strip().upper()
        team_b_id = str(row["team_b_id"]).strip().upper()
        goals_a = int(row["team_a_goals"])
        goals_b = int(row["team_b_goals"])

        match, swapped = _find_upcoming_row(upcoming, date, team_a_id, team_b_id)
        if match is None:
            unmatched_positions.append(position)
            continue

        if swapped:
            goals_a, goals_b = goals_b, goals_a
        team_a_id, team_b_id = match["team_a_id"], match["team_b_id"]

        result_1x2, winner_team_id = _derive_result(goals_a, goals_b, team_a_id, team_b_id)
        team_a_name = teams_by_id.get(team_a_id, {}).get("name_es", team_a_id)
        team_b_name = teams_by_id.get(team_b_id, {}).get("name_es", team_b_id)

        team_a_xg = _optional(row, "team_a_xg")
        team_b_xg = _optional(row, "team_b_xg")
        has_both_xg = team_a_xg is not None and team_b_xg is not None

        appended_rows.append(
            {
                "match_id": match["match_id"],
                "match_no": None,
                "date": date,
                "group": match.get("group"),
                "team_a_id": team_a_id,
                "team_a_name": team_a_name,
                "team_a_goals": goals_a,
                "team_b_id": team_b_id,
                "team_b_name": team_b_name,
                "team_b_goals": goals_b,
                "total_goals": goals_a + goals_b,
                "goal_diff": abs(goals_a - goals_b),
                "winner_team_id": winner_team_id,
                "result_1x2": result_1x2,
                "team_a_possession": _optional(row, "team_a_possession"),
                "team_b_possession": _optional(row, "team_b_possession"),
                "team_a_shots": _optional(row, "team_a_shots"),
                "team_b_shots": _optional(row, "team_b_shots"),
                "team_a_shots_on_target": _optional(row, "team_a_shots_on_target"),
                "team_b_shots_on_target": _optional(row, "team_b_shots_on_target"),
                "team_a_xg": team_a_xg,
                "team_b_xg": team_b_xg,
                "total_xg": (team_a_xg + team_b_xg) if has_both_xg else None,
                "xg_diff": (team_a_xg - team_b_xg) if has_both_xg else None,
                "team_a_big_chances": None,
                "team_b_big_chances": None,
                "team_a_corners": _optional(row, "team_a_corners"),
                "team_b_corners": _optional(row, "team_b_corners"),
                "team_a_yellow_cards": _optional(row, "team_a_yellow_cards"),
                "team_b_yellow_cards": _optional(row, "team_b_yellow_cards"),
                "team_a_red_cards": _optional(row, "team_a_red_cards"),
                "team_b_red_cards": _optional(row, "team_b_red_cards"),
                "team_a_formation": _optional(row, "team_a_formation"),
                "team_b_formation": _optional(row, "team_b_formation"),
                "source_url": _optional(row, "source_url"),
                "data_status": "verified",
            }
        )
        matched_index_labels.append(match.name)
        summary.append(
            {
                "match_id": match["match_id"],
                "label": f"{team_a_name} {goals_a}-{goals_b} {team_b_name}",
            }
        )

    if appended_rows:
        matches_current = pd.concat(
            [matches_current, pd.DataFrame(appended_rows, columns=MATCHES_CURRENT_COLUMNS)],
            ignore_index=True,
        )
    if matched_index_labels:
        upcoming = upcoming.drop(index=matched_index_labels).reset_index(drop=True)

    unmatched = new_results.loc[unmatched_positions].reset_index(drop=True)
    return matches_current, upcoming, unmatched, summary
