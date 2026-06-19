from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from src.config import FROZEN_PREDICTIONS_DIR


def freeze_predictions(predictions_path: Path, output_dir: Path = FROZEN_PREDICTIONS_DIR) -> Path:
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions = pd.read_csv(predictions_path)
    if predictions.empty or "generated_at" not in predictions.columns:
        timestamp = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
    else:
        timestamp = pd.to_datetime(predictions["generated_at"].max()).strftime("%Y%m%d_%H%M%S")
    target = output_dir / f"predictions_{timestamp}.csv"
    if not target.exists():
        shutil.copy2(predictions_path, target)
    return target
