from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from src.audit.calibration import build_calibration_bins, goals_calibration
from src.config import MODEL_VERSION, OUTPUTS_DIR


class AuditMetrics(BaseModel):
    accuracy_1x2: float | None = Field(default=None, ge=0, le=1)
    brier_score: float | None = Field(default=None, ge=0)
    log_loss: float | None = Field(default=None, ge=0)
    exact_score_hit_rate: float | None = Field(default=None, ge=0, le=1)
    goals_bias: float | None = None
    goals_mae: float | None = Field(default=None, ge=0)


class ModelAudit(BaseModel):
    generated_at: str
    model_version: str
    matches_audited: int
    metrics: AuditMetrics
    by_confidence_bin: list[dict[str, Any]]
    notes: list[str]


class ModelCalibration(BaseModel):
    generated_at: str
    model_version: str
    bins: list[dict[str, Any]]
    goals: dict[str, float | None]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def audit_metrics(audited_matches: pd.DataFrame) -> dict[str, float | None]:
    if audited_matches.empty:
        return {
            "accuracy_1x2": None,
            "brier_score": None,
            "log_loss": None,
            "exact_score_hit_rate": None,
            "goals_bias": None,
            "goals_mae": None,
        }
    goals_error = audited_matches["goals_error"]
    return {
        "accuracy_1x2": round(float(audited_matches["hit_1x2"].mean()), 6),
        "brier_score": round(float(audited_matches["brier"].mean()), 6),
        "log_loss": round(float(audited_matches["log_loss"].mean()), 6),
        "exact_score_hit_rate": round(float(audited_matches["hit_exact_score"].mean()), 6),
        "goals_bias": round(float(goals_error.mean()), 6),
        "goals_mae": round(float(goals_error.abs().mean()), 6),
    }


def export_model_audit(
    audited_matches: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "model_audit.json",
) -> dict[str, Any]:
    notes = [
        "El modelo sigue siendo experimental.",
        "La muestra auditada puede ser pequena para conclusiones definitivas.",
        "El marcador exacto no es la metrica principal.",
    ]
    if audited_matches.empty:
        notes.insert(
            0,
            "Aun no hay partidos auditables porque no existe cruce entre predicciones congeladas y resultados reales.",
        )
    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "matches_audited": int(len(audited_matches)),
        "metrics": audit_metrics(audited_matches),
        "by_confidence_bin": build_calibration_bins(audited_matches),
        "notes": notes,
    }
    ModelAudit.model_validate(payload)
    _write_json(path, payload)
    return payload


def export_model_calibration(
    audited_matches: pd.DataFrame,
    path: Path = OUTPUTS_DIR / "model_calibration.json",
) -> dict[str, Any]:
    bins = [
        {
            "lower": int(item["bin"].split("-")[0]) / 100,
            "upper": int(item["bin"].split("-")[1]) / 100,
            "n": item["n"],
            "avg_predicted_probability": item["avg_confidence"],
            "empirical_frequency": item["actual_hit_rate"],
        }
        for item in build_calibration_bins(audited_matches)
        if "-" in str(item["bin"])
    ]
    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "model_version": MODEL_VERSION,
        "bins": bins,
        "goals": goals_calibration(audited_matches),
    }
    ModelCalibration.model_validate(payload)
    _write_json(path, payload)
    return payload
