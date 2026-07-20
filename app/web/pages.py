from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.lib.competitions import COMPETITION_LABELS
from app.lib.team_form import result_for_team
from app.lib.team_search import filter_by_team_name
from app.services.football import get_standings, get_stats_data, get_team_detail
from app.web.deps import get_session
from app.web.partials import match_list_context, parse_competition, standings_table_view_context
from app.web.templating import templates

router = APIRouter()


@router.get("/")
def live_scores(request: Request, session: Session = Depends(get_session)):
    context = match_list_context(request, session)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "page_title": "Live Scores",
            "competition_labels": COMPETITION_LABELS,
            **context,
        },
    )


@router.get("/standings")
def standings(request: Request, session: Session = Depends(get_session)):
    competition = parse_competition(request.query_params.get("competition"))
    query = request.query_params.get("q", "")
    rows = filter_by_team_name(get_standings(session, competition), query)
    context = standings_table_view_context(competition, query, rows)
    return templates.TemplateResponse(
        request,
        "standings.html",
        {
            "page_title": "Standings",
            "competition_labels": COMPETITION_LABELS,
            **context,
        },
    )


def _parse_stats_season(raw: str | None) -> tuple[int | None, bool]:
    if raw == "current":
        return None, False
    if raw is None or raw == "":
        return None, True
    try:
        return int(raw), True
    except ValueError:
        return None, True


@router.get("/stats")
def stats(request: Request, session: Session = Depends(get_session)):
    competition = parse_competition(request.query_params.get("competition"))
    season, default_to_latest = _parse_stats_season(request.query_params.get("season"))
    stats_data = get_stats_data(
        session,
        competition,
        season,
        default_to_latest=default_to_latest,
    )
    return templates.TemplateResponse(
        request,
        "stats.html",
        {
            "page_title": "Stats",
            "competition": competition,
            "competition_labels": COMPETITION_LABELS,
            "stats": stats_data,
            "selected_season_param": (
                "current"
                if stats_data["resolvedSeason"] is None
                else str(stats_data["resolvedSeason"])
            ),
        },
    )


def _recent_result_context(match, team_id: int) -> dict:
    result = result_for_team(match, team_id)
    played = match.home_score is not None and match.away_score is not None
    home_win = played and match.home_score > match.away_score
    away_win = played and match.away_score > match.home_score
    opponent_id = match.away_team_id if match.home_team_id == team_id else match.home_team_id

    return {
        "match": match,
        "result": result,
        "opponent_id": opponent_id,
        "home_win": home_win,
        "away_win": away_win,
    }


@router.get("/teams/{team_id}")
def team_detail(team_id: int, request: Request, session: Session = Depends(get_session)):
    detail = get_team_detail(session, team_id)
    summary = detail["summary"]
    competition = parse_competition(summary.competition_code if summary else None)
    recent_results = [_recent_result_context(match, team_id) for match in detail["recent_matches"]]
    return templates.TemplateResponse(
        request,
        "team_detail.html",
        {
            "page_title": summary.team_name if summary else "Team not found",
            "competition": competition,
            "competition_labels": COMPETITION_LABELS,
            "summary": summary,
            "recent_results": recent_results,
            "team_id": team_id,
        },
    )
