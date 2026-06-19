from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import OUTPUTS_DIR, PROCESSED_DIR
from src.export.to_json import (
    export_model_metadata,
    export_predictions_today,
    export_team_power_ranking,
)


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    teams = pd.read_csv(PROCESSED_DIR / "teams.csv")
    team_features = pd.read_csv(PROCESSED_DIR / "team_features.csv")
    upcoming_matches = pd.read_csv(PROCESSED_DIR / "upcoming_matches.csv")
    predictions = pd.read_csv(PROCESSED_DIR / "predictions_frozen.csv")

    export_predictions_today(predictions, upcoming_matches, teams)
    export_team_power_ranking(team_features)
    export_model_metadata()

    print("OK predictions_today.json exportado")
    print("OK team_power_ranking.json exportado")
    print("OK model_metadata.json exportado")


if __name__ == "__main__":
    main()

