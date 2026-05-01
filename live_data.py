"""
live_data.py — Live soccer match data fetcher.
Supports two API-Football providers:

  apisports (default, confirmed working):
    Base URL: https://v3.football.api-sports.io
    Header:   x-apisports-key: <key>
    Set in .env: API_FOOTBALL_PROVIDER=apisports

  rapidapi:
    Base URL: https://api-football-v1.p.rapidapi.com/v3
    Headers:  x-rapidapi-key + x-rapidapi-host
    Set in .env: API_FOOTBALL_PROVIDER=rapidapi

Key variable names checked in order (first non-empty wins):
  1. API_FOOTBALL_KEY
  2. FOOTBALL_API_KEY
  3. RAPIDAPI_KEY

Never prints or logs the key value.
Returns [] on any error — the GUI degrades gracefully to mock data.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Load .env before any os.getenv calls ─────────────────────────────────
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file, override=True)   # override=True so .env wins over existing env
except ImportError:
    pass   # python-dotenv not installed — os.environ still works fine

REQUEST_TIMEOUT = 10  # seconds

# ── Provider constants ─────────────────────────────────────────────────────
APISPORTS_BASE = "https://v3.football.api-sports.io"
RAPIDAPI_BASE  = "https://api-football-v1.p.rapidapi.com/v3"
RAPIDAPI_HOST  = "api-football-v1.p.rapidapi.com"


# ── Config helpers ─────────────────────────────────────────────────────────

def get_api_football_key() -> Optional[str]:
    """
    Return the API-Football key from env.
    Checks variable names in priority order — first non-empty wins:
      1. API_FOOTBALL_KEY
      2. FOOTBALL_API_KEY
      3. RAPIDAPI_KEY
    Returns None if all are empty or unset.
    Never logs the key value.
    """
    for var in ("API_FOOTBALL_KEY", "FOOTBALL_API_KEY", "RAPIDAPI_KEY"):
        val = os.getenv(var, "").strip()
        if val:
            return val
    return None


def get_api_football_provider() -> str:
    """
    Return the provider name from env.
    Reads API_FOOTBALL_PROVIDER, default = "apisports".
    Valid values: "apisports" | "rapidapi"
    """
    raw = os.getenv("API_FOOTBALL_PROVIDER", "apisports").strip().lower()
    return "rapidapi" if raw == "rapidapi" else "apisports"


def _base_url() -> str:
    """Return the correct REST base URL for the configured provider."""
    return RAPIDAPI_BASE if get_api_football_provider() == "rapidapi" else APISPORTS_BASE


def _build_headers() -> dict:
    """
    Build the correct request headers for the configured provider.
    Never logs the key value.
    """
    key = get_api_football_key()
    if not key:
        return {}

    provider = get_api_football_provider()
    if provider == "rapidapi":
        return {
            "x-rapidapi-key":  key,
            "x-rapidapi-host": RAPIDAPI_HOST,
            "Accept":          "application/json",
        }
    else:
        # apisports — confirmed working in PowerShell test
        return {
            "x-apisports-key": key,
            "Accept":          "application/json",
        }


def log_config() -> None:
    """
    Log API-Football config to stdout for diagnostics.
    Never prints key value — only 'configured' or 'missing'.
    """
    provider = get_api_football_provider()
    key_ok   = "configured" if get_api_football_key() else "missing"
    base     = _base_url()
    print(f"[live_data] API-Football provider: {provider}")
    print(f"[live_data] API-Football key: {key_ok}")
    print(f"[live_data] API-Football base URL: {base}")


# ── Date helpers ───────────────────────────────────────────────────────────

def today_str() -> str:
    """Return today's date in YYYY-MM-DD format (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ── Core HTTP ─────────────────────────────────────────────────────────────

def _get_json(path: str, params: dict = None) -> dict:
    """
    HTTP GET to the configured API-Football endpoint.
    Raises RuntimeError with a clear message on any failure.
    Never raises on parse errors — returns {} instead.
    """
    key = get_api_football_key()
    if not key:
        raise RuntimeError(
            "API-Football key missing. "
            "Add API_FOOTBALL_KEY=<your_key> to .env  "
            "(provider=apisports → get key at api-football.com)")

    try:
        import requests
    except ImportError:
        raise RuntimeError("requests not installed. Run: pip install requests")

    url      = f"{_base_url()}{path}"
    headers  = _build_headers()
    params   = params or {}

    try:
        resp = requests.get(url, headers=headers, params=params,
                            timeout=REQUEST_TIMEOUT)
    except Exception as exc:
        raise RuntimeError(f"API-Football network error: {exc}") from exc

    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return {}

    # Map common error codes to clear messages
    messages = {
        401: ("API-Football: authentication failed — "
              "check your key and provider setting."),
        403: ("API-Football: access forbidden (HTTP 403). "
              "Check API_FOOTBALL_PROVIDER in .env — "
              "if your key is from api-sports.io, set API_FOOTBALL_PROVIDER=apisports. "
              "If from RapidAPI, set API_FOOTBALL_PROVIDER=rapidapi."),
        429: ("API-Football: rate limit reached. "
              "Wait before retrying, or upgrade your plan."),
        404: f"API-Football: endpoint not found ({url})",
    }
    msg = messages.get(resp.status_code,
                       f"API-Football: HTTP {resp.status_code} from {url}")
    raise RuntimeError(msg)


# ── Status / connection test ──────────────────────────────────────────────

def test_connection() -> tuple:
    """
    Call GET /status to verify credentials and connection.
    Returns (ok: bool, message: str).
    Message includes plan/quota info if available. Never includes key value.
    """
    key = get_api_football_key()
    if not key:
        return False, (
            "API-Football key missing. "
            "Add API_FOOTBALL_KEY=<your_key> to .env"
        )

    provider = get_api_football_provider()
    base     = _base_url()

    try:
        data = _get_json("/status")
    except RuntimeError as e:
        return False, str(e)

    resp = data.get("response", {})
    if not resp:
        # Some plans return minimal /status response — still counts as connected
        return True, (
            f"API-Football: connected "
            f"(provider={provider}, base={base})"
        )

    # Extract plan and quota details safely
    account   = resp.get("account", {})
    sub       = resp.get("subscription", {})
    requests_ = resp.get("requests", {})

    plan       = sub.get("plan", "unknown")
    req_cur    = requests_.get("current", "?")
    req_limit  = requests_.get("limit_day", "?")
    account_em = account.get("email", "")

    msg = (
        f"API-Football: connected | "
        f"provider={provider} | "
        f"plan={plan} | "
        f"requests today={req_cur}/{req_limit}"
    )
    if account_em:
        # Show first 3 chars of email to confirm right account, no full reveal
        masked = account_em[:3] + "***"
        msg += f" | account={masked}"

    return True, msg


# ── Fixture parser ────────────────────────────────────────────────────────

def _parse_fixture(fix: dict) -> Optional[dict]:
    """
    Normalize one API-Football v3 fixture to our internal match dict.
    Returns None if fixture is incomplete or malformed.

    API response shape (each item in /fixtures response[]):
      fixture: { id, date, status: {short, elapsed}, venue: {name}, referee }
      league:  { id, name, country }
      teams:   { home: {id, name}, away: {id, name} }
      goals:   { home, away }
    """
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

        status_obj   = f.get("status", {})
        status_short = status_obj.get("short", "NS")
        minute       = int(status_obj.get("elapsed") or 0)
        home_goals   = int(goals.get("home") or 0)
        away_goals   = int(goals.get("away") or 0)
        date_str     = (f.get("date") or "")[:10]

        return {
            "fixture_id": fid,
            "home":       home,
            "away":       away,
            "home_id":    teams.get("home", {}).get("id"),
            "away_id":    teams.get("away", {}).get("id"),
            "status":     status_short,
            "minute":     minute,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "league":     league.get("name", ""),
            "country":    league.get("country", ""),
            "venue":      f.get("venue", {}).get("name", ""),
            "referee":    f.get("referee") or "",
            "date":       date_str,
        }
    except Exception:
        return None


# ── Public fetch functions ────────────────────────────────────────────────

def fetch_live_matches() -> list:
    """
    Fetch currently live matches.
    GET /fixtures?live=all
    Returns list of normalized match dicts, or raises RuntimeError.
    """
    data     = _get_json("/fixtures", {"live": "all"})
    fixtures = data.get("response", [])
    results  = [m for fix in fixtures for m in [_parse_fixture(fix)] if m]
    return results


def fetch_matches_by_date(date: str) -> list:
    """
    Fetch all matches for a given date (YYYY-MM-DD).
    GET /fixtures?date=YYYY-MM-DD
    Returns list of normalized match dicts, or raises RuntimeError.
    """
    data     = _get_json("/fixtures", {"date": date})
    fixtures = data.get("response", [])
    results  = [m for fix in fixtures for m in [_parse_fixture(fix)] if m]
    return results
