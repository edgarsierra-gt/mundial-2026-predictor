from __future__ import annotations

import pandas as pd

from src.audit.scoring import (
    brier_score,
    exact_score_hit,
    goals_error,
    log_loss,
    normalize_actual_result,
    predicted_result,
)


def latest_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty:
        return predictions.copy()
    return predictions.sort_values("generated_at").drop_duplicates("match_id", keep="last")


def audit_predictions(predictions: pd.DataFrame, match_results_real: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty or match_results_real.empty:
        return _empty_audit_frame()

    latest = latest_predictions(predictions)
    merged = latest.merge(match_results_real, on="match_id", how="inner", suffixes=("_pred", "_real"))
    if merged.empty:
        return _empty_audit_frame()

    rows = []
    for row in merged.itertuples():
        probabilities = {
            "team_a_win": float(row.prob_a),
            "draw": float(row.prob_draw),
            "team_b_win": float(row.prob_b),
        }
        actual = normalize_actual_result(str(row.actual_result))
        predicted = predicted_result(probabilities)
        top_score = getattr(row, "top_score_1", None)
        total_goals_real = int(row.total_goals_real)
        rows.append(
            {
                "match_id": row.match_id,
                "prediction_timestamp": row.generated_at,
                "result_timestamp": row.verified_at,
                "model_version": row.model_version,
                "team_a_id": row.team_a_id_pred,
                "team_b_id": row.team_b_id_pred,
                "team_a_goals": int(row.team_a_goals),
                "team_b_goals": int(row.team_b_goals),
                "actual_1x2": actual,
                "predicted_1x2": predicted,
                "predicted_confidence": max(probabilities.values()),
                "hit_1x2": predicted == actual,
                "hit_exact_score": exact_score_hit(top_score, int(row.team_a_goals), int(row.team_b_goals)),
                "brier": brier_score(probabilities, actual),
                "log_loss": log_loss(probabilities, actual),
                "lambda_a": float(row.lambda_a),
                "lambda_b": float(row.lambda_b),
                "total_goals_real": total_goals_real,
                "goals_error": goals_error(float(row.lambda_a), float(row.lambda_b), total_goals_real),
            }
        )
    return pd.DataFrame(rows)


def _empty_audit_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "match_id",
            "prediction_timestamp",
            "result_timestamp",
            "model_version",
            "team_a_id",
            "team_b_id",
            "team_a_goals",
            "team_b_goals",
            "actual_1x2",
            "predicted_1x2",
            "predicted_confidence",
            "hit_1x2",
            "hit_exact_score",
            "brier",
            "log_loss",
            "lambda_a",
            "lambda_b",
            "total_goals_real",
            "goals_error",
        ]
    )
