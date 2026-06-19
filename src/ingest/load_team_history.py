from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.ingest.load_worldcup_current import _clean_value, _date, _int
from src.ingest.normalize_teams import normalize_team


def load_team_history(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_excel(path, sheet_name="Partidos_ultimos20")
    return transform_team_history(df), build_teams_from_history(df)


def _map_result(value: object, goals_for: int | None, goals_against: int | None) -> str | None:
    text = str(_clean_value(value) or "").strip().upper()
    if text in {"W", "D", "L"}:
        return text
    if text.startswith("G") or text.startswith("V"):
        return "W"
    if text.startswith("E") or text == "DRAW":
        return "D"
    if text.startswith("P") or text.startswith("L"):
        return "L"
    if goals_for is None or goals_against is None:
        return None
    if goals_for > goals_against:
        return "W"
    if goals_for < goals_against:
        return "L"
    return "D"


def _condition(value: object) -> str:
    text = str(_clean_value(value) or "").strip().lower()
    mapping = {
        "local": "home",
        "home": "home",
        "visitante": "away",
        "away": "away",
        "neutral": "neutral",
        "sede": "host",
        "host": "host",
    }
    return mapping.get(text, "unknown")


def transform_team_history(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx, row in df.iterrows():
        team = normalize_team(row.get("Seleccion") or row.get("Selección"))
        opponent = normalize_team(row.get("Rival"))
        home = normalize_team(row.get("Local"))
        away = normalize_team(row.get("Visitante"))
        date = _date(row.get("Fecha"))
        goals_for = _int(row.get("GF"))
        goals_against = _int(row.get("GC"))
        result = _map_result(row.get("Resultado"), goals_for, goals_against)
        rows.append(
            {
                "history_match_id": f"{date or 'unknown'}_{team.team_id}_{opponent.team_id}_{idx + 1}",
                "date": date,
                "team_id": team.team_id,
                "team_name": team.name,
                "opponent_id": opponent.team_id,
                "opponent_name": opponent.name,
                "condition": _condition(row.get("Condicion") or row.get("Condición")),
                "match_type": _clean_value(row.get("Tipo_partido")) or "Unknown",
                "home_team_id": home.team_id,
                "away_team_id": away.team_id,
                "home_goals": _int(row.get("Goles_local")),
                "away_goals": _int(row.get("Goles_visitante")),
                "goals_for": goals_for,
                "goals_against": goals_against,
                "result": result,
                "total_goals": _int(row.get("Goles_totales")),
                "shots_on_target_for": _int(row.get("Remates_al_arco_equipo")),
                "shots_on_target_against": _int(row.get("Remates_al_arco_rival")),
                "shots_source_url": _clean_value(row.get("Fuente_remates")),
                "shots_status": _clean_value(row.get("Estado_remates")) or "missing",
                "notes": _clean_value(row.get("Notas")),
                "result_source_url": _clean_value(row.get("Fuente_resultado")),
                "data_status": "verified" if goals_for is not None and goals_against is not None else "partial",
            }
        )
    return pd.DataFrame(rows)


def build_teams_from_history(df: pd.DataFrame) -> pd.DataFrame:
    teams = {}
    for _, row in df.iterrows():
        team = normalize_team(row.get("Seleccion") or row.get("Selección"))
        teams.setdefault(
            team.team_id,
            {
                "team_id": team.team_id,
                "fifa_code": team.team_id,
                "name_es": team.name,
                "name_en": team.name,
                "slug": team.slug,
                "group": None,
                "is_host": False,
                "confederation": None,
            },
        )
    return pd.DataFrame(teams.values()).sort_values("team_id").reset_index(drop=True)

