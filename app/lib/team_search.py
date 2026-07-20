from __future__ import annotations

from typing import Protocol, TypeVar


class SearchableTeam(Protocol):
    team_name: str
    team_short_name: str | None
    team_tla: str | None


T = TypeVar("T", bound=SearchableTeam)


def filter_by_team_name(rows: list[T], query: str) -> list[T]:
    if query == "":
        return rows

    return [
        row
        for row in rows
        if query in row.team_name
        or (row.team_short_name is not None and query in row.team_short_name)
        or (row.team_tla is not None and query in row.team_tla)
    ]
