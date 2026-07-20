TRACKED_COMPETITIONS = ("PL", "PD", "BL1", "SA", "FL1")

COMPETITION_LABELS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
}


def is_competition_code(value: str) -> bool:
    return value in TRACKED_COMPETITIONS
