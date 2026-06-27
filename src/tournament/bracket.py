from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.config import G_EFF
from src.model.poisson import clamp_lambda, score_matrix


ROUND_COLUMNS = [
    "reached_round_of_32",
    "reached_round_of_16",
    "reached_quarterfinal",
    "reached_semifinal",
    "reached_final",
    "champion",
]


def approximate_bracket_seed(classified_standings: pd.DataFrame) -> list[str]:
    qualified = classified_standings.loc[classified_standings["qualified_group"]].copy()
    winners = qualified.loc[qualified["rank_current"] == 1].sort_values("group")
    runners_up = qualified.loc[qualified["rank_current"] == 2].sort_values("group")
    thirds = qualified.loc[qualified["qualified_as_third"]].sort_values(
        ["points", "goal_difference", "goals_for", "team_id"],
        ascending=[False, False, False, True],
    )
    seeded = pd.concat([winners, runners_up, thirds], ignore_index=True)
    if len(seeded) != 32:
        raise ValueError(f"Expected 32 qualified teams, got {len(seeded)}")
    return seeded["team_id"].astype(str).tolist()


def first_round_pairs(seeded_teams: list[str]) -> list[tuple[str, str]]:
    if len(seeded_teams) != 32:
        raise ValueError("Round of 32 requires exactly 32 seeded teams")
    return [(seeded_teams[index], seeded_teams[-(index + 1)]) for index in range(16)]


def _team_feature_lookup(team_features: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {
        str(row.team_id): {
            "attack_index": float(row.attack_index),
            "defense_index": float(row.defense_index),
        }
        for row in team_features.itertuples()
    }


def _match_distribution(
    team_a_id: str,
    team_b_id: str,
    features: dict[str, dict[str, float]],
    cache: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any]:
    key = (team_a_id, team_b_id)
    if key in cache:
        return cache[key]
    team_a = features[team_a_id]
    team_b = features[team_b_id]
    lambda_a = clamp_lambda((G_EFF / 2) * team_a["attack_index"] * team_b["defense_index"])
    lambda_b = clamp_lambda((G_EFF / 2) * team_b["attack_index"] * team_a["defense_index"])
    matrix = score_matrix(lambda_a, lambda_b)
    payload = {
        "scores": matrix[["goals_a", "goals_b"]].to_numpy(dtype=int),
        "probabilities": matrix["probability"].to_numpy(dtype=float),
        "advance_a_if_draw": _advance_probability_if_draw(lambda_a, lambda_b),
    }
    cache[key] = payload
    return payload


def _advance_probability_if_draw(lambda_a: float, lambda_b: float) -> float:
    total = lambda_a + lambda_b
    if total <= 0:
        return 0.5
    return min(max(lambda_a / total, 0.05), 0.95)


def simulate_knockout_match(
    team_a_id: str,
    team_b_id: str,
    features: dict[str, dict[str, float]],
    rng: np.random.Generator,
    cache: dict[tuple[str, str], dict[str, Any]],
) -> str:
    distribution = _match_distribution(team_a_id, team_b_id, features, cache)
    sample_idx = int(rng.choice(len(distribution["scores"]), p=distribution["probabilities"]))
    goals_a, goals_b = distribution["scores"][sample_idx]
    if goals_a > goals_b:
        return team_a_id
    if goals_b > goals_a:
        return team_b_id
    return team_a_id if rng.random() < distribution["advance_a_if_draw"] else team_b_id


def allocate_thirds(third_groups: list[str]) -> dict[str, str]:
    # We define the allowed groups for each winner as per FIFA 2026 rules:
    allowed = {
        'A': ['C', 'E', 'F', 'H', 'I'],
        'B': ['E', 'F', 'G', 'I', 'J'],
        'D': ['B', 'E', 'F', 'I', 'J'],
        'E': ['A', 'B', 'C', 'D', 'F'],
        'G': ['A', 'E', 'H', 'I', 'J'],
        'I': ['C', 'D', 'F', 'G', 'H'],
        'K': ['D', 'E', 'I', 'J', 'L'],
        'L': ['E', 'H', 'I', 'J', 'K']
    }
    
    winners = sorted(allowed.keys())
    thirds = sorted(third_groups)
    assignment = {}
    
    def backtrack(winner_idx, available_thirds):
        if winner_idx == len(winners):
            return True
        w = winners[winner_idx]
        for t in available_thirds:
            if t in allowed[w]:
                assignment[w] = t
                remaining = [x for x in available_thirds if x != t]
                if backtrack(winner_idx + 1, remaining):
                    return True
                del assignment[w]
        return False
        
    if backtrack(0, thirds):
        return assignment
    else:
        # Fallback safe assignment
        assignment = {}
        used = set()
        for w in winners:
            assigned = False
            for t in thirds:
                if t not in used and t in allowed[w]:
                    assignment[w] = t
                    used.add(t)
                    assigned = True
                    break
            if not assigned:
                for t in thirds:
                    if t not in used:
                        assignment[w] = t
                        used.add(t)
                        break
        return assignment


def simulate_bracket(
    classified_standings: pd.DataFrame,
    team_features: pd.DataFrame,
    rng: np.random.Generator,
    cache: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> dict[str, list[str] | str]:
    cache = cache if cache is not None else {}
    features = _team_feature_lookup(team_features)

    # 1. Extract winners, runners-up, and thirds from group stage
    qualified = classified_standings.loc[classified_standings["qualified_group"]].copy()
    
    # Winners map: group -> team_id
    winners_df = qualified.loc[qualified["rank_current"] == 1]
    winners = {row.group: str(row.team_id) for row in winners_df.itertuples()}
    
    # Runners-up map: group -> team_id
    runners_df = qualified.loc[qualified["rank_current"] == 2]
    runners = {row.group: str(row.team_id) for row in runners_df.itertuples()}
    
    # Best thirds
    thirds_df = classified_standings.loc[classified_standings["qualified_as_third"]].sort_values(
        ["points", "goal_difference", "goals_for", "team_id"],
        ascending=[False, False, False, True],
    )
    
    # The 8 best thirds teams (team_id) and their group letters
    best_thirds_teams = {row.group: str(row.team_id) for row in thirds_df.itertuples()}
    best_thirds_groups = list(best_thirds_teams.keys())
    
    # 2. Allocate thirds dynamically
    thirds_assigned = allocate_thirds(best_thirds_groups)
    
    # Resolve third place team IDs with fallback if missing key
    t_A = best_thirds_teams.get(thirds_assigned.get('A', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_B = best_thirds_teams.get(thirds_assigned.get('B', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_D = best_thirds_teams.get(thirds_assigned.get('D', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_E = best_thirds_teams.get(thirds_assigned.get('E', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_G = best_thirds_teams.get(thirds_assigned.get('G', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_I = best_thirds_teams.get(thirds_assigned.get('I', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_K = best_thirds_teams.get(thirds_assigned.get('K', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')
    t_L = best_thirds_teams.get(thirds_assigned.get('L', ''), list(best_thirds_teams.values())[0] if best_thirds_teams else '')

    # 3. Define the Round of 32 pairings
    pairs_r32 = {
        73: (runners.get('A', ''), runners.get('B', '')),
        74: (winners.get('E', ''), t_E),
        75: (winners.get('F', ''), runners.get('C', '')),
        76: (winners.get('C', ''), runners.get('F', '')),
        77: (winners.get('I', ''), t_I),
        78: (runners.get('E', ''), runners.get('I', '')),
        79: (winners.get('A', ''), t_A),
        80: (winners.get('L', ''), t_L),
        81: (winners.get('D', ''), t_D),
        82: (winners.get('G', ''), t_G),
        83: (runners.get('K', ''), runners.get('L', '')),
        84: (winners.get('H', ''), runners.get('J', '')),
        85: (winners.get('B', ''), t_B),
        86: (winners.get('J', ''), runners.get('H', '')),
        87: (winners.get('K', ''), t_K),
        88: (runners.get('D', ''), runners.get('G', ''))
    }
    
    # Simulate Round of 32
    winners_r32 = {}
    for m, (team_a, team_b) in pairs_r32.items():
        winners_r32[m] = simulate_knockout_match(team_a, team_b, features, rng, cache)
        
    # Simulate Round of 16
    w89 = simulate_knockout_match(winners_r32[74], winners_r32[77], features, rng, cache)
    w90 = simulate_knockout_match(winners_r32[73], winners_r32[75], features, rng, cache)
    w91 = simulate_knockout_match(winners_r32[76], winners_r32[78], features, rng, cache)
    w92 = simulate_knockout_match(winners_r32[79], winners_r32[80], features, rng, cache)
    w93 = simulate_knockout_match(winners_r32[83], winners_r32[84], features, rng, cache)
    w94 = simulate_knockout_match(winners_r32[81], winners_r32[82], features, rng, cache)
    w95 = simulate_knockout_match(winners_r32[86], winners_r32[88], features, rng, cache)
    w96 = simulate_knockout_match(winners_r32[85], winners_r32[87], features, rng, cache)
    
    # Simulate Quarterfinals
    w97 = simulate_knockout_match(w89, w90, features, rng, cache)
    w98 = simulate_knockout_match(w93, w94, features, rng, cache)
    w99 = simulate_knockout_match(w91, w92, features, rng, cache)
    w100 = simulate_knockout_match(w95, w96, features, rng, cache)
    
    # Simulate Semifinals
    w101 = simulate_knockout_match(w97, w98, features, rng, cache)
    w102 = simulate_knockout_match(w99, w100, features, rng, cache)
    
    # Simulate Final
    champion = simulate_knockout_match(w101, w102, features, rng, cache)
    
    # Assemble outputs matching the format
    round_of_32 = []
    round_of_32.extend(pairs_r32[74])
    round_of_32.extend(pairs_r32[77])
    round_of_32.extend(pairs_r32[73])
    round_of_32.extend(pairs_r32[75])
    round_of_32.extend(pairs_r32[76])
    round_of_32.extend(pairs_r32[78])
    round_of_32.extend(pairs_r32[79])
    round_of_32.extend(pairs_r32[80])
    round_of_32.extend(pairs_r32[83])
    round_of_32.extend(pairs_r32[84])
    round_of_32.extend(pairs_r32[81])
    round_of_32.extend(pairs_r32[82])
    round_of_32.extend(pairs_r32[86])
    round_of_32.extend(pairs_r32[88])
    round_of_32.extend(pairs_r32[85])
    round_of_32.extend(pairs_r32[87])
    
    round_of_16 = [
        winners_r32[74], winners_r32[77],
        winners_r32[73], winners_r32[75],
        winners_r32[76], winners_r32[78],
        winners_r32[79], winners_r32[80],
        winners_r32[83], winners_r32[84],
        winners_r32[81], winners_r32[82],
        winners_r32[86], winners_r32[88],
        winners_r32[85], winners_r32[87]
    ]
    quarterfinal = [w89, w90, w91, w92, w93, w94, w95, w96]
    semifinal = [w97, w98, w99, w100]
    final = [w101, w102]
    
    return {
        "round_of_32": round_of_32,
        "round_of_16": round_of_16,
        "quarterfinal": quarterfinal,
        "semifinal": semifinal,
        "final": final,
        "champion": champion,
    }


def _simulate_round(
    teams: list[str],
    features: dict[str, dict[str, float]],
    rng: np.random.Generator,
    cache: dict[tuple[str, str], dict[str, Any]],
) -> list[str]:
    if len(teams) % 2 != 0:
        raise ValueError("Knockout rounds require an even number of teams")
    winners = []
    for index in range(0, len(teams), 2):
        winners.append(simulate_knockout_match(teams[index], teams[index + 1], features, rng, cache))
    return winners
