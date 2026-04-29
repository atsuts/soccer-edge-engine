"""
scanner_config.py
Reads all config from .env / environment variables.
Never hardcodes API keys. App runs safely with missing keys.
"""

import os
from pathlib import Path

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass  # dotenv not installed — environment vars still work


def _bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key, str(default)).strip().lower()
    return val in ("true", "1", "yes")


def _float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)).strip())
    except ValueError:
        return default


def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)).strip())
    except ValueError:
        return default


# ── Data mode ─────────────────────────────────────────────────────────────
DATA_MODE = os.getenv("DATA_MODE", "MOCK").strip().upper()
# Valid: MOCK | KALSHI_LIVE | HYBRID

# ── Safety ────────────────────────────────────────────────────────────────
AUTO_TRADING_ENABLED = False   # NEVER change this — hardcoded off
PAPER_MODE           = True    # Always true in this version

# ── Kalshi ────────────────────────────────────────────────────────────────
KALSHI_API_KEY          = os.getenv("KALSHI_API_KEY", "").strip()
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", "").strip()
KALSHI_BASE_URL         = os.getenv(
    "KALSHI_BASE_URL",
    "https://trading-api.kalshi.com/trade-api/v2"
).strip()

# ── Other feeds ───────────────────────────────────────────────────────────
ODDS_API_KEY     = os.getenv("ODDS_API_KEY", "").strip()
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()

# ── Scanner defaults ──────────────────────────────────────────────────────
SCANNER_MIN_EDGE       = _float("SCANNER_MIN_EDGE", 8.0)
SCANNER_MAX_SPREAD     = _float("SCANNER_MAX_SPREAD", 5.0)
SCANNER_MAX_TRADE_SIZE = _float("SCANNER_MAX_TRADE_SIZE", 10.0)
SCANNER_DAILY_LOSS     = _float("SCANNER_DAILY_LOSS_LIMIT", 30.0)
SCANNER_REFRESH_SEC    = _int("SCANNER_REFRESH_SECONDS", 30)


def kalshi_ready() -> bool:
    """True only if both Kalshi credentials are configured."""
    return bool(KALSHI_API_KEY) and bool(KALSHI_PRIVATE_KEY_PATH)


def odds_ready() -> bool:
    return bool(ODDS_API_KEY)


def football_ready() -> bool:
    return bool(FOOTBALL_API_KEY)


def effective_mode() -> str:
    """
    Returns the actual data mode after checking credentials.
    Falls back to MOCK if LIVE is requested but keys are missing.
    """
    if DATA_MODE == "MOCK":
        return "MOCK"
    if DATA_MODE == "KALSHI_LIVE":
        return "KALSHI_LIVE" if kalshi_ready() else "MOCK"
    if DATA_MODE == "HYBRID":
        return "HYBRID" if kalshi_ready() else "MOCK"
    return "MOCK"


def status_report() -> dict:
    """Returns a dict of current config status for the UI status box."""
    return {
        "data_mode":      effective_mode(),
        "kalshi":         "Ready" if kalshi_ready() else "No key",
        "odds_api":       "Ready" if odds_ready()   else "No key",
        "football_api":   "Ready" if football_ready() else "No key",
        "auto_trading":   "OFF",
        "paper_mode":     "ON",
        "risk_guard":     "ON",
    }
