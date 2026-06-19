from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import CURRENT_WORLD_CUP_XLSX, PROCESSED_DIR, TEAM_HISTORY_XLSX
from src.features.team_strength import build_team_features
from src.ingest.load_team_history import load_team_history
from src.ingest.load_worldcup_current import load_current_workbook


def _merge_teams(current_teams: pd.DataFrame, history_teams: pd.DataFrame) -> pd.DataFrame:
    teams = pd.concat([current_teams, history_teams], ignore_index=True)
    teams = teams.sort_values("group", na_position="last")
    teams = teams.drop_duplicates("team_id", keep="first")
    return teams.sort_values("team_id").reset_index(drop=True)


def _build_upcoming_template(teams: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "match_id",
            "date",
            "time_local",
            "group",
            "team_a_id",
            "team_b_id",
            "team_a_name",
            "team_b_name",
            "status",
            "venue",
            "source_url",
        ]
    )


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    if not CURRENT_WORLD_CUP_XLSX.exists():
        raise FileNotFoundError(f"Missing current World Cup workbook: {CURRENT_WORLD_CUP_XLSX}")
    if not TEAM_HISTORY_XLSX.exists():
        raise FileNotFoundError(f"Missing team history workbook: {TEAM_HISTORY_XLSX}")

    matches_current, team_match_current, current_teams = load_current_workbook(CURRENT_WORLD_CUP_XLSX)
    team_history, history_teams = load_team_history(TEAM_HISTORY_XLSX)
    teams = _merge_teams(current_teams, history_teams)
    team_features = build_team_features(teams, team_history, team_match_current)

    upcoming_path = PROCESSED_DIR / "upcoming_matches.csv"
    if upcoming_path.exists():
        upcoming_matches = pd.read_csv(upcoming_path)
    else:
        upcoming_matches = _build_upcoming_template(teams)

    teams.to_csv(PROCESSED_DIR / "teams.csv", index=False)
    matches_current.to_csv(PROCESSED_DIR / "matches_current.csv", index=False)
    team_match_current.to_csv(PROCESSED_DIR / "team_match_current.csv", index=False)
    team_history.to_csv(PROCESSED_DIR / "team_history.csv", index=False)
    team_features.to_csv(PROCESSED_DIR / "team_features.csv", index=False)
    upcoming_matches.to_csv(upcoming_path, index=False)

    print(f"OK teams.csv creado: {len(teams)} equipos")
    print(f"OK matches_current.csv creado: {len(matches_current)} partidos")
    print(f"OK team_match_current.csv creado: {len(team_match_current)} filas")
    print(f"OK team_history.csv creado: {len(team_history)} filas")
    print(f"OK team_features.csv creado: {len(team_features)} equipos")
    print(f"OK upcoming_matches.csv listo: {len(upcoming_matches)} partidos programados")


if __name__ == "__main__":
    main()
