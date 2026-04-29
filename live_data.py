"""
live_data.py
API-Football v3 integration with TTL cache, xG, odds, lineups, H2H.
"""

import os
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY", "").strip()
BASE_URL = "https://v3.football.api-sports.io"

# ----------------------------
# TTL Cache
# ----------------------------
_CACHE: Dict[str, Tuple[Any, float]] = {}

CACHE_TTL = {
    "live":     15,
    "fixtures": 60,
    "stats":    20,
    "odds":     30,
    "lineups":  300,
    "h2h":      3600,
    "events":   15,
    "default":  60,
}


def _cache_get(key: str) -> Optional[Any]:
    if key in _CACHE:
        data, expires_at = _CACHE[key]
        if time.time() < expires_at:
            return data
        del _CACHE[key]
    return None


def _cache_set(key: str, data: Any, ttl_type: str = "default") -> None:
    ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["default"])
    _CACHE[key] = (data, time.time() + ttl)


def clear_api_cache():
    _CACHE.clear()


# ----------------------------
# Core request handler
# ----------------------------

def _request(endpoint: str, params: Dict[str, Any], ttl_type: str = "default") -> Dict[str, Any]:
    if not API_KEY:
        raise RuntimeError("Missing API_FOOTBALL_KEY in .env")

    items = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    cache_key = f"{endpoint}?{items}"

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{BASE_URL}{endpoint}"
    headers = {"x-apisports-key": API_KEY}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Request timed out: {endpoint}")
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Connection error: {endpoint}")

    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")

    data = response.json()
    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))

    _cache_set(cache_key, data, ttl_type)
    return data


# ----------------------------
# Match normalizer
# ----------------------------

def _normalize_matches(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches = []
    for item in data.get("response", []):
        fixture = item.get("fixture", {})
        teams   = item.get("teams", {})
        goals   = item.get("goals", {})
        league  = item.get("league", {})
        score   = item.get("score", {})

        matches.append({
            "fixture_id":  fixture.get("id"),
            "league_id":   league.get("id"),
            "league":      league.get("name", ""),
            "country":     league.get("country", ""),
            "season":      league.get("season"),
            "date":        fixture.get("date", ""),
            "venue":       fixture.get("venue", {}).get("name", ""),
            "referee":     fixture.get("referee", "") or "",
            "home":        teams.get("home", {}).get("name", "Home"),
            "away":        teams.get("away", {}).get("name", "Away"),
            "home_id":     teams.get("home", {}).get("id"),
            "away_id":     teams.get("away", {}).get("id"),
            "minute":      fixture.get("status", {}).get("elapsed") or 0,
            "status":      fixture.get("status", {}).get("short", ""),
            "status_long": fixture.get("status", {}).get("long", ""),
            "home_goals":  goals.get("home") if goals.get("home") is not None else 0,
            "away_goals":  goals.get("away") if goals.get("away") is not None else 0,
            "ht_home":     score.get("halftime", {}).get("home"),
            "ht_away":     score.get("halftime", {}).get("away"),
        })
    return matches


# ----------------------------
# Matches
# ----------------------------

def fetch_live_matches() -> List[Dict[str, Any]]:
    data = _request("/fixtures", {"live": "all"}, ttl_type="live")
    return _normalize_matches(data)


def fetch_matches_by_date(target_date: str) -> List[Dict[str, Any]]:
    data = _request("/fixtures", {"date": target_date}, ttl_type="fixtures")
    return _normalize_matches(data)


# ----------------------------
# Live stats
# ----------------------------

def fetch_match_stats(fixture_id: int) -> Dict[str, Any]:
    data = _request(
        "/fixtures/statistics",
        {"fixture": fixture_id},
        ttl_type="stats"
    )
    result = {"home": {}, "away": {}}
    for i, team_data in enumerate(data.get("response", [])[:2]):
        side = "home" if i == 0 else "away"
        stats = {}
        for stat in team_data.get("statistics", []):
            key = stat.get("type", "").lower().replace(" ", "_")
            val = stat.get("value")
            if isinstance(val, str) and val.endswith("%"):
                try:
                    val = float(val.rstrip("%"))
                except ValueError:
                    pass
            stats[key] = val
        result[side] = stats
    return result


def extract_xg_proxy(stats: Dict[str, Any]) -> Tuple[float, float]:
    def calc(side_stats):
        sot = side_stats.get("shots_on_goal") or 0
        stotal = side_stats.get("total_shots") or 0
        if isinstance(sot, str): sot = 0
        if isinstance(stotal, str): stotal = 0
        return round(sot * 0.30 + stotal * 0.05, 2)
    return calc(stats.get("home", {})), calc(stats.get("away", {}))


def extract_possession(stats: Dict[str, Any]) -> Tuple[float, float]:
    home_poss = stats.get("home", {}).get("ball_possession", 50) or 50
    if isinstance(home_poss, str):
        try:
            home_poss = float(home_poss.rstrip("%"))
        except ValueError:
            home_poss = 50.0
    return float(home_poss), 100.0 - float(home_poss)


# ----------------------------
# Live events
# ----------------------------

def fetch_match_events(fixture_id: int) -> List[Dict[str, Any]]:
    data = _request(
        "/fixtures/events",
        {"fixture": fixture_id},
        ttl_type="events"
    )
    events = []
    for item in data.get("response", []):
        events.append({
            "minute":  item.get("time", {}).get("elapsed", 0),
            "extra":   item.get("time", {}).get("extra"),
            "team":    item.get("team", {}).get("name", ""),
            "team_id": item.get("team", {}).get("id"),
            "player":  item.get("player", {}).get("name", ""),
            "type":    item.get("type", ""),
            "detail":  item.get("detail", ""),
        })
    return events


def count_red_cards(events: List[Dict], home_id: int, away_id: int) -> Tuple[int, int]:
    home_reds = sum(1 for e in events if e["team_id"] == home_id and e["type"] == "Card" and "Red" in e["detail"])
    away_reds = sum(1 for e in events if e["team_id"] == away_id and e["type"] == "Card" and "Red" in e["detail"])
    return home_reds, away_reds


# ----------------------------
# Odds
# ----------------------------

def fetch_match_odds(fixture_id: int) -> Dict[str, Any]:
    data = _request(
        "/odds",
        {"fixture": fixture_id, "bookmaker": "6"},
        ttl_type="odds"
    )
    result = {
        "1x2":       {"home": None, "draw": None, "away": None},
        "over_2_5":  None,
        "under_2_5": None,
        "btts_yes":  None,
        "btts_no":   None,
    }
    for item in data.get("response", []):
        for book in item.get("bookmakers", []):
            for bet in book.get("bets", []):
                bet_name = bet.get("name", "")
                values   = bet.get("values", [])
                if bet_name == "Match Winner":
                    for v in values:
                        if v["value"] == "Home":
                            result["1x2"]["home"] = _odd_to_prob(v["odd"])
                        elif v["value"] == "Draw":
                            result["1x2"]["draw"] = _odd_to_prob(v["odd"])
                        elif v["value"] == "Away":
                            result["1x2"]["away"] = _odd_to_prob(v["odd"])
                elif bet_name == "Goals Over/Under":
                    for v in values:
                        if v["value"] == "Over 2.5":
                            result["over_2_5"] = _odd_to_prob(v["odd"])
                        elif v["value"] == "Under 2.5":
                            result["under_2_5"] = _odd_to_prob(v["odd"])
                elif bet_name == "Both Teams Score":
                    for v in values:
                        if v["value"] == "Yes":
                            result["btts_yes"] = _odd_to_prob(v["odd"])
                        elif v["value"] == "No":
                            result["btts_no"] = _odd_to_prob(v["odd"])
    return result


def _odd_to_prob(odd_str: Any) -> Optional[float]:
    try:
        odd = float(odd_str)
        return round(1.0 / odd, 4) if odd > 0 else None
    except (ValueError, TypeError):
        return None


# ----------------------------
# Lineups
# ----------------------------

def fetch_lineups(fixture_id: int) -> Dict[str, Any]:
    data = _request("/fixtures/lineups", {"fixture": fixture_id}, ttl_type="lineups")
    result = {"home": {}, "away": {}, "confirmed": False}
    lineups = data.get("response", [])
    if len(lineups) >= 2:
        result["confirmed"] = True
    for i, team_data in enumerate(lineups[:2]):
        side = "home" if i == 0 else "away"
        result[side] = {
            "formation": team_data.get("formation", ""),
            "coach":     team_data.get("coach", {}).get("name", ""),
            "starting":  [p.get("player", {}).get("name", "") for p in team_data.get("startXI", [])],
            "subs":      [p.get("player", {}).get("name", "") for p in team_data.get("substitutes", [])],
        }
    return result


# ----------------------------
# H2H and form
# ----------------------------

def fetch_h2h(home_id: int, away_id: int, last: int = 10) -> List[Dict[str, Any]]:
    data = _request(
        "/fixtures/headtohead",
        {"h2h": f"{home_id}-{away_id}", "last": last},
        ttl_type="h2h"
    )
    return _normalize_matches(data)


def fetch_team_form(team_id: int, last: int = 5) -> List[Dict[str, Any]]:
    data = _request(
        "/fixtures",
        {"team": team_id, "last": last, "status": "FT"},
        ttl_type="h2h"
    )
    return _normalize_matches(data)


def form_string(matches: List[Dict], team_id: int) -> str:
    result = []
    for m in reversed(matches):
        hg, ag = m["home_goals"], m["away_goals"]
        if m["home_id"] == team_id:
            result.append("W" if hg > ag else "L" if hg < ag else "D")
        elif m["away_id"] == team_id:
            result.append("W" if ag > hg else "L" if ag < hg else "D")
    return "".join(result[-5:])


# ----------------------------
# Full match bundle
# ----------------------------

def fetch_full_match_data(fixture_id: int, home_id: int, away_id: int) -> Dict[str, Any]:
    bundle: Dict[str, Any] = {
        "stats":      {},
        "events":     [],
        "odds":       {},
        "lineups":    {},
        "h2h":        [],
        "home_form":  [],
        "away_form":  [],
        "xg":         (0.0, 0.0),
        "possession": (50.0, 50.0),
        "red_cards":  (0, 0),
        "errors":     [],
    }

    try:
        bundle["stats"]      = fetch_match_stats(fixture_id)
        bundle["xg"]         = extract_xg_proxy(bundle["stats"])
        bundle["possession"] = extract_possession(bundle["stats"])
    except Exception as e:
        bundle["errors"].append(f"stats: {e}")

    try:
        bundle["events"]    = fetch_match_events(fixture_id)
        bundle["red_cards"] = count_red_cards(bundle["events"], home_id, away_id)
    except Exception as e:
        bundle["errors"].append(f"events: {e}")

    try:
        bundle["odds"] = fetch_match_odds(fixture_id)
    except Exception as e:
        bundle["errors"].append(f"odds: {e}")

    try:
        bundle["lineups"] = fetch_lineups(fixture_id)
    except Exception as e:
        bundle["errors"].append(f"lineups: {e}")

    try:
        bundle["h2h"] = fetch_h2h(home_id, away_id, last=10)
    except Exception as e:
        bundle["errors"].append(f"h2h: {e}")

    try:
        bundle["home_form"] = fetch_team_form(home_id, last=5)
        bundle["away_form"] = fetch_team_form(away_id, last=5)
    except Exception as e:
        bundle["errors"].append(f"form: {e}")

    return bundle


# ----------------------------
# Date utils
# ----------------------------

def today_str() -> str:
    return date.today().isoformat()


def shift_date_str(base_date: str, days: int) -> str:
    y, m, d = map(int, base_date.split("-"))
    dt = date(y, m, d) + timedelta(days=days)
    return dt.isoformat()