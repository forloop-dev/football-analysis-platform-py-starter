from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Competition
from app.lib.competitions import TRACKED_COMPETITIONS
from app.store.football_store import (
    read_available_seasons,
    read_finished_matches_for_season,
    read_latest_standings,
    read_matches,
    read_team_detail,
    read_team_form,
)


def assert_tracked_code(code: str) -> str:
    if code not in TRACKED_COMPETITIONS:
        raise ValueError(f"Unsupported competition code: {code}")
    return code


def competition_id_for_code(session: Session, code: str) -> int | None:
    return session.execute(
        select(Competition.id).where(Competition.code == code)
    ).scalar_one_or_none()


def get_matches(session: Session, code: str) -> list[Any]:
    competition_id = competition_id_for_code(session, assert_tracked_code(code))
    return [] if competition_id is None else read_matches(session, competition_id)


def get_standings(session: Session, code: str) -> list[Any]:
    competition_id = competition_id_for_code(session, assert_tracked_code(code))
    return [] if competition_id is None else read_latest_standings(session, competition_id)


def get_team_detail(session: Session, team_id: int) -> dict[str, Any]:
    if not isinstance(team_id, int) or team_id <= 0:
        raise ValueError(f"Invalid team id: {team_id}")
    return {
        "summary": read_team_detail(session, team_id),
        "recent_matches": read_team_form(session, team_id, 5),
    }


def get_stats_data(
    session: Session,
    code: str,
    season: int | None,
    *,
    default_to_latest: bool = True,
) -> dict[str, Any]:
    code = assert_tracked_code(code)
    competition = session.execute(
        select(Competition.id, Competition.name).where(Competition.code == code)
    ).first()

    if competition is None:
        return {
            "code": code,
            "name": code,
            "availableSeasons": [],
            "resolvedSeason": None,
            "matches": [],
        }

    available_seasons = read_available_seasons(session, competition.id)
    if season in available_seasons:
        resolved_season = season
    elif default_to_latest:
        resolved_season = next(iter(available_seasons), None)
    else:
        resolved_season = None
    matches = read_finished_matches_for_season(session, competition.id, resolved_season)

    return {
        "code": code,
        "name": competition.name,
        "availableSeasons": available_seasons,
        "resolvedSeason": resolved_season,
        "matches": matches,
    }
