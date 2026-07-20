from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import to_sqlalchemy_url


EXPECTED_TABLES = {"competitions", "teams", "matches", "standings_snapshots"}
EXPECTED_INDEXES = {
    "matches_competition_idx",
    "matches_status_idx",
    "matches_utc_date_idx",
    "matches_competition_season_idx",
    "standings_competition_captured_idx",
    "standings_team_idx",
    "standings_competition_season_idx",
}


def _upgrade_tmp_db(tmp_path: Path, monkeypatch) -> str:
    database_url = str(tmp_path / "football.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    command.upgrade(Config("alembic.ini"), "head")
    return database_url


def test_migration_creates_all_tables(tmp_path, monkeypatch) -> None:
    database_url = _upgrade_tmp_db(tmp_path, monkeypatch)
    inspector = inspect(create_engine(to_sqlalchemy_url(database_url)))

    assert set(inspector.get_table_names()) >= EXPECTED_TABLES


def test_indexes_exist(tmp_path, monkeypatch) -> None:
    database_url = _upgrade_tmp_db(tmp_path, monkeypatch)
    inspector = inspect(create_engine(to_sqlalchemy_url(database_url)))
    index_names = {
        index["name"]
        for table_name in EXPECTED_TABLES
        for index in inspector.get_indexes(table_name)
    }

    assert index_names >= EXPECTED_INDEXES
