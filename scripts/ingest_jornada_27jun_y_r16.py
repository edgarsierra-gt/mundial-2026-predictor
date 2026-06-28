"""
Ingest batch: partidos de grupos 25-jun (jornada 3 grupos D/E/F),
27-jun (jornada 3 grupos J/K/L), limpieza de 26-jun de upcoming,
y primer partido de 16avos (Canada vs Sudafrica, 2026-06-28).

Uso:
    python scripts/ingest_jornada_27jun_y_r16.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import PROCESSED_DIR, RAW_DIR

UPCOMING_PATH = PROCESSED_DIR / "upcoming_matches.csv"
MATCHES_CURRENT_PATH = PROCESSED_DIR / "matches_current.csv"

# ---------------------------------------------------------------------------
# Resultados grupos 25-jun (Excel fecha 46198 = 2026-06-25)
# ---------------------------------------------------------------------------
RESULTS_25JUN = [
    # date, team_a_id, team_b_id, gf_a, gf_b, pos_a, pos_b, shots_a, shots_b,
    # sot_a, sot_b, xg_a, xg_b, corners_a, corners_b, yellow_a, yellow_b, red_a, red_b,
    # form_a, form_b
    ("2026-06-25", "ECU", "GER", 2, 1, 39, 61, 8, 11, 3, 3, 1.54, 0.67, 3, 2, 3, 1, 0, 0, "4-4-2", "4-2-3-1"),
    ("2026-06-25", "CUW", "CIV", 0, 2, 38, 62, 10, 8, 3, 3, 0.45, 1.11, 4, 6, 2, 1, 0, 0, "5-3-2", "4-4-2"),
    ("2026-06-25", "JPN", "SWE", 1, 1, 51, 49, 8, 10, 3, 5, 1.04, 0.70, 2, 8, 1, 2, 0, 0, "3-4-3", "3-4-1-2"),
    ("2026-06-25", "TUN", "NED", 1, 3, 29, 71, 10, 19, 4, 6, 0.61, 1.65, 4, 6, 0, 0, 0, 0, "5-3-2", "4-3-3"),
    ("2026-06-25", "TUR", "USA", 3, 2, 47, 53, 10, 19, 4, 7, 1.59, 1.80, 2, 9, 0, 1, 0, 0, "4-2-3-1", "4-1-2-3"),
    ("2026-06-25", "PAR", "AUS", 0, 0, 44, 56, 8, 12, 2, 5, 0.42, 0.85, 1, 3, 1, 1, 0, 0, "5-4-1", "3-4-3"),
]

# ---------------------------------------------------------------------------
# Resultados grupos 27-jun (Excel fecha 46200 = 2026-06-27)
# ---------------------------------------------------------------------------
RESULTS_27JUN = [
    ("2026-06-27", "PAN", "ENG", 0, 2, 32, 68, 9, 17, 2, 8, 0.52, 1.36, 3, 7, 2, 1, 0, 0, None, None),
    ("2026-06-27", "CRO", "GHA", 2, 1, 53, 47, 8, 6, 4, 1, 0.53, 0.61, 3, 2, 1, 1, 0, 0, None, None),
    ("2026-06-27", "COL", "POR", 0, 0, 55, 45, 26, 13, 6, 2, 1.38, 0.69, 5, 2, 1, 0, 0, 0, None, None),
    ("2026-06-27", "COD", "UZB", 3, 1, 58, 42, 19, 3, 4, 1, 1.92, 0.23, 2, 4, 3, 2, 0, 0, None, None),
    ("2026-06-27", "DZA", "AUT", 3, 3, 53, 47, 10, 9, 4, 3, 0.93, 0.81, 0, 3, 0, 1, 0, 0, "4-2-3-1", "4-2-3-1"),
    ("2026-06-27", "JOR", "ARG", 1, 3, 30, 70, 5, 13, 1, 5, 0.49, 1.78, 2, 6, 3, 0, 0, 0, None, None),
]

# ---------------------------------------------------------------------------
# Primer partido R16: Canada vs Sudafrica (2026-06-28)
# Resultado: CAN 4-2 RSA (pendiente confirmar estadisticas exactas)
# ---------------------------------------------------------------------------
R16_MATCH = {
    "match_id": "2026-06-28_CAN_RSA",
    "date": "2026-06-28",
    "time_local": "12:00 PM",
    "group": "R16",
    "team_a_id": "CAN",
    "team_b_id": "RSA",
    "team_a_name": "Canadá",
    "team_b_name": "Sudáfrica",
    "status": "scheduled",
    "venue": "SoFi Stadium, Inglewood, California, EUA",
    "source_url": "fifa_world_cup_2026_r16",
}

R16_RESULT = (
    # date, team_a_id, team_b_id, gf_a, gf_b, pos_a, pos_b, shots_a, shots_b,
    # sot_a, sot_b, xg_a, xg_b, corners_a, corners_b, yellow_a, yellow_b, red_a, red_b,
    # form_a, form_b
    # CAN 1-0 RSA: gol de Eustaquio (min. 92). Primer triunfo historico de Canada en
    # fase eliminatoria de un Mundial senior masculino.
    "2026-06-28", "CAN", "RSA", 1, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
)


def build_result_rows(results: list) -> list[dict]:
    cols = [
        "date", "team_a_id", "team_b_id", "team_a_goals", "team_b_goals",
        "team_a_possession", "team_b_possession", "team_a_shots", "team_b_shots",
        "team_a_shots_on_target", "team_b_shots_on_target",
        "team_a_xg", "team_b_xg", "team_a_corners", "team_b_corners",
        "team_a_yellow_cards", "team_b_yellow_cards", "team_a_red_cards", "team_b_red_cards",
        "team_a_formation", "team_b_formation",
    ]
    rows = []
    for r in results:
        row = dict(zip(cols, r))
        row["source_url"] = "manual_excel_27jun2026"
        rows.append(row)
    return rows


def main(dry_run: bool = False) -> None:
    upcoming = pd.read_csv(UPCOMING_PATH)
    matches_current = pd.read_csv(MATCHES_CURRENT_PATH)

    print("=" * 60)
    print(f"upcoming_matches antes: {len(upcoming)} filas")
    print(f"matches_current antes:  {len(matches_current)} filas")

    # ------------------------------------------------------------------
    # 1. Limpiar duplicados del 26-jun: estan ya en matches_current
    #    pero siguen en upcoming como 'scheduled'
    # ------------------------------------------------------------------
    done_26_pairs = set(
        zip(
            matches_current[matches_current["date"] == "2026-06-26"]["team_a_id"],
            matches_current[matches_current["date"] == "2026-06-26"]["team_b_id"],
        )
    )
    # Identificar filas en upcoming del 26-jun que ya estan en matches_current
    mask_26_already_done = upcoming.apply(
        lambda r: r["date"] == "2026-06-26" and (r["team_a_id"], r["team_b_id"]) in done_26_pairs,
        axis=1,
    )
    n_removed_26 = mask_26_already_done.sum()
    print(f"\n[1] Eliminando {n_removed_26} entradas del 26-jun ya ingestadas de upcoming...")
    upcoming = upcoming[~mask_26_already_done].reset_index(drop=True)

    # ------------------------------------------------------------------
    # 2. Agregar el partido R16 a upcoming (antes de ingestar su resultado)
    # ------------------------------------------------------------------
    r16_already = (
        (upcoming["team_a_id"] == R16_MATCH["team_a_id"])
        & (upcoming["team_b_id"] == R16_MATCH["team_b_id"])
        & (upcoming["date"] == R16_MATCH["date"])
    ).any()
    if not r16_already:
        print(f"\n[2] Agregando partido R16 {R16_MATCH['match_id']} a upcoming...")
        upcoming = pd.concat(
            [upcoming, pd.DataFrame([R16_MATCH])], ignore_index=True
        )
    else:
        print("\n[2] Partido R16 ya existe en upcoming, saltando.")

    # ------------------------------------------------------------------
    # 3. Ingestar resultados 25-jun, 27-jun y R16 via resultados_nuevos
    # ------------------------------------------------------------------
    from src.ingest.load_new_results import NEW_RESULTS_COLUMNS, ingest_new_results

    teams = pd.read_csv(PROCESSED_DIR / "teams.csv")

    all_results = RESULTS_25JUN + RESULTS_27JUN + [R16_RESULT]
    result_rows = build_result_rows(all_results)
    new_results_df = pd.DataFrame(result_rows, columns=NEW_RESULTS_COLUMNS)

    print(f"\n[3] Ingiriendo {len(new_results_df)} partidos...")
    matches_current, upcoming, remaining, summary = ingest_new_results(
        new_results_df, upcoming, matches_current, teams
    )

    for s in summary:
        print(f"   OK {s['label']}")

    if not remaining.empty:
        print(f"\n   AVISO: {len(remaining)} resultado(s) sin match en upcoming:")
        print(remaining[["date", "team_a_id", "team_b_id"]].to_string())

    # ------------------------------------------------------------------
    # 4. Guardar
    # ------------------------------------------------------------------
    print(f"\nupcoming_matches despues: {len(upcoming)} filas")
    print(f"matches_current despues:  {len(matches_current)} filas")

    if dry_run:
        print("\n[DRY-RUN] No se guardaron cambios.")
        return

    matches_current.to_csv(MATCHES_CURRENT_PATH, index=False)
    upcoming.to_csv(UPCOMING_PATH, index=False)

    # Dejar resultados_nuevos vacio (ya ingestados)
    new_results_empty = pd.DataFrame(columns=NEW_RESULTS_COLUMNS)
    new_results_empty.to_csv(RAW_DIR / "resultados_nuevos.csv", index=False)

    print("\nArchivos actualizados:")
    print(f"  - {MATCHES_CURRENT_PATH}")
    print(f"  - {UPCOMING_PATH}")
    print(f"  - {RAW_DIR / 'resultados_nuevos.csv'} (vaciado)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest jornada 27-jun + R16 Canada vs Sudafrica.")
    parser.add_argument("--dry-run", action="store_true", help="Muestra que se haria sin guardar.")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
