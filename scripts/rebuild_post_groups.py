"""
Script de reconstruccion completa post-fase-de-grupos.

Situacion al 28 de junio de 2026:
- Los 72 partidos de fase de grupos ya se jugaron
- El nuevo Excel (27-jun) contiene los 72 resultados de grupos
- Ya se jugo el primer partido de 16avos: CAN 1-0 RSA (gol Eustaquio min. 92)
- Los partidos restantes de 16avos aun no se han jugado

Este script:
1. Reconstruye matches_current.csv desde el Excel nuevo (72 partidos de grupos)
2. Agrega CAN 1-0 RSA como primer partido de knockout
3. Reemplaza upcoming_matches.csv con SOLO los R16 restantes (sin jornadas de grupos)
4. Deja resultados_nuevos.csv vacio

Uso:
    python scripts/rebuild_post_groups.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import CURRENT_WORLD_CUP_XLSX, PROCESSED_DIR, RAW_DIR
from src.ingest.load_new_results import NEW_RESULTS_COLUMNS, MATCHES_CURRENT_COLUMNS
from src.ingest.load_worldcup_current import load_current_workbook

# ---------------------------------------------------------------------------
# Partidos R16 restantes (28 partidos de 16avos menos CAN vs RSA ya jugado)
# Basado en el cruce de la fase de grupos del Mundial 2026
# ---------------------------------------------------------------------------
R16_REMAINING = [
    # match_id, date, time_local, group, team_a_id, team_b_id, team_a_name, team_b_name, venue
    # Fuente: calendario FIFA oficial Mundial 2026
    # Junio 29
    ("2026-06-29_BRA_JPN", "2026-06-29", "TBD", "R16", "BRA", "JPN", "Brasil",          "Japón",           "TBD"),
    ("2026-06-29_GER_PAR", "2026-06-29", "TBD", "R16", "GER", "PAR", "Alemania",        "Paraguay",        "TBD"),
    ("2026-06-29_NED_MAR", "2026-06-29", "TBD", "R16", "NED", "MAR", "Países Bajos",    "Marruecos",       "TBD"),
    # Junio 30
    ("2026-06-30_CIV_NOR", "2026-06-30", "TBD", "R16", "CIV", "NOR", "Costa de Marfil", "Noruega",         "TBD"),
    ("2026-06-30_FRA_SWE", "2026-06-30", "TBD", "R16", "FRA", "SWE", "Francia",         "Suecia",          "TBD"),
    ("2026-06-30_MEX_ECU", "2026-06-30", "TBD", "R16", "MEX", "ECU", "México",          "Ecuador",         "TBD"),
    # Julio 1
    ("2026-07-01_ENG_COD", "2026-07-01", "TBD", "R16", "ENG", "COD", "Inglaterra",      "DR Congo",        "TBD"),
    ("2026-07-01_BEL_SEN", "2026-07-01", "TBD", "R16", "BEL", "SEN", "Bélgica",         "Senegal",         "TBD"),
    ("2026-07-01_USA_BIH", "2026-07-01", "TBD", "R16", "USA", "BIH", "Estados Unidos",  "Bosnia y Herzegovina", "TBD"),
    # Julio 2
    ("2026-07-02_ESP_AUT", "2026-07-02", "TBD", "R16", "ESP", "AUT", "España",          "Austria",         "TBD"),
    ("2026-07-02_POR_CRO", "2026-07-02", "TBD", "R16", "POR", "CRO", "Portugal",        "Croacia",         "TBD"),
    ("2026-07-02_SUI_DZA", "2026-07-02", "TBD", "R16", "SUI", "DZA", "Suiza",           "Argelia",         "TBD"),
    # Julio 3
    ("2026-07-03_AUS_EGY", "2026-07-03", "TBD", "R16", "AUS", "EGY", "Australia",       "Egipto",          "TBD"),
    ("2026-07-03_ARG_CPV", "2026-07-03", "TBD", "R16", "ARG", "CPV", "Argentina",       "Cabo Verde",      "TBD"),
    ("2026-07-03_COL_GHA", "2026-07-03", "TBD", "R16", "COL", "GHA", "Colombia",        "Ghana",           "TBD"),
]

# CAN 1-0 RSA (ya jugado, gol Eustaquio min. 92)
CAN_RSA_RESULT = {
    "match_id": "2026-06-28_CAN_RSA",
    "match_no": None,
    "date": "2026-06-28",
    "group": "R16",
    "team_a_id": "CAN",
    "team_a_name": "Canadá",
    "team_a_goals": 1,
    "team_b_id": "RSA",
    "team_b_name": "Sudáfrica",
    "team_b_goals": 0,
    "total_goals": 1,
    "goal_diff": 1,
    "winner_team_id": "CAN",
    "result_1x2": "1",
    "team_a_possession": None,
    "team_b_possession": None,
    "team_a_shots": None,
    "team_b_shots": None,
    "team_a_shots_on_target": None,
    "team_b_shots_on_target": None,
    "team_a_xg": None,
    "team_b_xg": None,
    "total_xg": None,
    "xg_diff": None,
    "team_a_big_chances": None,
    "team_b_big_chances": None,
    "team_a_corners": None,
    "team_b_corners": None,
    "team_a_yellow_cards": None,
    "team_b_yellow_cards": None,
    "team_a_red_cards": None,
    "team_b_red_cards": None,
    "team_a_formation": None,
    "team_b_formation": None,
    "source_url": "manual_28jun2026_r16_can_1_rsa_0_eustaquio_min92",
    "data_status": "verified",
}


def build_r16_upcoming() -> pd.DataFrame:
    rows = []
    for (match_id, date, time_local, group, a_id, b_id, a_name, b_name, venue) in R16_REMAINING:
        rows.append({
            "match_id": match_id,
            "date": date,
            "time_local": time_local,
            "group": group,
            "team_a_id": a_id,
            "team_b_id": b_id,
            "team_a_name": a_name,
            "team_b_name": b_name,
            "status": "scheduled",
            "venue": venue,
            "source_url": "manual_calendar_r16_2026",
        })
    return pd.DataFrame(rows)


def main(dry_run: bool = False) -> None:
    print("=" * 60)
    print("Reconstruccion post-fase-de-grupos (28-jun-2026)")
    print("=" * 60)

    # 1. Cargar los 72 partidos de grupos del Excel nuevo
    print(f"\n[1] Cargando partidos de grupos desde: {CURRENT_WORLD_CUP_XLSX.name}")
    matches_current, team_match_current, current_teams = load_current_workbook(CURRENT_WORLD_CUP_XLSX)
    print(f"    {len(matches_current)} partidos de grupos cargados")

    # 2. Agregar CAN 1-0 RSA a matches_current
    print("\n[2] Agregando CAN 1-0 RSA (R16, gol Eustaquio min. 92)...")
    can_rsa_df = pd.DataFrame([CAN_RSA_RESULT], columns=MATCHES_CURRENT_COLUMNS)
    matches_current = pd.concat([matches_current, can_rsa_df], ignore_index=True)
    print(f"    Total partidos en matches_current: {len(matches_current)}")

    # 3. Construir upcoming con solo los R16 restantes
    print("\n[3] Construyendo upcoming_matches con R16 restantes...")
    upcoming = build_r16_upcoming()
    print(f"    {len(upcoming)} partidos de R16 pendientes")

    # Mostrar resumen
    print("\nResumen upcoming R16:")
    for _, r in upcoming.iterrows():
        print(f"    {r['date']} | {r['team_a_id']} vs {r['team_b_id']}")

    # 4. Vaciar resultados_nuevos.csv
    print("\n[4] Vaciando resultados_nuevos.csv...")

    if dry_run:
        print("\n[DRY-RUN] No se guardaron cambios.")
        return

    matches_current.to_csv(PROCESSED_DIR / "matches_current.csv", index=False)
    upcoming.to_csv(PROCESSED_DIR / "upcoming_matches.csv", index=False)

    empty = pd.DataFrame(columns=NEW_RESULTS_COLUMNS)
    empty.to_csv(RAW_DIR / "resultados_nuevos.csv", index=False)

    print("\nArchivos actualizados:")
    print(f"  - data/processed/matches_current.csv ({len(matches_current)} filas)")
    print(f"  - data/processed/upcoming_matches.csv ({len(upcoming)} filas)")
    print("  - data/raw/resultados_nuevos.csv (vacio)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruir modelo post-fase-de-grupos.")
    parser.add_argument("--dry-run", action="store_true", help="Muestra que se haria sin guardar.")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
