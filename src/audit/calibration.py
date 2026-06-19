from __future__ import annotations

import pandas as pd


CONFIDENCE_BINS = [
    (0.40, 0.50, "40-50"),
    (0.50, 0.60, "50-60"),
    (0.60, 0.70, "60-70"),
    (0.70, 0.80, "70-80"),
    (0.80, 0.90, "80-90"),
    (0.90, 1.01, "90-100"),
]


def confidence_bin(confidence: float) -> str:
    for lower, upper, label in CONFIDENCE_BINS:
        if lower <= confidence < upper:
            return label
    if confidence < 0.40:
        return "below-40"
    return "90-100"


def build_calibration_bins(audited_matches: pd.DataFrame) -> list[dict[str, float | int | str]]:
    if audited_matches.empty:
        return []

    df = audited_matches.copy()
    df["bin"] = df["predicted_confidence"].apply(confidence_bin)
    rows = []
    for label in [item[2] for item in CONFIDENCE_BINS]:
        group = df.loc[df["bin"] == label]
        if group.empty:
            continue
        rows.append(
            {
                "bin": label,
                "n": int(len(group)),
                "avg_confidence": round(float(group["predicted_confidence"].mean()), 6),
                "actual_hit_rate": round(float(group["hit_1x2"].mean()), 6),
            }
        )
    return rows


def goals_calibration(audited_matches: pd.DataFrame) -> dict[str, float | None]:
    if audited_matches.empty:
        return {
            "mean_predicted_total": None,
            "mean_actual_total": None,
            "bias": None,
            "mae": None,
        }
    predicted_total = audited_matches["lambda_a"] + audited_matches["lambda_b"]
    actual_total = audited_matches["total_goals_real"]
    error = predicted_total - actual_total
    return {
        "mean_predicted_total": round(float(predicted_total.mean()), 6),
        "mean_actual_total": round(float(actual_total.mean()), 6),
        "bias": round(float(error.mean()), 6),
        "mae": round(float(error.abs().mean()), 6),
    }
