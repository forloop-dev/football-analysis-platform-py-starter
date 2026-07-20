from dataclasses import dataclass

from app.lib.team_form import result_for_team


@dataclass(frozen=True)
class FormMatch:
    home_team_id: int
    away_team_id: int
    home_score: int | None
    away_score: int | None


def test_result_for_team_reads_home_team_result() -> None:
    match = FormMatch(home_team_id=1, away_team_id=2, home_score=2, away_score=1)

    assert result_for_team(match, 1) == "W"


def test_result_for_team_returns_none_without_scores() -> None:
    match = FormMatch(home_team_id=1, away_team_id=2, home_score=None, away_score=None)

    assert result_for_team(match, 1) is None
