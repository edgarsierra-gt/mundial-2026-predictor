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

    latest = latest_predictions(predictions).copy()
    real = match_results_real.copy()

    # Try merging by match_id first (for backward compatibility / ingested matches)
    merged = latest.merge(real, on="match_id", how="inner", suffixes=("_pred", "_real"))

    # Only perform fallback matching if required columns exist
    has_latest_cols = "team_a_id" in latest.columns and "team_b_id" in latest.columns
    has_real_cols = "date" in real.columns and "team_a_id" in real.columns and "team_b_id" in real.columns

    if has_latest_cols and has_real_cols:
        # Find which matches are not yet in merged
        merged_match_ids = set(merged["match_id"])
        remaining_predictions = latest[~latest["match_id"].isin(merged_match_ids)]

        if not remaining_predictions.empty:
            # Extract date from prediction match_id (first 10 chars)
            remaining_predictions = remaining_predictions.copy()
            remaining_predictions["pred_date"] = remaining_predictions["match_id"].astype(str).str.slice(0, 10)
            remaining_predictions["merge_key_normal"] = (
                remaining_predictions["pred_date"] + "_" + remaining_predictions["team_a_id"] + "_" + remaining_predictions["team_b_id"]
            )
            remaining_predictions["merge_key_swapped"] = (
                remaining_predictions["pred_date"] + "_" + remaining_predictions["team_b_id"] + "_" + remaining_predictions["team_a_id"]
            )

            real["merge_key"] = real["date"].astype(str).str.slice(0, 10) + "_" + real["team_a_id"] + "_" + real["team_b_id"]

            # Match normal direction
            merged_by_key_normal = remaining_predictions.merge(
                real, left_on="merge_key_normal", right_on="merge_key", how="inner", suffixes=("_pred", "_real")
            )
            if not merged_by_key_normal.empty:
                merged_by_key_normal["match_id"] = merged_by_key_normal["match_id_pred"]
                # Drop temp columns
                temp_cols = ["pred_date", "merge_key_normal", "merge_key_swapped", "merge_key"]
                merged_by_key_normal = merged_by_key_normal.drop(columns=[c for c in temp_cols if c in merged_by_key_normal.columns])
                merged = pd.concat([merged, merged_by_key_normal], ignore_index=True)

            # Match swapped direction (if any remaining)
            merged_match_ids = set(merged["match_id"])
            remaining_predictions = remaining_predictions[~remaining_predictions["match_id"].isin(merged_match_ids)]

            if not remaining_predictions.empty:
                merged_by_key_swapped = remaining_predictions.merge(
                    real, left_on="merge_key_swapped", right_on="merge_key", how="inner", suffixes=("_pred", "_real")
                )
                if not merged_by_key_swapped.empty:
                    merged_by_key_swapped["match_id"] = merged_by_key_swapped["match_id_pred"]

                    # Swapped orientation: swap goals to match prediction's perspective
                    temp_goals_a = merged_by_key_swapped["team_a_goals"].copy()
                    merged_by_key_swapped["team_a_goals"] = merged_by_key_swapped["team_b_goals"]
                    merged_by_key_swapped["team_b_goals"] = temp_goals_a

                    # Swap result
                    def swap_result(res):
                        if res == "team_a_win": return "team_b_win"
                        if res == "team_b_win": return "team_a_win"
                        return res
                    merged_by_key_swapped["actual_result"] = merged_by_key_swapped["actual_result"].apply(swap_result)

                    # Drop temp columns
                    temp_cols = ["pred_date", "merge_key_normal", "merge_key_swapped", "merge_key"]
                    merged_by_key_swapped = merged_by_key_swapped.drop(columns=[c for c in temp_cols if c in merged_by_key_swapped.columns])
                    merged = pd.concat([merged, merged_by_key_swapped], ignore_index=True)

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
