from __future__ import annotations

import hashlib

import pandas as pd

from src.config import G_EFF, MODEL_VERSION
from src.model.poisson import clamp_lambda, outcome_probabilities, score_matrix, top_scores


def _confidence_label(probabilities: dict[str, float]) -> str:
    max_prob = max(probabilities.values())
    if max_prob >= 0.75:
        return "Muy alta"
    if max_prob >= 0.60:
        return "Alta"
    if max_prob >= 0.50:
        return "Media"
    if max_prob >= 0.42:
        return "Media-baja"
    return "Baja"


def _predicted_result(probabilities: dict[str, float]) -> str:
    return max(probabilities, key=probabilities.get)


def _input_hash(team_features: pd.DataFrame, upcoming_matches: pd.DataFrame) -> str:
    payload = (
        team_features.sort_values("team_id").to_csv(index=False)
        + upcoming_matches.sort_values("match_id").to_csv(index=False)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def predict_matches(team_features: pd.DataFrame, upcoming_matches: pd.DataFrame) -> pd.DataFrame:
    if upcoming_matches.empty:
        return pd.DataFrame(
            columns=[
                "prediction_id",
                "match_id",
                "generated_at",
                "model_version",
                "team_a_id",
                "team_b_id",
                "lambda_a",
                "lambda_b",
                "prob_a",
                "prob_draw",
                "prob_b",
                "predicted_result",
                "top_score_1",
                "top_score_1_prob",
                "top_score_2",
                "top_score_2_prob",
                "top_score_3",
                "top_score_3_prob",
                "top_score_4",
                "top_score_4_prob",
                "top_score_5",
                "top_score_5_prob",
                "confidence_label",
                "input_data_hash",
                "notes",
            ]
        )

    features = team_features.set_index("team_id")
    generated_at = pd.Timestamp.utcnow().isoformat()
    input_hash = _input_hash(team_features, upcoming_matches)
    rows = []

    for _, match in upcoming_matches.iterrows():
        if str(match.get("status", "scheduled")).lower() != "scheduled":
            continue
        team_a = features.loc[match["team_a_id"]]
        team_b = features.loc[match["team_b_id"]]
        lambda_a = clamp_lambda((G_EFF / 2) * team_a["attack_index"] * team_b["defense_index"])
        lambda_b = clamp_lambda((G_EFF / 2) * team_b["attack_index"] * team_a["defense_index"])
        matrix = score_matrix(lambda_a, lambda_b)
        probs = outcome_probabilities(matrix)
        scores = top_scores(matrix, 5)
        while len(scores) < 5:
            scores.append({"score": None, "probability": None})

        prediction_id = f"{match['match_id']}_{generated_at}_{MODEL_VERSION}"
        rows.append(
            {
                "prediction_id": prediction_id,
                "match_id": match["match_id"],
                "generated_at": generated_at,
                "model_version": MODEL_VERSION,
                "team_a_id": match["team_a_id"],
                "team_b_id": match["team_b_id"],
                "lambda_a": round(lambda_a, 6),
                "lambda_b": round(lambda_b, 6),
                "prob_a": round(probs["team_a_win"], 6),
                "prob_draw": round(probs["draw"], 6),
                "prob_b": round(probs["team_b_win"], 6),
                "predicted_result": _predicted_result(probs),
                "top_score_1": scores[0]["score"],
                "top_score_1_prob": scores[0]["probability"],
                "top_score_2": scores[1]["score"],
                "top_score_2_prob": scores[1]["probability"],
                "top_score_3": scores[2]["score"],
                "top_score_3_prob": scores[2]["probability"],
                "top_score_4": scores[3]["score"],
                "top_score_4_prob": scores[3]["probability"],
                "top_score_5": scores[4]["score"],
                "top_score_5_prob": scores[4]["probability"],
                "confidence_label": _confidence_label(probs),
                "input_data_hash": input_hash,
                "notes": "Prediccion inicial basada en indices de ataque/defensa y matriz Poisson.",
            }
        )
    return pd.DataFrame(rows)

