from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.ingest.normalize_teams import normalize_team


def _clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return None if value == "" or value.upper() == "ND" else value
    return value


def _number(value):
    value = _clean_value(value)
    if value is None:
        return None
    if isinstance(value, str):
        value = value.replace("%", "").replace(",", ".").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value):
    value = _number(value)
    return None if value is None else int(value)


def _date(value):
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def _result_1x2(goals_a: int | None, goals_b: int | None) -> str | None:
    if goals_a is None or goals_b is None:
        return None
    if goals_a > goals_b:
        return "1"
    if goals_a < goals_b:
        return "2"
    return "X"


def _match_id(date: str | None, team_a_id: str, team_b_id: str, match_no: object = None) -> str:
    prefix = date or f"match-{match_no or 'unknown'}"
    if match_no is not None and str(match_no).strip() not in {"", "nan", "None"}:
        return f"{prefix}_match-{str(match_no).strip()}"
    return f"{prefix}_{team_a_id}_{team_b_id}"


def load_current_workbook(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    partidos = pd.read_excel(path, sheet_name="Partidos")
    team_rows = pd.read_excel(path, sheet_name="Datos por equipo")
    return (
        transform_matches_current(partidos),
        transform_team_match_current(team_rows),
        build_teams_from_current(partidos, team_rows),
    )


def transform_matches_current(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        team_a = normalize_team(row.get("Equipo 1"), row.get("Codigo 1") or row.get("Código 1"))
        team_b = normalize_team(row.get("Equipo 2"), row.get("Codigo 2") or row.get("Código 2"))
        date = _date(row.get("Fecha"))
        goals_a = _int(row.get("GF 1"))
        goals_b = _int(row.get("GF 2"))
        result = _result_1x2(goals_a, goals_b)
        winner = team_a.team_id if result == "1" else team_b.team_id if result == "2" else None
        match_no = _clean_value(row.get("No"))
        rows.append(
            {
                "match_id": _match_id(date, team_a.team_id, team_b.team_id, match_no),
                "match_no": match_no,
                "date": date,
                "group": _clean_value(row.get("Grupo")),
                "team_a_id": team_a.team_id,
                "team_a_name": team_a.name,
                "team_a_goals": goals_a,
                "team_b_id": team_b.team_id,
                "team_b_name": team_b.name,
                "team_b_goals": goals_b,
                "total_goals": _int(row.get("Total goles")),
                "goal_diff": _int(row.get("Dif. goles")),
                "winner_team_id": winner,
                "result_1x2": result,
                "team_a_possession": _number(row.get("Posesion 1 %") or row.get("Posesión 1 %")),
                "team_b_possession": _number(row.get("Posesion 2 %") or row.get("Posesión 2 %")),
                "team_a_shots": _int(row.get("Remates 1")),
                "team_b_shots": _int(row.get("Remates 2")),
                "team_a_shots_on_target": _int(row.get("Remates al arco 1")),
                "team_b_shots_on_target": _int(row.get("Remates al arco 2")),
                "team_a_xg": _number(row.get("xG 1")),
                "team_b_xg": _number(row.get("xG 2")),
                "total_xg": _number(row.get("xG total")),
                "xg_diff": _number(row.get("Dif. xG")),
                "team_a_big_chances": _int(row.get("Ocasiones 1")),
                "team_b_big_chances": _int(row.get("Ocasiones 2")),
                "team_a_corners": _int(row.get("Corners 1") or row.get("Córners 1")),
                "team_b_corners": _int(row.get("Corners 2") or row.get("Córners 2")),
                "team_a_yellow_cards": _int(row.get("Amarillas 1")),
                "team_b_yellow_cards": _int(row.get("Amarillas 2")),
                "team_a_red_cards": _int(row.get("Rojas 1")),
                "team_b_red_cards": _int(row.get("Rojas 2")),
                "team_a_formation": _clean_value(row.get("Formacion 1") or row.get("Formación 1")),
                "team_b_formation": _clean_value(row.get("Formacion 2") or row.get("Formación 2")),
                "source_url": _clean_value(row.get("Fuente")),
                "data_status": "verified" if goals_a is not None and goals_b is not None else "partial",
            }
        )
    return pd.DataFrame(rows)


def transform_team_match_current(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        team = normalize_team(row.get("Equipo"), row.get("Codigo") or row.get("Código"))
        opponent = normalize_team(row.get("Rival"), row.get("Codigo rival") or row.get("Código rival"))
        date = _date(row.get("Fecha"))
        match_no = _clean_value(row.get("No partido"))
        is_team_a = str(_clean_value(row.get("Orden")) or "").strip() in {"1", "A", "a"}
        goals_for = _int(row.get("GF"))
        goals_against = _int(row.get("GC"))
        shots = _number(row.get("Remates"))
        shots_on_target = _number(row.get("Remates al arco"))
        shot_accuracy = _number(row.get("% remates al arco"))
        if shot_accuracy is None and shots and shots_on_target is not None:
            shot_accuracy = shots_on_target / shots
        rows.append(
            {
                "match_id": _match_id(date, team.team_id, opponent.team_id, match_no),
                "match_no": match_no,
                "date": date,
                "group": _clean_value(row.get("Grupo")),
                "team_id": team.team_id,
                "team_name": team.name,
                "opponent_id": opponent.team_id,
                "opponent_name": opponent.name,
                "is_team_a": is_team_a,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "result": _clean_value(row.get("Resultado")),
                "points": _int(row.get("Puntos")),
                "possession": _number(row.get("Posesion %") or row.get("Posesión %")),
                "shots": _int(row.get("Remates")),
                "shots_on_target": _int(row.get("Remates al arco")),
                "shot_accuracy": shot_accuracy,
                "xg_for": _number(row.get("xG")),
                "xg_against": _number(row.get("xG rival")),
                "xg_diff": _number(row.get("Dif. xG")),
                "big_chances": _int(row.get("Ocasiones")),
                "corners": _int(row.get("Corners") or row.get("Córners")),
                "yellow_cards": _int(row.get("Amarillas")),
                "red_cards": _int(row.get("Rojas")),
                "formation": _clean_value(row.get("Formacion") or row.get("Formación")),
                "source_url": _clean_value(row.get("Fuente")),
                "data_status": "verified" if goals_for is not None and goals_against is not None else "partial",
            }
        )
    return pd.DataFrame(rows)


def build_teams_from_current(matches: pd.DataFrame, team_rows: pd.DataFrame) -> pd.DataFrame:
    teams = {}
    for _, row in matches.iterrows():
        for name_col, code_col in [
            ("Equipo 1", "Codigo 1"),
            ("Equipo 1", "Código 1"),
            ("Equipo 2", "Codigo 2"),
            ("Equipo 2", "Código 2"),
        ]:
            if name_col in row:
                team = normalize_team(row.get(name_col), row.get(code_col))
                teams.setdefault(team.team_id, {"team_id": team.team_id, "fifa_code": team.team_id, "name_es": team.name, "name_en": team.name, "slug": team.slug, "group": _clean_value(row.get("Grupo")), "is_host": False, "confederation": None})
    for _, row in team_rows.iterrows():
        team = normalize_team(row.get("Equipo"), row.get("Codigo") or row.get("Código"))
        teams.setdefault(team.team_id, {"team_id": team.team_id, "fifa_code": team.team_id, "name_es": team.name, "name_en": team.name, "slug": team.slug, "group": _clean_value(row.get("Grupo")), "is_host": False, "confederation": None})
    return pd.DataFrame(teams.values()).sort_values("team_id").reset_index(drop=True)
