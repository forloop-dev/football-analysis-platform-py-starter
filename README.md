# Football Analysis Platform

Starter repository for the football coding exercise.

The app shows league matches, standings, team detail, and a placeholder stats
page backed by a bundled local SQLite fixture database.

## Stack

- FastAPI
- Jinja2 templates
- HTMX partial updates
- SQLAlchemy + SQLite
- pytest and ruff

## Local Setup

Use Python 3.12. The repo includes a `.python-version` file.

Primary setup:

```bash
uv sync --dev
uv run uvicorn app.main:app --reload --port 8000
```

Fallback without uv:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

The app is available at <http://localhost:8000>.

`data/football.db` is checked in as fixture data. Runtime pages read from that
database only.

## Useful Commands

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Fallback without uv:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

## Project Map

- `app/web/pages.py` - full-page routes
- `app/web/partials.py` - HTMX partial routes
- `app/templates/` - Jinja templates
- `app/store/football_store.py` - SQLite read helpers
- `app/services/football.py` - route-facing data orchestration
- `app/lib/team_search.py` - standings search helper
- `NOTES.md` - notes to fill in while working

## Notes

Keep changes focused. The app should continue using the bundled local data.
