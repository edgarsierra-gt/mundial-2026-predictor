from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, field_validator

from src.config import MODEL_VERSION, OUTPUTS_DIR


class GroupProbabilityTeam(BaseModel):
    team_id: str
    name: str
    group: str
    played: int
    points: int
    prob_group_winner: float = Field(ge=0, le=1)
    prob_group_runner_up: float = Field(ge=0, le=1)
    prob_qualified_as_third: float = Field(ge=0, le=1)
    prob_eliminated_group: float = Field(ge=0, le=1)
    prob_advance: float = Field(ge=0, le=1)

    @field_validator("prob_advance")
    @classmethod
    def advance_matches_components(cls, value: float, info):
        data = info.data
        total = (
            data.get("prob_group_winner", 0)
            + data.get("prob_group_runner_up", 0)
            + data.get("prob_qualified_as_third", 0)
        )
        if abs(value - total) > 0.02:
            raise ValueError("prob_advance must match advancement components")
        return value


class GroupProbability(BaseModel):
    group: str
    teams: list[GroupProbabilityTeam]


class GroupProbabilities(BaseModel):
    generated_at: str
    model_version: str
    n_simulations: int
    groups: list[GroupProbability]


class RoundProbabilityTeam(BaseModel):
    team_id: str
    name: str
    group: str
    prob_round_of_32: float = Field(ge=0, le=1)
    prob_round_of_16: float = Field(ge=0, le=1)
    prob_quarterfinal: float = Field(ge=0, le=1)
    prob_semifinal: float = Field(ge=0, le=1)
    prob_final: float = Field(ge=0, le=1)
    prob_champion: float = Field(ge=0, le=1)


class RoundProbabilities(BaseModel):
    generated_at: str
    model_version: str
    n_simulations: int
    bracket_mode: str
    teams: list[RoundProbabilityTeam]


class ChampionOddsTeam(BaseModel):
    rank: int
    team_id: str
    name: str
    group: str
    prob_champion: float = Field(ge=0, le=1)
    prob_final: float = Field(ge=0, le=1)
    prob_semifinal: float = Field(ge=0, le=1)
    movement_since_previous: float | None = None


class ChampionOdds(BaseModel):
    generated_at: str
    model_version: str
    n_simulations: int
    bracket_mode: str
    interpretation_note: str
    teams: list[ChampionOddsTeam]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def export_group_probabilities(
    probabilities: pd.DataFrame,
    current_standings: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "group_probabilities.json",
) -> dict[str, Any]:
    standings_lookup = current_standings.set_index("team_id").to_dict(orient="index")
    groups = []
    n_simulations = int(probabilities["n_simulations"].max()) if not probabilities.empty else 0

    for group, group_df in probabilities.groupby("group", sort=True):
        teams = []
        group_df = group_df.sort_values(["prob_advance", "prob_group_winner"], ascending=False)
        for row in group_df.itertuples():
            standing = standings_lookup.get(row.team_id, {})
            teams.append(
                {
                    "team_id": row.team_id,
                    "name": row.name,
                    "group": row.group,
                    "played": int(standing.get("played", 0)),
                    "points": int(standing.get("points", 0)),
                    "prob_group_winner": round(float(row.prob_group_winner), 4),
                    "prob_group_runner_up": round(float(row.prob_group_runner_up), 4),
                    "prob_qualified_as_third": round(float(row.prob_qualified_as_third), 4),
                    "prob_eliminated_group": round(float(row.prob_eliminated_group), 4),
                    "prob_advance": round(float(row.prob_advance), 4),
                }
            )
        groups.append({"group": str(group), "teams": teams})

    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "n_simulations": n_simulations,
        "groups": groups,
    }
    GroupProbabilities.model_validate(payload)
    _write_json(path, payload)
    return payload


def export_round_probabilities(
    probabilities: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "round_probabilities.json",
) -> dict[str, Any]:
    n_simulations = int(probabilities["n_simulations"].max()) if not probabilities.empty else 0
    bracket_mode = str(probabilities["bracket_mode"].iloc[0]) if not probabilities.empty else "unknown"
    ordered = probabilities.sort_values(
        ["prob_round_of_32", "prob_round_of_16", "prob_champion"],
        ascending=[False, False, False],
    )
    teams = []
    for row in ordered.itertuples():
        teams.append(
            {
                "team_id": row.team_id,
                "name": row.name,
                "group": row.group,
                "prob_round_of_32": round(float(row.prob_round_of_32), 4),
                "prob_round_of_16": round(float(row.prob_round_of_16), 4),
                "prob_quarterfinal": round(float(row.prob_quarterfinal), 4),
                "prob_semifinal": round(float(row.prob_semifinal), 4),
                "prob_final": round(float(row.prob_final), 4),
                "prob_champion": round(float(row.prob_champion), 4),
            }
        )
    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "n_simulations": n_simulations,
        "bracket_mode": bracket_mode,
        "teams": teams,
    }
    RoundProbabilities.model_validate(payload)
    _write_json(path, payload)
    return payload


def export_champion_odds(
    probabilities: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "champion_odds.json",
) -> dict[str, Any]:
    n_simulations = int(probabilities["n_simulations"].max()) if not probabilities.empty else 0
    bracket_mode = str(probabilities["bracket_mode"].iloc[0]) if not probabilities.empty else "unknown"
    ordered = probabilities.sort_values(
        ["prob_champion", "prob_final", "prob_semifinal", "team_id"],
        ascending=[False, False, False, True],
    )
    teams = []
    for rank, row in enumerate(ordered.itertuples(), start=1):
        teams.append(
            {
                "rank": rank,
                "team_id": row.team_id,
                "name": row.name,
                "group": row.group,
                "prob_champion": round(float(row.prob_champion), 4),
                "prob_final": round(float(row.prob_final), 4),
                "prob_semifinal": round(float(row.prob_semifinal), 4),
                "movement_since_previous": None,
            }
        )
    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "n_simulations": n_simulations,
        "bracket_mode": bracket_mode,
        "interpretation_note": (
            "Probabilidad experimental de campeonar en simulaciones Monte Carlo; "
            "no es una prediccion determinista ni lenguaje de apuestas."
        ),
        "teams": teams,
    }
    ChampionOdds.model_validate(payload)
    _write_json(path, payload)
    return payload


def export_tournament_snapshot(
    probabilities: pd.DataFrame,
    current_standings: pd.DataFrame,
    round_probabilities: pd.DataFrame | None = None,
    path: Path = OUTPUTS_DIR / "tournament_snapshot.json",
) -> dict[str, Any]:
    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "n_simulations": int(probabilities["n_simulations"].max()) if not probabilities.empty else 0,
        "scope": "group_stage_and_official_bracket",
        "bracket_mode": (
            str(round_probabilities["bracket_mode"].iloc[0])
            if round_probabilities is not None and not round_probabilities.empty
            else "not_available"
        ),
        "standings_current": current_standings.to_dict(orient="records"),
        "notes": [
            "Este snapshot cubre la simulación de fase de grupos y el bracket oficial de la FIFA 2026.",
            "Modelo v2.0 incorpora ancla externa de fuerza (Elo prior) y la matriz oficial de mejores terceros de la FIFA.",
        ],
    }
    _write_json(path, payload)
    return payload
