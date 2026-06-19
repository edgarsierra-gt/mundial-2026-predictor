from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"

CURRENT_WORLD_CUP_XLSX = RAW_DIR / "mundial_fifa_2026_partidos_hasta_18_jun_2026_estadisticas.xlsx"
TEAM_HISTORY_XLSX = RAW_DIR / "Estadisticas_ultimos20_selecciones_Mundial2026_v5_48selecciones_FINAL.xlsx"

MODEL_VERSION = "0.1.0"
MODEL_MODE = "goals_only"

G_EFF = 3.10
HALF_LIFE_DAYS = 450
MAX_GOALS_MATRIX = 8
LAMBDA_MIN = 0.10
LAMBDA_MAX = 4.50
RHO_DIXON_COLES = 0.0

MATCH_TYPE_WEIGHTS = {
    "world cup": 1.30,
    "fifa world cup": 1.30,
    "copa mundial": 1.30,
    "continental tournament": 1.15,
    "world cup qualification": 1.10,
    "nations league": 1.00,
    "friendly international": 0.70,
    "friendly": 0.70,
    "amistoso": 0.70,
    "unknown": 0.80,
}

OUTPUT_FILES = {
    "predictions_today": OUTPUTS_DIR / "predictions_today.json",
    "team_power_ranking": OUTPUTS_DIR / "team_power_ranking.json",
    "model_metadata": OUTPUTS_DIR / "model_metadata.json",
}

