from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, field_validator

from src.config import (
    G_EFF,
    HALF_LIFE_DAYS,
    MAX_GOALS_MATRIX,
    MODEL_MODE,
    MODEL_VERSION,
    OUTPUTS_DIR,
    RHO_DIXON_COLES,
)


class ProbabilityBlock(BaseModel):
    team_a_win: float
    draw: float
    team_b_win: float

    @field_validator("team_b_win")
    @classmethod
    def probabilities_sum_to_one(cls, value: float, info):
        data = info.data
        total = data.get("team_a_win", 0) + data.get("draw", 0) + value
        if abs(total - 1.0) > 0.01:
            raise ValueError("1X2 probabilities must sum approximately to 1")
        return value


class ScoreProbability(BaseModel):
    score: str
    probability: float


class TeamRef(BaseModel):
    id: str
    name: str
    slug: str


class PredictionMatch(BaseModel):
    match_id: str
    date: str | None = None
    time_local: str | None = None
    group: str | None = None
    venue: str | None = None
    team_a: TeamRef
    team_b: TeamRef
    expected_goals: dict[str, float]
    probabilities: ProbabilityBlock
    predicted_result: str
    most_likely_score: ScoreProbability | None = None
    top_scores: list[ScoreProbability]
    confidence_label: str
    notes: str | None = None


class PredictionsToday(BaseModel):
    generated_at: str
    model_version: str
    model_mode: str
    matches: list[PredictionMatch]


def _clean_json(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _time_sort_key(time_local: object) -> str:
    if time_local is None or pd.isna(time_local):
        return "99:99"
    text = str(time_local).strip()
    try:
        return datetime.strptime(text, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        return text


def export_predictions_today(
    predictions: pd.DataFrame,
    upcoming_matches: pd.DataFrame,
    teams: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "predictions_today.json",
) -> dict[str, Any]:
    if not predictions.empty:
        predictions = (
            predictions.sort_values("generated_at")
            .drop_duplicates("match_id", keep="last")
            .reset_index(drop=True)
        )
    generated_at = (
        str(predictions["generated_at"].max()) if not predictions.empty else pd.Timestamp.utcnow().isoformat()
    )
    teams_by_id = teams.set_index("team_id").to_dict(orient="index")
    upcoming_by_id = upcoming_matches.set_index("match_id").to_dict(orient="index") if not upcoming_matches.empty else {}
    matches = []

    for _, row in predictions.iterrows():
        match = upcoming_by_id.get(row["match_id"], {})
        team_a = teams_by_id[row["team_a_id"]]
        team_b = teams_by_id[row["team_b_id"]]
        top_scores = [
            {"score": row[f"top_score_{i}"], "probability": row[f"top_score_{i}_prob"]}
            for i in range(1, 6)
            if _clean_json(row.get(f"top_score_{i}")) is not None
        ]
        matches.append(
            {
                "match_id": row["match_id"],
                "date": _clean_json(match.get("date")),
                "time_local": _clean_json(match.get("time_local")),
                "group": _clean_json(match.get("group")),
                "venue": _clean_json(match.get("venue")),
                "team_a": {
                    "id": row["team_a_id"],
                    "name": team_a["name_es"],
                    "slug": team_a["slug"],
                },
                "team_b": {
                    "id": row["team_b_id"],
                    "name": team_b["name_es"],
                    "slug": team_b["slug"],
                },
                "expected_goals": {
                    "team_a": float(row["lambda_a"]),
                    "team_b": float(row["lambda_b"]),
                },
                "probabilities": {
                    "team_a_win": float(row["prob_a"]),
                    "draw": float(row["prob_draw"]),
                    "team_b_win": float(row["prob_b"]),
                },
                "predicted_result": row["predicted_result"],
                "most_likely_score": top_scores[0] if top_scores else None,
                "top_scores": top_scores,
                "confidence_label": row["confidence_label"],
                "notes": _clean_json(row.get("notes")),
            }
        )
    matches = sorted(
        matches,
        key=lambda item: (
            item.get("date") or "",
            _time_sort_key(item.get("time_local")),
            item["match_id"],
        ),
    )

    payload = {
        "generated_at": generated_at,
        "model_version": MODEL_VERSION,
        "model_mode": MODEL_MODE,
        "matches": matches,
    }
    PredictionsToday.model_validate(payload)
    _write_json(path, payload)
    return payload


def export_team_power_ranking(
    team_features: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "team_power_ranking.json",
) -> dict[str, Any]:
    df = team_features.copy()
    df["power_score"] = df["attack_index"] / df["defense_index"].replace(0, 0.1)
    df = df.sort_values(["power_score", "data_quality_score"], ascending=False)
    teams = []
    for _, row in df.iterrows():
        teams.append(
            {
                "team_id": row["team_id"],
                "name": row["team_name"],
                "group": _clean_json(row.get("group")),
                "attack_index": _clean_json(row.get("attack_index")),
                "defense_index": _clean_json(row.get("defense_index")),
                "weighted_goals_for_pg": _clean_json(row.get("weighted_goals_for_pg")),
                "weighted_goals_against_pg": _clean_json(row.get("weighted_goals_against_pg")),
                "current_tournament_xg_diff_pg": _clean_json(row.get("current_tournament_xg_diff_pg")),
                "data_quality_score": _clean_json(row.get("data_quality_score")),
            }
        )
    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "ranking_type": "team_power_ranking",
        "not_a_champion_probability": True,
        "teams": teams,
    }
    _write_json(path, payload)
    return payload


def export_model_metadata(path: Path = OUTPUTS_DIR / "model_metadata.json") -> dict[str, Any]:
    payload = {
        "model_version": MODEL_VERSION,
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_mode": MODEL_MODE,
        "parameters": {
            "G_eff": G_EFF,
            "half_life_days": HALF_LIFE_DAYS,
            "max_goals_matrix": MAX_GOALS_MATRIX,
            "rho_dixon_coles": RHO_DIXON_COLES,
        },
        "data_sources": {
            "current_worldcup_matches": "mundial_fifa_2026_partidos_hasta_18_jun_2026_estadisticas.xlsx",
            "team_history": "Estadisticas_ultimos20_selecciones_Mundial2026_v5_48selecciones_FINAL.xlsx",
        },
        "handoff_to_astro": {
            "contract_outputs_dir": "data/outputs",
            "integration_phase": "Fase 2 y Fase 3",
        },
        "limitations": [
            "El modelo inicial no incorpora Elo si no se carga la tabla de ratings.",
            "La probabilidad de campeon es experimental y usa bracket aproximado.",
            "No implementa todavia el bracket oficial completo de FIFA.",
            "La simulacion Monte Carlo actual cubre fase de grupos, mejores terceros y eliminatorias aproximadas.",
            "El marcador exacto se muestra como curiosidad probabilistica, no como prediccion segura.",
        ],
    }
    _write_json(path, payload)
    return payload
