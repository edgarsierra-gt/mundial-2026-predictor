from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.audit.audit_predictions import audit_predictions
from src.audit.snapshots import freeze_predictions
from src.config import OUTPUTS_DIR, PROCESSED_DIR
from src.export.audit_json import export_model_audit, export_model_calibration


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    predictions_path = PROCESSED_DIR / "predictions_frozen.csv"
    results_path = PROCESSED_DIR / "match_results_real.csv"

    frozen_path = freeze_predictions(predictions_path)
    predictions = pd.read_csv(predictions_path)
    match_results_real = pd.read_csv(results_path)
    audited_matches = audit_predictions(predictions, match_results_real)

    audited_matches.to_csv(PROCESSED_DIR / "prediction_audit.csv", index=False)
    export_model_audit(audited_matches)
    export_model_calibration(audited_matches)

    print(f"OK predicciones congeladas: {frozen_path}")
    print(f"OK prediction_audit.csv exportado: {len(audited_matches)} partidos auditados")
    print("OK model_audit.json exportado")
    print("OK model_calibration.json exportado")


if __name__ == "__main__":
    main()
