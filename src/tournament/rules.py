from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.config import DIRECT_QUALIFIERS_PER_GROUP, THIRD_PLACE_QUALIFIERS


@dataclass
class TeamStanding:
    group: str
    team_id: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def record_match(self, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.wins += 1
            self.points += 3
        elif goals_for == goals_against:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1

    def as_dict(self) -> dict[str, int | str]:
        return {
            "group": self.group,
            "team_id": self.team_id,
            "played": self.played,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "goal_difference": self.goal_difference,
            "points": self.points,
        }


def empty_standings(teams: pd.DataFrame) -> dict[str, TeamStanding]:
    return {
        row.team_id: TeamStanding(group=str(row.group), team_id=str(row.team_id))
        for row in teams.itertuples()
    }


def apply_match(
    standings: dict[str, TeamStanding],
    team_a_id: str,
    team_b_id: str,
    team_a_goals: int,
    team_b_goals: int,
) -> None:
    standings[team_a_id].record_match(team_a_goals, team_b_goals)
    standings[team_b_id].record_match(team_b_goals, team_a_goals)


def standings_to_frame(standings: dict[str, TeamStanding]) -> pd.DataFrame:
    rows = [standing.as_dict() for standing in standings.values()]
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def rank_standings(standings: pd.DataFrame) -> pd.DataFrame:
    if standings.empty:
        return standings.copy()
    ranked = standings.sort_values(
        ["group", "points", "goal_difference", "goals_for", "team_id"],
        ascending=[True, False, False, False, True],
    ).copy()
    ranked["rank_current"] = ranked.groupby("group").cumcount() + 1
    return ranked.reset_index(drop=True)


def direct_qualifiers(ranked_standings: pd.DataFrame) -> set[str]:
    direct = ranked_standings.loc[
        ranked_standings["rank_current"] <= DIRECT_QUALIFIERS_PER_GROUP,
        "team_id",
    ]
    return set(direct.tolist())


def third_place_qualifiers(ranked_standings: pd.DataFrame) -> set[str]:
    third_place = ranked_standings.loc[ranked_standings["rank_current"] == 3].copy()
    third_place = third_place.sort_values(
        ["points", "goal_difference", "goals_for", "team_id"],
        ascending=[False, False, False, True],
    )
    return set(third_place.head(THIRD_PLACE_QUALIFIERS)["team_id"].tolist())


def classify_teams(ranked_standings: pd.DataFrame) -> pd.DataFrame:
    classified = ranked_standings.copy()
    direct = direct_qualifiers(classified)
    third = third_place_qualifiers(classified)
    classified["qualified_direct"] = classified["team_id"].isin(direct)
    classified["qualified_as_third"] = classified["team_id"].isin(third)
    classified["qualified_group"] = classified["qualified_direct"] | classified["qualified_as_third"]
    classified["eliminated_group"] = ~classified["qualified_group"]
    return classified
