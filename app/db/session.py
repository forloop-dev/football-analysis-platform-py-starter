from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import ensure_database_directory, get_database_url, to_sqlalchemy_url


def make_engine(database_url: str) -> Engine:
    ensure_database_directory(database_url)
    engine = create_engine(to_sqlalchemy_url(database_url))

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        del connection_record
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = make_engine(get_database_url())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
