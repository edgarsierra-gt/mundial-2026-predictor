from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import PROCESSED_DIR, RAW_DIR
from src.ingest.load_new_results import NEW_RESULTS_COLUMNS, REQUIRED_COLUMNS, ingest_new_results

NEW_RESULTS_PATH = RAW_DIR / "resultados_nuevos.csv"
INGEST_LOG_PATH = PROCESSED_DIR / "results_ingest_log.csv"


def _read_new_results() -> pd.DataFrame:
    if not NEW_RESULTS_PATH.exists():
        return pd.DataFrame(columns=NEW_RESULTS_COLUMNS)
    df = pd.read_csv(NEW_RESULTS_PATH)
    if df.empty:
        return df
    return df.dropna(subset=REQUIRED_COLUMNS, how="any").reset_index(drop=True)


def main() -> None:
    new_results = _read_new_results()
    if new_results.empty:
        print("OK sin resultados nuevos en data/raw/resultados_nuevos.csv")
        return

    upcoming = pd.read_csv(PROCESSED_DIR / "upcoming_matches.csv")
    matches_current = pd.read_csv(PROCESSED_DIR / "matches_current.csv")
    teams = pd.read_csv(PROCESSED_DIR / "teams.csv")

    matches_current, upcoming, remaining, summary = ingest_new_results(
        new_results, upcoming, matches_current, teams
    )

    matches_current.to_csv(PROCESSED_DIR / "matches_current.csv", index=False)
    upcoming.to_csv(PROCESSED_DIR / "upcoming_matches.csv", index=False)

    remaining_to_write = remaining if not remaining.empty else pd.DataFrame(columns=NEW_RESULTS_COLUMNS)
    remaining_to_write.to_csv(NEW_RESULTS_PATH, index=False)

    if summary:
        log_rows = pd.DataFrame([{"ingested_at": pd.Timestamp.utcnow().isoformat(), **row} for row in summary])
        if INGEST_LOG_PATH.exists():
            log_rows = pd.concat([pd.read_csv(INGEST_LOG_PATH), log_rows], ignore_index=True)
        log_rows.to_csv(INGEST_LOG_PATH, index=False)

    print(f"OK {len(summary)} resultado(s) nuevo(s) ingerido(s):")
    for row in summary:
        print(f"   - {row['label']}")
    if not remaining_to_write.empty:
        print(
            f"AVISO {len(remaining_to_write)} fila(s) en resultados_nuevos.csv no coinciden con "
            "ningun partido en upcoming_matches.csv (revisar fecha y codigos de equipo)."
        )


if __name__ == "__main__":
    main()
