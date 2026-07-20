from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.lib.competitions import COMPETITION_LABELS, is_competition_code
from app.lib.match_display import order_matches, paginate
from app.lib.team_search import filter_by_team_name
from app.services.football import get_matches, get_standings
from app.web.deps import get_session
from app.web.templating import templates

router = APIRouter(prefix="/partials")


def parse_competition(raw: str | None) -> str:
    return raw if raw is not None and is_competition_code(raw) else "PL"


def parse_page(raw: str | None) -> int:
    try:
        page = int(raw or "1")
    except ValueError:
        return 1
    return page if page > 0 else 1


def match_list_context(request: Request, session: Session) -> dict[str, object]:
    competition = parse_competition(request.query_params.get("competition"))
    page = parse_page(request.query_params.get("page"))
    matches = order_matches(get_matches(session, competition))
    match_page = paginate(matches, page)
    return {
        "competition": competition,
        "competition_labels": COMPETITION_LABELS,
        "match_page": match_page,
    }


def zone_for(position: int, total_teams: int) -> str | None:
    if position <= 4:
        return "ucl"
    if position == 5:
        return "uel"
    if position > total_teams - 3:
        return "rel"
    return None


def standings_table_view_context(
    competition: str, query: str, rows: list[object]
) -> dict[str, object]:
    has_search = query.strip() != ""
    positions = [getattr(row, "position") for row in rows]
    show_zones = not has_search and len(rows) >= 8 and len(set(positions)) == len(positions)
    return {
        "competition": competition,
        "competition_labels": COMPETITION_LABELS,
        "q": query,
        "standings_rows": rows,
        "has_search": has_search,
        "show_zones": show_zones,
        "zone_for": zone_for,
    }


def standings_table_context(request: Request, session: Session) -> dict[str, object]:
    competition = parse_competition(request.query_params.get("competition"))
    query = request.query_params.get("q", "")
    rows = filter_by_team_name(get_standings(session, competition), query)
    return standings_table_view_context(competition, query, rows)


@router.get("/matches")
def matches_partial(request: Request, session: Session = Depends(get_session)):
    return templates.TemplateResponse(
        request,
        "partials/match_list.html",
        match_list_context(request, session),
    )


@router.get("/standings-table")
def standings_table_partial(request: Request, session: Session = Depends(get_session)):
    context = standings_table_context(request, session)
    response = templates.TemplateResponse(
        request,
        "partials/standings_table.html",
        context,
    )
    push_params = {"competition": context["competition"]}
    if str(context["q"]).strip() != "":
        push_params["q"] = context["q"]
    response.headers["HX-Push-Url"] = "/standings?" + urlencode(push_params)
    return response
