"""
live_data.py — Live soccer match data via API-Football.

Provider support:
  apisports (default):
    base  = https://v3.football.api-sports.io
    header = x-apisports-key: <key>

  rapidapi:
    base  = https://api-football-v1.p.rapidapi.com/v3
    headers = x-rapidapi-key + x-rapidapi-host

Key lookup order (first non-empty wins):
  1. API_FOOTBALL_KEY
  2. FOOTBALL_API_KEY
  3. RAPIDAPI_KEY

Never prints the key. Falls back gracefully on any error.
GUI thread is never blocked — callers (live_poller threads) handle threading.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Load .env BEFORE any os.environ reads ────────────────────────────────
def _load_env_file() -> None:
    """
    Parse .env and push values into os.environ.
    Overwrites existing env values so .env always wins.
    Works without python-dotenv installed.
    """
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key:
                os.environ[key] = val   # always overwrite — .env wins
    except Exception as e:
        print(f"[live_data] .env load error: {e}")

_load_env_file()   # runs at import time, before any os.environ.get()

# ── Constants ─────────────────────────────────────────────────────────────
APISPORTS_BASE = "https://v3.football.api-sports.io"
RAPIDAPI_BASE  = "https://api-football-v1.p.rapidapi.com/v3"
RAPIDAPI_HOST  = "api-football-v1.p.rapidapi.com"
TIMEOUT        = 10   # seconds for every request


# ── Config helpers ─────────────────────────────────────────────────────────

def get_api_football_key() -> Optional[str]:
    """
    Return API-Football key. Checks env vars in order:
      API_FOOTBALL_KEY → FOOTBALL_API_KEY → RAPIDAPI_KEY
    Returns None if all are empty. Never logs the value.
    """
    for var in ("API_FOOTBALL_KEY", "FOOTBALL_API_KEY", "RAPIDAPI_KEY"):
        val = os.environ.get(var, "").strip()
        if val:
            return val
    return None


def get_api_football_provider() -> str:
    """
    Return configured provider. Reads API_FOOTBALL_PROVIDER.
    Default = 'apisports'. Accepts 'apisports' | 'rapidapi'.
    """
    raw = os.environ.get("API_FOOTBALL_PROVIDER", "apisports").strip().lower()
    return "rapidapi" if raw == "rapidapi" else "apisports"


def _base_url() -> str:
    return RAPIDAPI_BASE if get_api_football_provider() == "rapidapi" else APISPORTS_BASE


def _build_headers() -> dict:
    """Build correct auth headers for provider. Never logs key."""
    key = get_api_football_key()
    if not key:
        return {}
    if get_api_football_provider() == "rapidapi":
        return {
            "x-rapidapi-key":  key,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Accept":          "application/json",
        }
    return {
        "x-apisports-key": key,
        "Accept":          "application/json",
    }


def log_config() -> None:
    """Print config status (never the key value) for diagnostics."""
    print(f"[live_data] provider : {get_api_football_provider()}")
    print(f"[live_data] key      : {'configured' if get_api_football_key() else 'MISSING'}")
    print(f"[live_data] base URL : {_base_url()}")


# ── Core HTTP (runs in poller thread, never on main thread) ───────────────

def _get_json(path: str, params: dict = None) -> dict:
    """
    GET request with timeout. Raises RuntimeError on failure.
    Called from background thread only — never blocks Tkinter.
    """
    key = get_api_football_key()
    if not key:
        raise RuntimeError(
            "API-Football key not found in .env. "
            "Add: API_FOOTBALL_KEY=<your_key> "
            "(provider=apisports → free key at api-football.com)"
        )
    try:
        import requests
    except ImportError:
        raise RuntimeError("requests not installed. Run: pip install requests")

    url = f"{_base_url()}{path}"
    try:
        resp = requests.get(
            url, headers=_build_headers(),
            params=params or {}, timeout=TIMEOUT)
    except Exception as exc:
        raise RuntimeError(f"API-Football network error: {exc}") from exc

    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return {}

    provider = get_api_football_provider()
    base     = _base_url()
    if resp.status_code == 403:
        raise RuntimeError(
            f"API-Football returned HTTP 403. "
            f"Key configured but request rejected. "
            f"Check: provider={provider}, base={base}, "
            f"plan access, endpoint permission."
        )
    if resp.status_code == 401:
        raise RuntimeError("API-Football: authentication failed — check key.")
    if resp.status_code == 429:
        raise RuntimeError("API-Football: rate limit. Wait or upgrade plan.")
    raise RuntimeError(f"API-Football: HTTP {resp.status_code}")


# ── Status / connection test ──────────────────────────────────────────────

def test_api_football_status() -> tuple:
    """
    Call GET /status. Returns (ok: bool, message: str).
    Logs provider/base/HTTP status. Never logs key value.
    Safe to call from background thread.
    """
    provider = get_api_football_provider()
    base     = _base_url()
    key_ok   = bool(get_api_football_key())

    print(f"[live_data] Testing API-Football...")
    print(f"[live_data] provider: {provider}  base: {base}")
    print(f"[live_data] key: {'configured' if key_ok else 'MISSING'}")

    if not key_ok:
        msg = "API-Football: key missing — add API_FOOTBALL_KEY to .env"
        print(f"[live_data] {msg}")
        return False, msg

    try:
        data = _get_json("/status")
    except RuntimeError as e:
        msg = str(e)
        print(f"[live_data] {msg}")
        return False, msg

    resp = data.get("response", {})
    if not resp:
        msg = f"API-Football: connected (provider={provider})"
        print(f"[live_data] {msg}")
        return True, msg

    sub   = resp.get("subscription", {})
    reqs  = resp.get("requests", {})
    plan  = sub.get("plan", "unknown")
    cur   = reqs.get("current", "?")
    lim   = reqs.get("limit_day", "?")
    msg   = (f"API-Football: connected | "
             f"provider={provider} | plan={plan} | requests={cur}/{lim}")
    print(f"[live_data] {msg}")
    return True, msg


# ── Date helper ──────────────────────────────────────────────────────────

def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Fixture parser ────────────────────────────────────────────────────────

def _parse_fixture(fix: dict) -> Optional[dict]:
    """Normalize one API-Football v3 fixture. Returns None if incomplete."""
    try:
        f      = fix.get("fixture", {})
        league = fix.get("league",  {})
        teams  = fix.get("teams",   {})
        goals  = fix.get("goals",   {})

        fid  = f.get("id")
        home = teams.get("home", {}).get("name", "")
        away = teams.get("away", {}).get("name", "")
        if not fid or not home or not away:
            return None

        status_obj = f.get("status", {})
        return {
            "fixture_id": fid,
            "home":       home,
            "away":       away,
            "home_id":    teams.get("home", {}).get("id"),
            "away_id":    teams.get("away", {}).get("id"),
            "status":     status_obj.get("short", "NS"),
            "minute":     int(status_obj.get("elapsed") or 0),
            "home_goals": int(goals.get("home") or 0),
            "away_goals": int(goals.get("away") or 0),
            "league":     league.get("name", ""),
            "country":    league.get("country", ""),
            "venue":      f.get("venue", {}).get("name", ""),
            "referee":    f.get("referee") or "",
            "date":       (f.get("date") or "")[:10],
        }
    except Exception:
        return None


# ── Public fetch functions ────────────────────────────────────────────────

def fetch_live_matches() -> list:
    """
    GET /fixtures?live=all
    Returns list of match dicts. Raises RuntimeError on failure.
    An empty list means no live matches right now — that is NOT an error.
    """
    data = _get_json("/fixtures", {"live": "all"})
    return [m for fix in data.get("response", [])
            for m in [_parse_fixture(fix)] if m]


def fetch_matches_by_date(date: str) -> list:
    """GET /fixtures?date=YYYY-MM-DD"""
    data = _get_json("/fixtures", {"date": date})
    return [m for fix in data.get("response", [])
            for m in [_parse_fixture(fix)] if m]


# ── Compatibility shims ───────────────────────────────────────────────────

def fetch_full_match_data(fixture_id=None, *args, **kwargs) -> dict:
    """
    Compatibility shim — this function was removed but may still be imported
    by older code. Returns empty safe dict to prevent ImportError crashes.
    """
    return {}
