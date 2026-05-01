"""
scanner_config.py
Reads all configuration from .env / environment variables.
Never hardcodes API keys or private key content.
App runs safely with all keys missing — defaults to MOCK mode.

Data modes:
  MOCK            — always works, no keys needed
  KALSHI_PUBLIC   — public Kalshi REST endpoint, no auth required
  KALSHI_AUTH_TEST— test RSA auth, then load public data
  HYBRID          — Kalshi public + mock rows side by side
  KALSHI_LIVE     — legacy alias for KALSHI_AUTH_TEST
"""

import os
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    _env = Path(__file__).parent / ".env"
    if _env.exists():
        load_dotenv(_env)
except ImportError:
    pass  # python-dotenv not installed — os.environ still works


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in ("true", "1", "yes")

def _float(key: str, default: float) -> float:
    try:   return float(os.getenv(key, str(default)).strip())
    except: return default

def _int(key: str, default: int) -> int:
    try:   return int(os.getenv(key, str(default)).strip())
    except: return default


# ── Core safety ───────────────────────────────────────────────────────────
AUTO_TRADING_ENABLED = False   # hardcoded OFF — never reads from env
PAPER_MODE           = True

# ── Data mode ─────────────────────────────────────────────────────────────
DATA_MODE = os.getenv("DATA_MODE", "MOCK").strip().upper()
# Normalise legacy alias
if DATA_MODE == "KALSHI_LIVE":
    DATA_MODE = "KALSHI_AUTH_TEST"

VALID_MODES = {"MOCK", "KALSHI_PUBLIC", "KALSHI_AUTH_TEST", "HYBRID"}

# ── Kalshi environment ────────────────────────────────────────────────────
KALSHI_ENV = os.getenv("KALSHI_ENV", "prod").strip().lower()

# Public REST base URLs (no auth required for GET /markets)
KALSHI_PROD_API_BASE = os.getenv(
    "KALSHI_PROD_API_BASE",
    "https://api.elections.kalshi.com/trade-api/v2"
).strip().rstrip("/")

KALSHI_DEMO_API_BASE = os.getenv(
    "KALSHI_DEMO_API_BASE",
    "https://demo-api.kalshi.co/trade-api/v2"
).strip().rstrip("/")

# Which base to use
def kalshi_base_url() -> str:
    if KALSHI_ENV == "demo":
        return KALSHI_DEMO_API_BASE
    return KALSHI_PROD_API_BASE

# ── Kalshi credentials (for auth phases only) ─────────────────────────────
KALSHI_API_KEY_ID       = os.getenv("KALSHI_API_KEY_ID",       "").strip()
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", "").strip()

# Legacy key names (fall back for compatibility)
if not KALSHI_API_KEY_ID:
    KALSHI_API_KEY_ID = os.getenv("KALSHI_API_KEY", "").strip()
if not KALSHI_PRIVATE_KEY_PATH:
    KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", "").strip()

# ── Other feeds ───────────────────────────────────────────────────────────
ODDS_API_KEY     = os.getenv("ODDS_API_KEY",     "").strip()

# ── API-Football key + provider (multi-name fallback) ─────────────────────
def get_api_football_key() -> str:
    """
    Return API-Football key from env. Checks names in priority order:
      1. API_FOOTBALL_KEY   (preferred)
      2. FOOTBALL_API_KEY   (legacy)
      3. RAPIDAPI_KEY       (RapidAPI wrapper)
    Returns "" if all empty. Never logs the key value.
    """
    for var_name in ("API_FOOTBALL_KEY", "FOOTBALL_API_KEY", "RAPIDAPI_KEY"):
        val = os.getenv(var_name, "").strip()
        if val:
            return val
    return ""

def get_api_football_provider() -> str:
    """
    Return the API provider name from API_FOOTBALL_PROVIDER env var.
    Default = "apisports". Valid: "apisports" | "rapidapi".
    """
    raw = os.getenv("API_FOOTBALL_PROVIDER", "apisports").strip().lower()
    return "rapidapi" if raw == "rapidapi" else "apisports"

# Keep FOOTBALL_API_KEY for backward compat — resolves to whichever var is set
FOOTBALL_API_KEY = get_api_football_key()

# ── Fair price model ─────────────────────────────────────────────────────
# Default false — signal stays DATA NEEDED until a real model is enabled
ENABLE_FAIR_PRICE_MODEL = _bool("ENABLE_FAIR_PRICE_MODEL", False)

# ── Crypto reference source ───────────────────────────────────────────────
# Options: auto | mock | coingecko | binance | coinbase
CRYPTO_PRICE_SOURCE = os.getenv("CRYPTO_PRICE_SOURCE", "auto").strip().lower()

# ── Scanner defaults ──────────────────────────────────────────────────────
SCANNER_MIN_EDGE       = _float("MIN_EDGE_CENTS",        8.0)
SCANNER_MAX_SPREAD     = _float("MAX_SPREAD_CENTS",      5.0)
SCANNER_MAX_TRADE_SIZE = _float("MAX_TRADE_SIZE",       10.0)
SCANNER_DAILY_LOSS     = _float("MAX_DAILY_LOSS",       30.0)
SCANNER_REFRESH_SEC    = _int("LIVE_REFRESH_SECONDS",   15)

# Legacy env names (keep backward compat)
if SCANNER_MIN_EDGE   == 8.0:  SCANNER_MIN_EDGE   = _float("SCANNER_MIN_EDGE",    8.0)
if SCANNER_MAX_SPREAD == 5.0:  SCANNER_MAX_SPREAD = _float("SCANNER_MAX_SPREAD",  5.0)
if SCANNER_REFRESH_SEC== 15:   SCANNER_REFRESH_SEC= _int("SCANNER_REFRESH_SECONDS", 15)


# ── Credential checks ──────────────────────────────────────────────────────

def kalshi_auth_ready() -> bool:
    """True if both API key ID and private key file are configured."""
    if not KALSHI_API_KEY_ID:
        return False
    if not KALSHI_PRIVATE_KEY_PATH:
        return False
    return Path(KALSHI_PRIVATE_KEY_PATH).exists()

# Legacy alias
def kalshi_ready() -> bool:
    return kalshi_auth_ready()

def odds_ready() -> bool:
    return bool(ODDS_API_KEY)

def football_ready() -> bool:
    return bool(get_api_football_key())


# ── Effective mode ─────────────────────────────────────────────────────────

def effective_mode() -> str:
    """
    Return the actual data mode the app will use.

    KALSHI_PUBLIC    — no credentials needed; works if internet is available
    KALSHI_AUTH_TEST — needs API key + private key file to exist
    HYBRID           — Kalshi public + mock; falls back to mock if unavailable
    MOCK             — always works
    """
    mode = DATA_MODE if DATA_MODE in VALID_MODES else "MOCK"

    if mode == "KALSHI_AUTH_TEST" and not kalshi_auth_ready():
        return "MOCK"   # missing credentials → silent fallback

    return mode


# ── Status report for UI ───────────────────────────────────────────────────

def status_report() -> dict:
    pk_path = KALSHI_PRIVATE_KEY_PATH
    pk_exists = Path(pk_path).exists() if pk_path else False

    kalshi_pub_status  = "Configured"          # public needs no keys
    kalshi_auth_status = (
        "Ready"          if kalshi_auth_ready()     else
        "Missing key"    if not KALSHI_API_KEY_ID   else
        "Missing PEM"    if not pk_path             else
        "PEM not found"
    )

    return {
        "data_mode":        effective_mode(),
        "kalshi_env":       KALSHI_ENV,
        "kalshi_public":    kalshi_pub_status,
        "kalshi_auth":      kalshi_auth_status,
        "odds_api":         "Ready" if odds_ready() else "No key",
        "football_api":     "configured" if football_ready() else "missing",
        "auto_trading":     "OFF",
        "paper_mode":       "ON",
        "risk_guard":       "ON",
    }
