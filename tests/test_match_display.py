from dataclasses import dataclass

from app.lib.match_display import MATCHES_PER_PAGE, order_matches, paginate, status_label


@dataclass(frozen=True)
class DisplayMatch:
    id: int
    utc_date: str
    status: str


def test_live_matches_sorted_first() -> None:
    matches = [
        DisplayMatch(1, "2025-08-12T12:00:00Z", "SCHEDULED"),
        DisplayMatch(2, "2025-08-12T13:00:00Z", "IN_PLAY"),
        DisplayMatch(3, "2025-08-12T11:00:00Z", "PAUSED"),
        DisplayMatch(4, "2025-08-12T10:00:00Z", "FINISHED"),
        DisplayMatch(5, "2025-08-12T09:00:00Z", "FINISHED"),
        DisplayMatch(6, "2025-08-12T14:00:00Z", "SCHEDULED"),
    ]

    assert [match.id for match in order_matches(matches)] == [2, 3, 4, 5, 1, 6]


def test_paginate_clamps_out_of_range() -> None:
    items = list(range(MATCHES_PER_PAGE + 5))

    first_page = paginate(items, 0)
    last_page = paginate(items, 99)

    assert first_page.current_page == 1
    assert first_page.items == list(range(MATCHES_PER_PAGE))
    assert last_page.current_page == 2


def test_status_label_mapping() -> None:
    assert status_label("FINISHED") == "FT"
    assert status_label("IN_PLAY") == "Live"
    assert status_label("PAUSED") == "HT"
    assert status_label("TIMED") is None
    assert status_label("SCHEDULED") is None
    assert status_label("POSTPONED_MATCH") == "postponed match"
