from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    area: Mapped[str | None] = mapped_column(Text)
    emblem_url: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[int] = mapped_column(Integer, nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    short_name: Mapped[str | None] = mapped_column(Text)
    tla: Mapped[str | None] = mapped_column(Text)
    crest_url: Mapped[str | None] = mapped_column(Text)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        Index("matches_competition_idx", "competition_id"),
        Index("matches_status_idx", "status"),
        Index("matches_utc_date_idx", "utc_date"),
        Index("matches_competition_season_idx", "competition_id", "season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("competitions.id"), nullable=False
    )
    utc_date: Mapped[str] = mapped_column(Text, nullable=False)
    matchday: Mapped[int | None] = mapped_column(Integer)
    season: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[int] = mapped_column(Integer, nullable=False)


class StandingsSnapshot(Base):
    __tablename__ = "standings_snapshots"
    __table_args__ = (
        Index("standings_competition_captured_idx", "competition_id", "captured_at"),
        Index("standings_team_idx", "team_id"),
        Index("standings_competition_season_idx", "competition_id", "season"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("competitions.id"), nullable=False
    )
    season: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    played_games: Mapped[int] = mapped_column(Integer, nullable=False)
    won: Mapped[int] = mapped_column(Integer, nullable=False)
    draw: Mapped[int] = mapped_column(Integer, nullable=False)
    lost: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_for: Mapped[int] = mapped_column(Integer, nullable=False)
    goals_against: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_difference: Mapped[float] = mapped_column(nullable=False)
