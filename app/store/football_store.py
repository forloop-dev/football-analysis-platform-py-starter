from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import RowMapping, and_, case, desc, func, or_, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session, aliased

from app.db.models import Competition, Match, StandingsSnapshot, Team


@dataclass(frozen=True)
class MatchView:
    id: int
    utc_date: str
    matchday: int | None
    status: str
    home_team_id: int
    home_team: str
    home_team_tla: str | None
    home_crest: str | None
    away_team_id: int
    away_team: str
    away_team_tla: str | None
    away_crest: str | None
    home_score: int | None
    away_score: int | None


@dataclass(frozen=True)
class StandingRow:
    team_id: int
    team_name: str
    team_short_name: str | None
    team_tla: str | None
    crest: str | None
    position: int
    played_games: int
    won: int
    draw: int
    lost: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: float


@dataclass(frozen=True)
class TeamDetail:
    team_id: int
    team_name: str
    crest: str | None
    competition_id: int
    competition_code: str
    competition_name: str
    position: int
    played_games: int
    won: int
    draw: int
    lost: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: float
    captured_at: int


@dataclass(frozen=True)
class TeamMatchView:
    id: int
    utc_date: str
    matchday: int | None
    home_team_id: int
    away_team_id: int
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None


@dataclass(frozen=True)
class SeasonMatch:
    matchday: int | None
    utc_date: str
    home_team_id: int
    away_team_id: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int


def _field(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value[name]
    return getattr(value, name)


def _team_values(team: Any) -> dict[str, Any]:
    return {
        "id": _field(team, "id"),
        "name": _field(team, "name"),
        "short_name": _field(team, "short_name"),
        "tla": _field(team, "tla"),
        "crest_url": _field(team, "crest_url"),
    }


def _upsert_teams(session: Session, teams: list[Any]) -> None:
    unique = {_field(team, "id"): team for team in teams}
    for team in unique.values():
        values = _team_values(team)
        statement = insert(Team).values(**values)
        session.execute(
            statement.on_conflict_do_update(
                index_elements=[Team.id],
                set_={
                    "name": values["name"],
                    "short_name": values["short_name"],
                    "tla": values["tla"],
                    "crest_url": values["crest_url"],
                },
            )
        )


def upsert_competition(session: Session, competition: Any, now: int) -> None:
    values = {
        "id": _field(competition, "id"),
        "code": _field(competition, "code"),
        "name": _field(competition, "name"),
        "area": _field(competition, "area"),
        "emblem_url": _field(competition, "emblem_url"),
        "fetched_at": now,
    }
    statement = insert(Competition).values(**values)
    session.execute(
        statement.on_conflict_do_update(
            index_elements=[Competition.id],
            set_={
                "code": values["code"],
                "name": values["name"],
                "area": values["area"],
                "emblem_url": values["emblem_url"],
                "fetched_at": now,
            },
        )
    )


def upsert_matches(
    session: Session, matches: list[Any], now: int, season: int | None = None
) -> None:
    _upsert_teams(
        session,
        [
            team
            for match in matches
            for team in (_field(match, "home_team"), _field(match, "away_team"))
        ],
    )

    for match in matches:
        home_team = _field(match, "home_team")
        away_team = _field(match, "away_team")
        values = {
            "id": _field(match, "id"),
            "competition_id": _field(match, "competition_id"),
            "utc_date": _field(match, "utc_date"),
            "matchday": _field(match, "matchday"),
            "season": season,
            "status": _field(match, "status"),
            "home_team_id": _field(home_team, "id"),
            "away_team_id": _field(away_team, "id"),
            "home_score": _field(match, "home_score"),
            "away_score": _field(match, "away_score"),
            "fetched_at": now,
        }
        statement = insert(Match).values(**values)
        session.execute(
            statement.on_conflict_do_update(
                index_elements=[Match.id],
                set_={
                    "utc_date": values["utc_date"],
                    "matchday": values["matchday"],
                    "season": values["season"],
                    "status": values["status"],
                    "home_score": values["home_score"],
                    "away_score": values["away_score"],
                    "fetched_at": values["fetched_at"],
                },
            )
        )


def insert_standings_snapshot(
    session: Session,
    competition_id: int,
    rows: list[Any],
    captured_at: int,
    season: int | None = None,
) -> None:
    _upsert_teams(session, [_field(row, "team") for row in rows])

    if not rows:
        return

    session.execute(
        insert(StandingsSnapshot),
        [
            {
                "competition_id": competition_id,
                "season": season,
                "captured_at": captured_at,
                "team_id": _field(_field(row, "team"), "id"),
                "position": _field(row, "position"),
                "played_games": _field(row, "played_games"),
                "won": _field(row, "won"),
                "draw": _field(row, "draw"),
                "lost": _field(row, "lost"),
                "points": _field(row, "points"),
                "goals_for": _field(row, "goals_for"),
                "goals_against": _field(row, "goals_against"),
                "goal_difference": _field(row, "goal_difference"),
            }
            for row in rows
        ],
    )


def _from_mapping(row_type: type[Any], row: RowMapping) -> Any:
    return row_type(**dict(row))


def read_matches(session: Session, competition_id: int) -> list[MatchView]:
    home = aliased(Team, name="home")
    away = aliased(Team, name="away")
    statement = (
        select(
            Match.id.label("id"),
            Match.utc_date.label("utc_date"),
            Match.matchday.label("matchday"),
            Match.status.label("status"),
            home.id.label("home_team_id"),
            home.name.label("home_team"),
            home.tla.label("home_team_tla"),
            home.crest_url.label("home_crest"),
            away.id.label("away_team_id"),
            away.name.label("away_team"),
            away.tla.label("away_team_tla"),
            away.crest_url.label("away_crest"),
            Match.home_score.label("home_score"),
            Match.away_score.label("away_score"),
        )
        .join(home, Match.home_team_id == home.id)
        .join(away, Match.away_team_id == away.id)
        .where(and_(Match.competition_id == competition_id, Match.season.is_(None)))
        .order_by(Match.utc_date)
    )
    return [_from_mapping(MatchView, row) for row in session.execute(statement).mappings()]


def read_latest_standings(session: Session, competition_id: int) -> list[StandingRow]:
    latest_nonempty_snapshot = (
        select(func.max(StandingsSnapshot.captured_at))
        .where(
            and_(
                StandingsSnapshot.competition_id == competition_id,
                StandingsSnapshot.played_games > 0,
            )
        )
        .scalar_subquery()
    )
    statement = (
        select(
            StandingsSnapshot.team_id.label("team_id"),
            Team.name.label("team_name"),
            Team.short_name.label("team_short_name"),
            Team.tla.label("team_tla"),
            Team.crest_url.label("crest"),
            StandingsSnapshot.position.label("position"),
            StandingsSnapshot.played_games.label("played_games"),
            StandingsSnapshot.won.label("won"),
            StandingsSnapshot.draw.label("draw"),
            StandingsSnapshot.lost.label("lost"),
            StandingsSnapshot.points.label("points"),
            StandingsSnapshot.goals_for.label("goals_for"),
            StandingsSnapshot.goals_against.label("goals_against"),
            StandingsSnapshot.goal_difference.label("goal_difference"),
        )
        .join(Team, StandingsSnapshot.team_id == Team.id)
        .where(
            and_(
                StandingsSnapshot.competition_id == competition_id,
                StandingsSnapshot.captured_at == latest_nonempty_snapshot,
            )
        )
        .order_by(StandingsSnapshot.position)
    )
    return [_from_mapping(StandingRow, row) for row in session.execute(statement).mappings()]


def read_team_detail(session: Session, team_id: int) -> TeamDetail | None:
    statement = (
        select(
            Team.id.label("team_id"),
            Team.name.label("team_name"),
            Team.crest_url.label("crest"),
            Competition.id.label("competition_id"),
            Competition.code.label("competition_code"),
            Competition.name.label("competition_name"),
            StandingsSnapshot.position.label("position"),
            StandingsSnapshot.played_games.label("played_games"),
            StandingsSnapshot.won.label("won"),
            StandingsSnapshot.draw.label("draw"),
            StandingsSnapshot.lost.label("lost"),
            StandingsSnapshot.points.label("points"),
            StandingsSnapshot.goals_for.label("goals_for"),
            StandingsSnapshot.goals_against.label("goals_against"),
            StandingsSnapshot.goal_difference.label("goal_difference"),
            StandingsSnapshot.captured_at.label("captured_at"),
        )
        .join(Team, StandingsSnapshot.team_id == Team.id)
        .join(Competition, StandingsSnapshot.competition_id == Competition.id)
        .where(StandingsSnapshot.team_id == team_id)
        .order_by(
            desc(case((StandingsSnapshot.played_games > 0, 1), else_=0)),
            desc(StandingsSnapshot.captured_at),
        )
        .limit(1)
    )
    row = session.execute(statement).mappings().first()
    return None if row is None else _from_mapping(TeamDetail, row)


def read_team_form(session: Session, team_id: int, limit: int = 5) -> list[TeamMatchView]:
    home = aliased(Team, name="home")
    away = aliased(Team, name="away")
    statement = (
        select(
            Match.id.label("id"),
            Match.utc_date.label("utc_date"),
            Match.matchday.label("matchday"),
            Match.home_team_id.label("home_team_id"),
            Match.away_team_id.label("away_team_id"),
            home.name.label("home_team"),
            away.name.label("away_team"),
            Match.home_score.label("home_score"),
            Match.away_score.label("away_score"),
        )
        .join(home, Match.home_team_id == home.id)
        .join(away, Match.away_team_id == away.id)
        .where(
            and_(
                Match.status == "FINISHED",
                or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            )
        )
        .order_by(desc(Match.utc_date))
        .limit(limit)
    )
    return [_from_mapping(TeamMatchView, row) for row in session.execute(statement).mappings()]


def read_finished_matches_for_season(
    session: Session, competition_id: int, season: int | None
) -> list[SeasonMatch]:
    home = aliased(Team, name="home")
    away = aliased(Team, name="away")
    season_filter = Match.season.is_(None) if season is None else Match.season == season
    statement = (
        select(
            Match.matchday.label("matchday"),
            Match.utc_date.label("utc_date"),
            Match.home_team_id.label("home_team_id"),
            Match.away_team_id.label("away_team_id"),
            home.name.label("home_team"),
            away.name.label("away_team"),
            func.coalesce(Match.home_score, 0).label("home_score"),
            func.coalesce(Match.away_score, 0).label("away_score"),
        )
        .join(home, Match.home_team_id == home.id)
        .join(away, Match.away_team_id == away.id)
        .where(
            and_(
                Match.competition_id == competition_id,
                season_filter,
                Match.status == "FINISHED",
            )
        )
        .order_by(Match.matchday, Match.utc_date)
    )
    return [_from_mapping(SeasonMatch, row) for row in session.execute(statement).mappings()]


def read_available_seasons(session: Session, competition_id: int) -> list[int]:
    statement = (
        select(Match.season)
        .distinct()
        .where(
            and_(
                Match.competition_id == competition_id,
                Match.season.is_not(None),
                Match.status == "FINISHED",
            )
        )
        .order_by(desc(Match.season))
    )
    return list(session.execute(statement).scalars())
