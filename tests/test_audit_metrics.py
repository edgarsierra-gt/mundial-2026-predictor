from __future__ import annotations

import math

import pandas as pd

from src.audit.audit_predictions import audit_predictions
from src.audit.calibration import build_calibration_bins, goals_calibration
from src.audit.scoring import brier_score, exact_score_hit, goals_error, log_loss
from src.export.audit_json import audit_metrics


def test_brier_score_manual_case() -> None:
    probabilities = {"team_a_win": 0.5, "draw": 0.3, "team_b_win": 0.2}

    assert brier_score(probabilities, "team_a_win") == (0.5 - 1) ** 2 + 0.3**2 + 0.2**2


def test_log_loss_manual_case() -> None:
    probabilities = {"team_a_win": 0.5, "draw": 0.3, "team_b_win": 0.2}

    assert log_loss(probabilities, "draw") == -math.log(0.3)


def test_exact_score_and_goals_error() -> None:
    assert exact_score_hit("2-1", 2, 1)
    assert not exact_score_hit("1-1", 2, 1)
    assert goals_error(1.2, 0.8, 3) == -1.0


def test_audit_predictions_computes_match_metrics() -> None:
    predictions = pd.DataFrame(
        [
            {
                "match_id": "m1",
                "generated_at": "2026-06-19T00:00:00Z",
                "model_version": "0.1.0",
                "team_a_id": "A",
                "team_b_id": "B",
                "lambda_a": 1.4,
                "lambda_b": 0.6,
                "prob_a": 0.6,
                "prob_draw": 0.25,
                "prob_b": 0.15,
                "top_score_1": "2-0",
            }
        ]
    )
    results = pd.DataFrame(
        [
            {
                "match_id": "m1",
                "team_a_id": "A",
                "team_b_id": "B",
                "team_a_goals": 2,
                "team_b_goals": 0,
                "actual_result": "team_a_win",
                "total_goals_real": 2,
                "verified_at": "2026-06-19T02:00:00Z",
            }
        ]
    )

    audited = audit_predictions(predictions, results)

    assert len(audited) == 1
    assert bool(audited.iloc[0]["hit_1x2"])
    assert bool(audited.iloc[0]["hit_exact_score"])
    assert audited.iloc[0]["goals_error"] == 0
    assert audit_metrics(audited)["accuracy_1x2"] == 1.0


def test_calibration_bins_and_goals_calibration() -> None:
    audited = pd.DataFrame(
        [
            {"predicted_confidence": 0.55, "hit_1x2": True, "lambda_a": 1.0, "lambda_b": 1.0, "total_goals_real": 3},
            {"predicted_confidence": 0.58, "hit_1x2": False, "lambda_a": 1.0, "lambda_b": 2.0, "total_goals_real": 2},
        ]
    )

    bins = build_calibration_bins(audited)
    goals = goals_calibration(audited)

    assert bins == [{"bin": "50-60", "n": 2, "avg_confidence": 0.565, "actual_hit_rate": 0.5}]
    assert goals["mean_predicted_total"] == 2.5
    assert goals["mean_actual_total"] == 2.5
    assert goals["bias"] == 0.0
    assert goals["mae"] == 1.0
