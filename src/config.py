from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
FROZEN_DIR = DATA_DIR / "frozen"
FROZEN_PREDICTIONS_DIR = FROZEN_DIR / "predictions"
FROZEN_SIMULATIONS_DIR = FROZEN_DIR / "simulations"


def _latest_raw_file(prefix: str) -> Path:
    """Most recently modified data/raw/<prefix>*.xlsx, or a non-existent
    placeholder Path if none is present.

    The source workbooks are re-exported under a new dated filename each time
    (e.g. mundial_fifa_2026_actualizado_22_jun_2026_gt.xlsx), so a hardcoded
    name goes stale the moment a fresher file lands. Same approach as
    edgarsierra.com's scripts/sync-estadisticas.mjs.

    Raw workbooks are gitignored (never published), so CI checkouts and
    --skip-build runs have none on disk at all — this must stay import-safe
    and only fail later, the same way the old hardcoded path did, when
    01_build_datasets.py explicitly checks .exists().
    """
    matches = sorted(RAW_DIR.glob(f"{prefix}*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if matches:
        return matches[0]
    return RAW_DIR / f"{prefix}NOT_FOUND.xlsx"


CURRENT_WORLD_CUP_XLSX = _latest_raw_file("mundial_fifa_2026_actualizado_")
TEAM_HISTORY_XLSX = _latest_raw_file("Estadisticas_ultimos20_")

MODEL_VERSION = "2.0.0"
MODEL_MODE = "goals_only"

N_SIMULATIONS = 10000
GROUPS = list("ABCDEFGHIJKL")
TEAMS_PER_GROUP = 4
DIRECT_QUALIFIERS_PER_GROUP = 2
THIRD_PLACE_QUALIFIERS = 8
RANDOM_SEED = 20260619

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
    "group_probabilities": OUTPUTS_DIR / "group_probabilities.json",
    "round_probabilities": OUTPUTS_DIR / "round_probabilities.json",
    "champion_odds": OUTPUTS_DIR / "champion_odds.json",
    "model_audit": OUTPUTS_DIR / "model_audit.json",
    "model_calibration": OUTPUTS_DIR / "model_calibration.json",
    "tournament_snapshot": OUTPUTS_DIR / "tournament_snapshot.json",
}
