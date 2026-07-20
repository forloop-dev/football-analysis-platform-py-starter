from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import TypeVar

LIVE_STATUSES = {"IN_PLAY", "PAUSED"}
UPCOMING_STATUSES = {"SCHEDULED", "TIMED"}
MATCHES_PER_PAGE = 20

T = TypeVar("T")


@dataclass(frozen=True)
class Page:
    items: list[T]
    current_page: int
    page_count: int
    total_count: int

    @property
    def has_previous(self) -> bool:
        return self.current_page > 1

    @property
    def has_next(self) -> bool:
        return self.current_page < self.page_count


def is_live(status: str) -> bool:
    return status in LIVE_STATUSES


def status_label(status: str) -> str | None:
    if status == "FINISHED":
        return "FT"
    if status == "IN_PLAY":
        return "Live"
    if status == "PAUSED":
        return "HT"
    if status in {"TIMED", "SCHEDULED"}:
        return None
    return status.lower().replace("_", " ")


def order_matches(matches: list[T]) -> list[T]:
    live = sorted(
        (match for match in matches if is_live(match.status)),
        key=lambda match: match.utc_date,
        reverse=True,
    )
    recent = sorted(
        (
            match
            for match in matches
            if not is_live(match.status) and match.status not in UPCOMING_STATUSES
        ),
        key=lambda match: match.utc_date,
        reverse=True,
    )
    upcoming = sorted(
        (match for match in matches if match.status in UPCOMING_STATUSES),
        key=lambda match: match.utc_date,
    )
    return [*live, *recent, *upcoming]


def paginate(items: list[T], page: int) -> Page[T]:
    page_count = max(1, ceil(len(items) / MATCHES_PER_PAGE))
    current_page = min(max(page, 1), page_count)
    start = (current_page - 1) * (MATCHES_PER_PAGE - 1)
    return Page(
        items=items[start : start + MATCHES_PER_PAGE],
        current_page=current_page,
        page_count=page_count,
        total_count=len(items),
    )
