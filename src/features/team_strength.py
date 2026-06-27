from __future__ import annotations

import pandas as pd

from src.config import G_EFF
from src.features.recent_form import add_history_weights


def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _points(result: object) -> int:
    return {"W": 3, "D": 1, "L": 0}.get(str(result or "").upper(), 0)


def build_team_features(
    teams: pd.DataFrame,
    history: pd.DataFrame,
    team_match_current: pd.DataFrame,
) -> pd.DataFrame:
    from pathlib import Path
    
    anchor_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "strength_anchor.csv"
    if anchor_path.exists():
        anchor_df = pd.read_csv(anchor_path)
        elo_lookup = anchor_df.set_index("team_id")["elo_rating"].to_dict()
    else:
        elo_lookup = {}

    if elo_lookup:
        mean_elo = float(sum(elo_lookup.values()) / len(elo_lookup))
    else:
        mean_elo = 1770.0

    weighted_history = add_history_weights(history)
    current = team_match_current.copy()
    rows = []

    for _, team in teams.iterrows():
        team_id = team["team_id"]
        h = weighted_history[weighted_history["team_id"] == team_id].copy()
        c = current[current["team_id"] == team_id].copy()

        weight_sum = float(h["match_weight"].sum()) if not h.empty else 0.0
        goals_for_weighted = (
            float((h["goals_for"].fillna(0) * h["match_weight"]).sum()) if not h.empty else 0.0
        )
        goals_against_weighted = (
            float((h["goals_against"].fillna(0) * h["match_weight"]).sum()) if not h.empty else 0.0
        )
        goals_for_pg = _safe_div(goals_for_weighted, weight_sum) or 0.0
        goals_against_pg = _safe_div(goals_against_weighted, weight_sum) or 0.0
        total_goals_pg = goals_for_pg + goals_against_pg

        result_counts = h["result"].value_counts() if not h.empty else pd.Series(dtype=float)
        matches_history = int(len(h))
        points_pg = _safe_div(float(h["result"].apply(_points).sum()), matches_history) or 0.0
        win_rate = _safe_div(float(result_counts.get("W", 0)), matches_history) or 0.0
        draw_rate = _safe_div(float(result_counts.get("D", 0)), matches_history) or 0.0
        loss_rate = _safe_div(float(result_counts.get("L", 0)), matches_history) or 0.0

        baseline = G_EFF / 2
        attack_index_recent = goals_for_pg / baseline if baseline else 1.0
        defense_index_recent = goals_against_pg / baseline if baseline else 1.0

        # Elo Prior
        elo_val = float(elo_lookup.get(team_id, mean_elo))
        elo_att = 10.0 ** ((elo_val - mean_elo) / 1000.0)
        elo_def = 10.0 ** (-(elo_val - mean_elo) / 1000.0)

        # Mix Elo (50%) and Recent Form (50%)
        attack_base = 0.5 * elo_att + 0.5 * attack_index_recent
        defense_base = 0.5 * elo_def + 0.5 * defense_index_recent

        # Real-time tournament performance adjustment
        n_current = len(c)
        if n_current > 0:
            if "xg_for" in c and not c["xg_for"].isna().all():
                tourney_goals_for = float(c["xg_for"].mean())
            else:
                tourney_goals_for = float(c["goals_for"].mean())

            if "xg_against" in c and not c["xg_against"].isna().all():
                tourney_goals_against = float(c["xg_against"].mean())
            else:
                tourney_goals_against = float(c["goals_against"].mean())

            tourney_att = tourney_goals_for / baseline if baseline else 1.0
            tourney_def = tourney_goals_against / baseline if baseline else 1.0

            w_current = n_current / (n_current + 3.0)
            attack_index = (1.0 - w_current) * attack_base + w_current * tourney_att
            defense_index = (1.0 - w_current) * defense_base + w_current * tourney_def
        else:
            attack_index = attack_base
            defense_index = defense_base

        # Safeguard clamps
        attack_index = max(0.1, min(attack_index, 4.0))
        defense_index = max(0.1, min(defense_index, 4.0))

        data_quality_score = min(1.0, matches_history / 20) if matches_history else 0.0

        rows.append(
            {
                "team_id": team_id,
                "team_name": team["name_es"],
                "group": team.get("group"),
                "matches_history": matches_history,
                "weighted_goals_for_pg": round(goals_for_pg, 4),
                "weighted_goals_against_pg": round(goals_against_pg, 4),
                "weighted_total_goals_pg": round(total_goals_pg, 4),
                "recent_form_points_pg": round(points_pg, 4),
                "win_rate": round(win_rate, 4),
                "draw_rate": round(draw_rate, 4),
                "loss_rate": round(loss_rate, 4),
                "attack_index": round(attack_index, 4),
                "defense_index": round(defense_index, 4),
                "current_tournament_goals_for_pg": round(float(c["goals_for"].mean()), 4)
                if not c.empty
                else None,
                "current_tournament_goals_against_pg": round(float(c["goals_against"].mean()), 4)
                if not c.empty
                else None,
                "current_tournament_xg_for_pg": round(float(c["xg_for"].mean()), 4)
                if not c.empty and "xg_for" in c
                else None,
                "current_tournament_xg_against_pg": round(float(c["xg_against"].mean()), 4)
                if not c.empty and "xg_against" in c
                else None,
                "current_tournament_xg_diff_pg": round(float(c["xg_diff"].mean()), 4)
                if not c.empty and "xg_diff" in c
                else None,
                "data_quality_score": round(data_quality_score, 4),
                "updated_at": pd.Timestamp.utcnow().isoformat(),
            }
        )
    return pd.DataFrame(rows).sort_values("team_id").reset_index(drop=True)

