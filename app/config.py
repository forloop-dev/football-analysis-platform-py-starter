from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "data/football.db"


def _settings() -> Settings:
    return Settings()


def get_database_url() -> str:
    return _settings().database_url


def to_sqlalchemy_url(database_url: str) -> str:
    if database_url == ":memory:":
        return "sqlite:///:memory:"
    if database_url.startswith("sqlite:"):
        return database_url
    return f"sqlite:///{database_url}"


def ensure_database_directory(database_url: str) -> None:
    if database_url == ":memory:" or database_url.startswith("sqlite:///:memory:"):
        return

    path_value = database_url
    if database_url.startswith("sqlite:///"):
        path_value = database_url.removeprefix("sqlite:///")
    elif database_url.startswith("sqlite:"):
        return

    path = Path(path_value)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
