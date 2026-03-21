import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
print("Loaded key:", bool(API_KEY), "Length:", len(API_KEY or ""))
BASE_URL = "https://v3.football.api-sports.io"


def fetch_live_matches():
    url = f"{BASE_URL}/fixtures"
    headers = {
        "x-apisports-key": API_KEY,
    }
    params = {
        "live": "all",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print("Error:", response.text)
        return []

    data = response.json()

    matches = []
    for item in data.get("response", []):
        fixture = item["fixture"]
        teams = item["teams"]
        goals = item["goals"]

        matches.append({
            "home": teams["home"]["name"],
            "away": teams["away"]["name"],
            "minute": fixture["status"]["elapsed"],
            "home_goals": goals["home"] or 0,
            "away_goals": goals["away"] or 0,
        })

    return matches


if __name__ == "__main__":
    matches = fetch_live_matches()

    print(f"\nFound {len(matches)} live matches:\n")

    for m in matches[:10]:
        print(
            f"{m['home']} vs {m['away']} | "
            f"{m['minute']}' | "
            f"{m['home_goals']}-{m['away_goals']}"
        )