from __future__ import annotations

import pandas as pd

from src.tournament.groups import build_tournament_schedule


def test_build_tournament_schedule_handles_missing_match_no() -> None:
    matches_current = pd.DataFrame(
        [
            {
                "match_id": "2026-06-11_match-1",
                "match_no": 1,
                "date": "2026-06-11",
                "group": "A",
                "team_a_id": "MEX",
                "team_b_id": "RSA",
                "source_url": "https://example.com",
            },
            {
                # Ingested via 00_ingest_results.py: match_no left blank on
                # purpose so match_id stays identical to the frozen prediction.
                "match_id": "2026-06-19_USA_AUS",
                "match_no": None,
                "date": "2026-06-19",
                "group": "D",
                "team_a_id": "USA",
                "team_b_id": "AUS",
                "source_url": "https://example.com",
            },
        ]
    )
    upcoming_matches = pd.DataFrame(
        [
            {
                "match_id": "2026-06-20_GER_CIV",
                "date": "2026-06-20",
                "group": "E",
                "team_a_id": "GER",
                "team_b_id": "CIV",
                "status": "scheduled",
                "source_url": None,
            }
        ]
    )

    schedule = build_tournament_schedule(matches_current, upcoming_matches)

    assert schedule["match_no"].notna().all()
    assert schedule["match_no"].is_unique
    completed = schedule[schedule["match_id"] == "2026-06-19_USA_AUS"].iloc[0]
    assert completed["match_no"] == 2
    scheduled = schedule[schedule["match_id"] == "2026-06-20_GER_CIV"].iloc[0]
    assert scheduled["match_no"] == 3
