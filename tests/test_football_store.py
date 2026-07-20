from types import SimpleNamespace

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Competition, Match, StandingsSnapshot, Team
from app.store.football_store import (
    insert_standings_snapshot,
    read_available_seasons,
    read_finished_matches_for_season,
    read_latest_standings,
    read_matches,
    read_team_detail,
    read_team_form,
    upsert_competition,
    upsert_matches,
)


def competition(
    id: int = 1,
    code: str = "PL",
    name: str = "Premier League",
    area: str = "England",
    emblem_url: str = "https://example.com/pl.png",
) -> SimpleNamespace:
    return SimpleNamespace(id=id, code=code, name=name, area=area, emblem_url=emblem_url)


def team(
    id: int,
    name: str,
    short_name: str | None = None,
    tla: str | None = None,
    crest_url: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        name=name,
        short_name=short_name,
        tla=tla,
        crest_url=crest_url,
    )


def match(
    id: int,
    home_team: SimpleNamespace,
    away_team: SimpleNamespace,
    *,
    competition_id: int = 1,
    utc_date: str = "2025-08-01T15:00:00Z",
    matchday: int | None = 1,
    status: str = "SCHEDULED",
    home_score: int | None = None,
    away_score: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        competition_id=competition_id,
        utc_date=utc_date,
        matchday=matchday,
        status=status,
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
    )


def standing(
    team_value: SimpleNamespace,
    *,
    position: int = 1,
    played_games: int = 1,
    won: int = 1,
    draw: int = 0,
    lost: int = 0,
    points: int = 3,
    goals_for: int = 2,
    goals_against: int = 0,
    goal_difference: float = 2,
) -> SimpleNamespace:
    return SimpleNamespace(
        team=team_value,
        position=position,
        played_games=played_games,
        won=won,
        draw=draw,
        lost=lost,
        points=points,
        goals_for=goals_for,
        goals_against=goals_against,
        goal_difference=goal_difference,
    )


def seed_competition(session: Session) -> None:
    upsert_competition(session, competition(), now=1000)


def seed_matches(session: Session) -> tuple[SimpleNamespace, SimpleNamespace, SimpleNamespace]:
    seed_competition(session)
    arsenal = team(10, "Arsenal", "Arsenal", "ARS", "arsenal.png")
    chelsea = team(20, "Chelsea", "Chelsea", "CHE", "chelsea.png")
    united = team(30, "Manchester United", "Man United", "MUN", "united.png")
    upsert_matches(
        session,
        [
            match(
                100,
                arsenal,
                chelsea,
                utc_date="2025-08-01T15:00:00Z",
                status="FINISHED",
                home_score=2,
                away_score=1,
            ),
            match(
                101,
                chelsea,
                united,
                utc_date="2025-08-08T15:00:00Z",
                status="TIMED",
            ),
            match(
                102,
                united,
                arsenal,
                utc_date="2024-08-01T15:00:00Z",
                status="FINISHED",
                home_score=3,
                away_score=0,
            ),
        ],
        now=1100,
    )
    return arsenal, chelsea, united


def test_upsert_competition_inserts_and_updates(session: Session) -> None:
    upsert_competition(session, competition(name="Old name"), now=1000)
    upsert_competition(session, competition(name="New name", area="UK"), now=2000)

    row = session.get(Competition, 1)

    assert row is not None
    assert row.name == "New name"
    assert row.area == "UK"
    assert row.fetched_at == 2000
    assert session.scalar(select(func.count()).select_from(Competition)) == 1


def test_upsert_matches_is_idempotent_and_upserts_teams(session: Session) -> None:
    seed_competition(session)
    arsenal = team(10, "Arsenal", "Arsenal", "ARS", "arsenal.png")
    chelsea = team(20, "Chelsea", "Chelsea", "CHE", "chelsea.png")
    first = match(100, arsenal, chelsea, status="SCHEDULED")
    updated = match(
        100,
        team(10, "Arsenal FC", "Arsenal", "ARS", "new-arsenal.png"),
        chelsea,
        utc_date="2025-08-02T15:00:00Z",
        status="FINISHED",
        home_score=2,
        away_score=0,
    )

    upsert_matches(session, [first], now=1000)
    upsert_matches(session, [updated], now=2000)

    stored_match = session.get(Match, 100)
    stored_team = session.get(Team, 10)
    assert stored_match is not None
    assert stored_team is not None
    assert stored_match.status == "FINISHED"
    assert stored_match.utc_date == "2025-08-02T15:00:00Z"
    assert stored_match.home_score == 2
    assert stored_match.fetched_at == 2000
    assert stored_team.name == "Arsenal FC"
    assert stored_team.crest_url == "new-arsenal.png"
    assert session.scalar(select(func.count()).select_from(Match)) == 1
    assert session.scalar(select(func.count()).select_from(Team)) == 2


def test_insert_standings_snapshot_appends_rows(session: Session) -> None:
    seed_competition(session)
    arsenal = team(10, "Arsenal", "Arsenal", "ARS", "arsenal.png")

    insert_standings_snapshot(session, 1, [standing(arsenal, points=3)], captured_at=1000)
    insert_standings_snapshot(session, 1, [standing(arsenal, points=4)], captured_at=2000)

    assert session.scalar(select(func.count()).select_from(StandingsSnapshot)) == 2
    assert session.get(Team, 10) is not None


def test_read_matches_returns_current_season_only(session: Session) -> None:
    arsenal, chelsea, _ = seed_matches(session)
    upsert_matches(
        session,
        [
            match(
                200,
                arsenal,
                chelsea,
                utc_date="2024-08-01T15:00:00Z",
                status="FINISHED",
                home_score=1,
                away_score=1,
            )
        ],
        now=1200,
        season=2024,
    )

    rows = read_matches(session, 1)

    assert [row.id for row in rows] == [102, 100, 101]
    assert rows[1].home_team == "Arsenal"
    assert rows[1].home_team_tla == "ARS"
    assert rows[1].away_crest == "chelsea.png"


def test_read_latest_standings_uses_latest_nonempty_snapshot(session: Session) -> None:
    seed_competition(session)
    arsenal = team(10, "Arsenal", "Arsenal", "ARS", "arsenal.png")
    chelsea = team(20, "Chelsea", "Chelsea", "CHE", "chelsea.png")
    insert_standings_snapshot(
        session,
        1,
        [
            standing(arsenal, position=1, played_games=3, points=9),
            standing(chelsea, position=2, played_games=3, points=6),
        ],
        captured_at=1000,
    )
    insert_standings_snapshot(
        session,
        1,
        [
            standing(chelsea, position=1, played_games=0, points=0),
            standing(arsenal, position=2, played_games=0, points=0),
        ],
        captured_at=2000,
    )

    rows = read_latest_standings(session, 1)

    assert [row.team_name for row in rows] == ["Arsenal", "Chelsea"]
    assert [row.played_games for row in rows] == [3, 3]


def test_read_team_detail_prefers_played_snapshots(session: Session) -> None:
    seed_competition(session)
    arsenal = team(10, "Arsenal", "Arsenal", "ARS", "arsenal.png")
    insert_standings_snapshot(
        session,
        1,
        [standing(arsenal, position=1, played_games=2, points=6)],
        captured_at=1000,
    )
    insert_standings_snapshot(
        session,
        1,
        [standing(arsenal, position=20, played_games=0, points=0)],
        captured_at=2000,
    )

    detail = read_team_detail(session, 10)

    assert detail is not None
    assert detail.team_name == "Arsenal"
    assert detail.competition_code == "PL"
    assert detail.position == 1
    assert detail.played_games == 2
    assert detail.captured_at == 1000


def test_read_team_form_filters_finished_matches_and_limits(session: Session) -> None:
    arsenal, chelsea, united = seed_matches(session)
    upsert_matches(
        session,
        [
            match(
                103,
                arsenal,
                united,
                utc_date="2025-08-15T15:00:00Z",
                status="FINISHED",
                home_score=4,
                away_score=0,
            ),
            match(
                104,
                chelsea,
                arsenal,
                utc_date="2025-08-22T15:00:00Z",
                status="FINISHED",
                home_score=1,
                away_score=1,
            ),
        ],
        now=1200,
    )

    rows = read_team_form(session, 10, limit=2)

    assert len(rows) == 2
    assert 101 not in [row.id for row in rows]
    assert all(row.home_team_id == 10 or row.away_team_id == 10 for row in rows)


def test_read_finished_matches_for_season_reads_requested_season(session: Session) -> None:
    arsenal, chelsea, united = seed_matches(session)
    upsert_matches(
        session,
        [
            match(
                200,
                chelsea,
                arsenal,
                utc_date="2024-09-01T15:00:00Z",
                matchday=2,
                status="FINISHED",
                home_score=None,
                away_score=2,
            ),
            match(
                201,
                united,
                chelsea,
                utc_date="2024-08-01T15:00:00Z",
                matchday=1,
                status="FINISHED",
                home_score=1,
                away_score=None,
            ),
            match(
                202,
                arsenal,
                united,
                utc_date="2024-08-10T15:00:00Z",
                matchday=1,
                status="SCHEDULED",
            ),
        ],
        now=1300,
        season=2024,
    )

    historical = read_finished_matches_for_season(session, 1, 2024)
    current = read_finished_matches_for_season(session, 1, None)

    assert [row.home_team for row in historical] == ["Manchester United", "Chelsea"]
    assert historical[0].away_score == 0
    assert historical[1].home_score == 0
    assert [row.home_team for row in current] == ["Manchester United", "Arsenal"]


def test_read_available_seasons_sorted_desc(session: Session) -> None:
    arsenal, chelsea, united = seed_matches(session)
    upsert_matches(
        session,
        [
            match(200, arsenal, chelsea, status="FINISHED", home_score=1, away_score=0),
            match(201, united, chelsea, status="FINISHED", home_score=1, away_score=1),
            match(202, arsenal, united, status="SCHEDULED"),
        ],
        now=1300,
        season=2023,
    )
    upsert_matches(
        session,
        [match(300, arsenal, chelsea, status="FINISHED", home_score=2, away_score=0)],
        now=1400,
        season=2025,
    )

    assert read_available_seasons(session, 1) == [2025, 2023]
