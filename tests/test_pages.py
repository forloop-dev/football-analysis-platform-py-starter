from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.main import create_app
from app.services.football import assert_tracked_code
from app.web.deps import get_session


def test_healthz() -> None:
    client = TestClient(create_app())

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_base_shell_renders_sidebar_nav() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Live Scores" in response.text
    assert "Standings" in response.text
    assert "Stats" in response.text


def test_index_defaults_to_pl_page_1() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Live Scores" in response.text
    assert 'option value="PL" selected' in response.text
    assert "Page 1 of" in response.text


def test_index_invalid_competition_falls_back_to_pl() -> None:
    client = TestClient(create_app())

    response = client.get("/?competition=XX")

    assert response.status_code == 200
    assert 'option value="PL" selected' in response.text


def test_index_page_2_shows_different_matches() -> None:
    client = TestClient(create_app())

    page_1 = client.get("/?competition=PL&page=1")
    page_2 = client.get("/?competition=PL&page=2")

    assert page_1.status_code == 200
    assert page_2.status_code == 200
    assert "Page 1 of" in page_1.text
    assert "Page 2 of" in page_2.text
    assert page_1.text != page_2.text


def test_matches_partial_returns_fragment_without_shell() -> None:
    client = TestClient(create_app())

    response = client.get("/partials/matches?competition=PL&page=2")

    assert response.status_code == 200
    assert "Page 2 of" in response.text
    assert "<!doctype html>" not in response.text
    assert "Football Explorer" not in response.text


def test_standings_renders_20_rows_for_pl() -> None:
    client = TestClient(create_app())

    response = client.get("/standings?competition=PL")

    assert response.status_code == 200
    assert "Standings" in response.text
    assert 'option value="PL" selected' in response.text
    assert response.text.count('href="/teams/') == 20
    assert "Champions League" in response.text
    assert "Relegation" in response.text


def test_standings_q_filters_rows_case_insensitively() -> None:
    client = TestClient(create_app())

    response = client.get("/standings?competition=PL&q=ARS")

    assert response.status_code == 200
    assert "Arsenal FC" in response.text
    assert "Manchester City FC" not in response.text
    assert response.text.count('href="/teams/') == 1


def test_standings_q_no_matches_shows_empty_state() -> None:
    client = TestClient(create_app())

    response = client.get("/standings?competition=PL&q=not-a-real-team")

    assert response.status_code == 200
    assert "No teams found" in response.text
    assert "Try a different team name." in response.text


def test_standings_partial_omits_zone_legend_when_searching() -> None:
    client = TestClient(create_app())

    response = client.get("/partials/standings-table?competition=PL&q=Man")

    assert response.status_code == 200
    assert "Manchester City FC" in response.text
    assert "Manchester United FC" in response.text
    assert "Champions League" not in response.text
    assert "<!doctype html>" not in response.text
    assert response.headers["HX-Push-Url"] == "/standings?competition=PL&q=Man"


def test_team_detail_renders_summary_tiles() -> None:
    client = TestClient(create_app())

    response = client.get("/teams/57")

    assert response.status_code == 200
    assert "Arsenal FC" in response.text
    assert "Premier League" in response.text
    assert "Points" in response.text
    assert "Record" in response.text
    assert "Goals" in response.text
    assert "Goal difference" in response.text


def test_team_detail_recent_results_have_wdl_chips() -> None:
    client = TestClient(create_app())

    response = client.get("/teams/57")

    assert response.status_code == 200
    assert "Recent Results" in response.text
    assert any(f">{result}<" in response.text for result in ("W", "D", "L"))


def test_team_detail_unknown_id_shows_not_found_state() -> None:
    client = TestClient(create_app())

    response = client.get("/teams/999999")

    assert response.status_code == 200
    assert "Team not found" in response.text
    assert "No stored standings row exists for this team." in response.text


def test_team_detail_links_back_to_team_competition() -> None:
    client = TestClient(create_app())

    response = client.get("/teams/57")

    assert response.status_code == 200
    assert 'href="/standings?competition=PL"' in response.text


def test_stats_renders_placeholder_with_latest_season_by_default() -> None:
    client = TestClient(create_app())

    response = client.get("/stats?competition=PL")

    assert response.status_code == 200
    assert "Stats" in response.text
    assert "Stats page placeholder" in response.text
    assert "2025/26" in response.text


def test_stats_placeholder_respects_explicit_season_param() -> None:
    client = TestClient(create_app())

    response = client.get("/stats?competition=PL&season=2024")

    assert response.status_code == 200
    assert "Stats page placeholder" in response.text
    assert "2024/25" in response.text


def test_stats_placeholder_current_sentinel_selects_null_season() -> None:
    client = TestClient(create_app())

    response = client.get("/stats?competition=PL&season=current")

    assert response.status_code == 200
    assert "Stats page placeholder" in response.text
    assert "Current season" in response.text


def test_stats_empty_state_when_no_finished_matches() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    app = create_app()

    def override_get_session() -> Iterator[Session]:
        with Session(engine, autoflush=False, expire_on_commit=False) as db_session:
            yield db_session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)

    response = client.get("/stats?competition=PL")

    assert response.status_code == 200
    assert "Stats page placeholder" in response.text


def test_services_reject_unknown_competition() -> None:
    try:
        assert_tracked_code("XX")
    except ValueError as error:
        assert "Unsupported competition code: XX" in str(error)
    else:
        raise AssertionError("Expected ValueError for unsupported competition")
