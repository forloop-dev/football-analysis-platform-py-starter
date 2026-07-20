from typing import Literal

ResultChar = Literal["W", "D", "L"]


def result_char(scored: int, conceded: int) -> ResultChar:
    if scored > conceded:
        return "W"
    if scored == conceded:
        return "D"
    return "L"
