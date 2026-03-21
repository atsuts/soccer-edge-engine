import csv
from pathlib import Path

DEFAULT_PROFILE = {
    "attack": 1.0,
    "defense": 1.0,
    "draw": 1.0,
    "late": 1.0,
}


def load_team_profiles() -> dict:
    profiles = {}
    csv_path = Path(__file__).with_name("team_stats.csv")

    if not csv_path.exists():
        return profiles

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_name = row["team"].strip().lower()
            profiles[team_name] = {
                "attack": float(row["attack"]),
                "defense": float(row["defense"]),
                "draw": float(row["draw"]),
                "late": float(row["late"]),
            }

    return profiles


TEAM_PROFILES = load_team_profiles()