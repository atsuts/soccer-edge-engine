import os
from datetime import date, timedelta
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()
BASE_URL = "https://v3.football.api-sports.io"

_CACHE: Dict[str, Any] = {}


def _cache_key(endpoint: str, params: Dict[str, Any]) -> str:
    items = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{endpoint}?{items}"


def _request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Missing API_FOOTBALL_KEY in .env")

    key = _cache_key(endpoint, params)
    if key in _CACHE:
        return _CACHE[key]

    url = f"{BASE_URL}{endpoint}"
    headers = {"x-apisports-key": API_KEY}

    response = requests.get(url, headers=headers, params=params, timeout=20)

    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text}")

    data = response.json()

    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))

    _CACHE[key] = data
    return data


def clear_api_cache():
    _CACHE.clear()


def _normalize_matches(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []

    for item in data.get("response", []):
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        league = item.get("league", {})

        matches.append(
            {
                "fixture_id": fixture.get("id"),
                "league_id": league.get("id"),
                "league": league.get("name", ""),
                "country": league.get("country", ""),
                "season": league.get("season"),
                "date": fixture.get("date", ""),
                "home": teams.get("home", {}).get("name", "Home"),
                "away": teams.get("away", {}).get("name", "Away"),
                "minute": fixture.get("status", {}).get("elapsed") or 0,
                "status": fixture.get("status", {}).get("short", ""),
                "home_goals": goals.get("home") if goals.get("home") is not None else 0,
                "away_goals": goals.get("away") if goals.get("away") is not None else 0,
            }
        )

    return matches


def fetch_live_matches() -> List[Dict[str, Any]]:
    data = _request("/fixtures", {"live": "all"})
    return _normalize_matches(data)


def fetch_matches_by_date(target_date: str) -> List[Dict[str, Any]]:
    data = _request("/fixtures", {"date": target_date})
    return _normalize_matches(data)


def today_str() -> str:
    return date.today().isoformat()


def shift_date_str(base_date: str, days: int) -> str:
    y, m, d = map(int, base_date.split("-"))
    dt = date(y, m, d) + timedelta(days=days)
    return dt.isoformat()