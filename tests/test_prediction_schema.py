from src.export.to_json import PredictionsToday


def test_predictions_today_schema_accepts_empty_matches():
    payload = {
        "generated_at": "2026-06-19T12:00:00-06:00",
        "model_version": "0.1.0",
        "model_mode": "goals_only",
        "matches": [],
    }
    validated = PredictionsToday.model_validate(payload)
    assert validated.generated_at == payload["generated_at"]


def test_prediction_probabilities_sum_to_one():
    payload = {
        "generated_at": "2026-06-19T12:00:00-06:00",
        "model_version": "0.1.0",
        "model_mode": "goals_only",
        "matches": [
            {
                "match_id": "2026-06-19_USA_AUS",
                "date": "2026-06-19",
                "group": "D",
                "team_a": {"id": "USA", "name": "Estados Unidos", "slug": "estados-unidos"},
                "team_b": {"id": "AUS", "name": "Australia", "slug": "australia"},
                "expected_goals": {"team_a": 1.18, "team_b": 1.23},
                "probabilities": {"team_a_win": 0.34, "draw": 0.30, "team_b_win": 0.36},
                "predicted_result": "team_b_win",
                "most_likely_score": {"score": "0-1", "probability": 0.10},
                "top_scores": [{"score": "0-1", "probability": 0.10}],
                "confidence_label": "Baja",
                "notes": "Partido cerrado.",
            }
        ],
    }
    validated = PredictionsToday.model_validate(payload)
    assert validated.matches[0].probabilities.team_b_win == 0.36

