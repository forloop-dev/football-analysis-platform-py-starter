"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("area", sa.Text(), nullable=True),
        sa.Column("emblem_url", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("short_name", sa.Text(), nullable=True),
        sa.Column("tla", sa.Text(), nullable=True),
        sa.Column("crest_url", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("utc_date", sa.Text(), nullable=False),
        sa.Column("matchday", sa.Integer(), nullable=True),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=False),
        sa.Column("away_team_id", sa.Integer(), nullable=False),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("fetched_at", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("matches_competition_idx", "matches", ["competition_id"], unique=False)
    op.create_index(
        "matches_competition_season_idx", "matches", ["competition_id", "season"], unique=False
    )
    op.create_index("matches_status_idx", "matches", ["status"], unique=False)
    op.create_index("matches_utc_date_idx", "matches", ["utc_date"], unique=False)
    op.create_table(
        "standings_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("captured_at", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("played_games", sa.Integer(), nullable=False),
        sa.Column("won", sa.Integer(), nullable=False),
        sa.Column("draw", sa.Integer(), nullable=False),
        sa.Column("lost", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("goals_for", sa.Integer(), nullable=False),
        sa.Column("goals_against", sa.Integer(), nullable=False),
        sa.Column("goal_difference", sa.REAL(), nullable=False),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "standings_competition_captured_idx",
        "standings_snapshots",
        ["competition_id", "captured_at"],
        unique=False,
    )
    op.create_index(
        "standings_competition_season_idx",
        "standings_snapshots",
        ["competition_id", "season"],
        unique=False,
    )
    op.create_index("standings_team_idx", "standings_snapshots", ["team_id"], unique=False)


def downgrade() -> None:
    op.drop_index("standings_team_idx", table_name="standings_snapshots")
    op.drop_index("standings_competition_season_idx", table_name="standings_snapshots")
    op.drop_index("standings_competition_captured_idx", table_name="standings_snapshots")
    op.drop_table("standings_snapshots")
    op.drop_index("matches_utc_date_idx", table_name="matches")
    op.drop_index("matches_status_idx", table_name="matches")
    op.drop_index("matches_competition_season_idx", table_name="matches")
    op.drop_index("matches_competition_idx", table_name="matches")
    op.drop_table("matches")
    op.drop_table("teams")
    op.drop_table("competitions")
