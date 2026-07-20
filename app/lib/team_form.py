from __future__ import annotations

from typing import Protocol

from app.lib.league_stats import ResultChar, result_char


class TeamFormMatch(Protocol):
    home_team_id: int
    away_team_id: int
    home_score: int | None
    away_score: int | None


def result_for_team(match: TeamFormMatch, team_id: int) -> ResultChar | None:
    if match.home_score is None or match.away_score is None:
        return None
    if match.home_team_id == team_id:
        return result_char(match.home_score, match.away_score)
    if match.away_team_id == team_id:
        return result_char(match.home_score, match.away_score)
    return None
