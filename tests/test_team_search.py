from dataclasses import dataclass

from app.lib.team_search import filter_by_team_name


@dataclass(frozen=True)
class Row:
    team_name: str
    team_short_name: str | None
    team_tla: str | None
    points: int


ROWS = [
    Row(team_name="Arsenal FC", team_short_name="Arsenal", team_tla="ARS", points=10),
    Row(team_name="Chelsea FC", team_short_name="Chelsea", team_tla="CHE", points=8),
    Row(
        team_name="Manchester United FC",
        team_short_name="Man United",
        team_tla="MUN",
        points=12,
    ),
]


def test_matches_team_names() -> None:
    assert filter_by_team_name(ROWS, "Arsenal") == [ROWS[0]]


def test_returns_every_row_for_an_empty_query() -> None:
    assert filter_by_team_name(ROWS, "") == ROWS


def test_matches_team_abbreviations() -> None:
    assert filter_by_team_name(ROWS, "MUN") == [ROWS[2]]
