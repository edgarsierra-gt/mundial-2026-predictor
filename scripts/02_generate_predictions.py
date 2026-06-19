from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import PROCESSED_DIR
from src.model.match_predictor import predict_matches


def main() -> None:
    team_features = pd.read_csv(PROCESSED_DIR / "team_features.csv")
    upcoming_matches = pd.read_csv(PROCESSED_DIR / "upcoming_matches.csv")
    predictions = predict_matches(team_features, upcoming_matches)

    frozen_path = PROCESSED_DIR / "predictions_frozen.csv"
    if frozen_path.exists() and not predictions.empty:
        existing = pd.read_csv(frozen_path)
        if not existing.empty:
            predictions = pd.concat([existing, predictions], ignore_index=True)
            predictions = predictions.drop_duplicates("prediction_id", keep="last")
    elif frozen_path.exists() and predictions.empty:
        predictions = pd.read_csv(frozen_path)

    predictions.to_csv(frozen_path, index=False)
    print(f"OK Predicciones disponibles: {len(predictions)} filas")
    print("OK predictions_frozen.csv actualizado")


if __name__ == "__main__":
    main()
