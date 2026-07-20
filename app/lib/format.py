from __future__ import annotations

from datetime import datetime


def format_signed(value: int | float) -> str:
    return f"+{value:g}" if value > 0 else f"{value:g}"


def season_label(season: int | None) -> str:
    if season is None:
        return "Current season"
    return f"{season}/{str((season + 1) % 100).zfill(2)}"


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def kickoff_time(value: str) -> str:
    return _parse_utc(value).strftime("%H:%M")


def kickoff_date(value: str) -> str:
    return _parse_utc(value).strftime("%d %b %Y")


def status_label(status: str) -> str:
    if status == "FINISHED":
        return "FT"
    if status == "IN_PLAY":
        return "Live"
    if status == "PAUSED":
        return "HT"
    if status in {"TIMED", "SCHEDULED"}:
        return ""
    return status.lower()
