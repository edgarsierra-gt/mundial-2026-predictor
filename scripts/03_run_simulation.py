from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import N_SIMULATIONS, OUTPUTS_DIR, PROCESSED_DIR, RANDOM_SEED
from src.export.simulation_json import (
    export_champion_odds,
    export_group_probabilities,
    export_round_probabilities,
    export_tournament_snapshot,
)
from src.tournament.groups import (
    build_current_standings,
    build_match_results_real,
    build_tournament_schedule,
)
from src.tournament.monte_carlo import simulate_tournament_probabilities


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    teams = pd.read_csv(PROCESSED_DIR / "teams.csv")
    matches_current = pd.read_csv(PROCESSED_DIR / "matches_current.csv")
    upcoming_matches = pd.read_csv(PROCESSED_DIR / "upcoming_matches.csv")
    predictions = pd.read_csv(PROCESSED_DIR / "predictions_frozen.csv")
    team_features = pd.read_csv(PROCESSED_DIR / "team_features.csv")

    tournament_schedule = build_tournament_schedule(matches_current, upcoming_matches)
    current_standings = build_current_standings(teams, matches_current)
    match_results_real = build_match_results_real(matches_current)

    tournament_schedule.to_csv(PROCESSED_DIR / "tournament_schedule.csv", index=False)
    current_standings.to_csv(PROCESSED_DIR / "group_standings_current.csv", index=False)
    match_results_real.to_csv(PROCESSED_DIR / "match_results_real.csv", index=False)

    group_probabilities, round_probabilities = simulate_tournament_probabilities(
        teams=teams,
        team_features=team_features,
        matches_current=matches_current,
        upcoming_matches=upcoming_matches,
        predictions=predictions,
        n_simulations=N_SIMULATIONS,
        seed=RANDOM_SEED,
    )

    export_group_probabilities(group_probabilities, current_standings)
    export_round_probabilities(round_probabilities)
    export_champion_odds(round_probabilities)
    export_tournament_snapshot(group_probabilities, current_standings, round_probabilities)

    print(f"OK tournament_schedule.csv exportado: {len(tournament_schedule)} partidos")
    print(f"OK group_standings_current.csv exportado: {len(current_standings)} equipos")
    print(f"OK match_results_real.csv exportado: {len(match_results_real)} resultados")
    print(f"OK group_probabilities.json exportado: {N_SIMULATIONS:,} simulaciones")
    print("OK round_probabilities.json exportado")
    print("OK champion_odds.json exportado")
    print("OK tournament_snapshot.json exportado")


if __name__ == "__main__":
    main()
