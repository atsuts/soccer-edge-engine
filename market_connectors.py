"""
market_connectors.py
All market data connectors.

Connector hierarchy:
  BaseMarketConnector          ← all connectors inherit this
  MockMarketConnector          ← always works, no keys needed
  KalshiPublicConnector        ← public REST, no auth (Phase 1)
  KalshiAuthConnector          ← RSA-PSS signed requests (Phase 2)
  DataLayer                    ← routes to correct connector(s)

Safety rules enforced here:
  - No buy/sell/order calls exist in this file.
  - AUTO_TRADING_ENABLED is always False (never read from env here).
  - All network calls have timeouts.
  - All exceptions are caught — callers never crash.
"""

import os
import time
import random
import hashlib
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from market_models import (
    MarketSnapshot, OrderbookSnapshot, OrderbookLevel,
    normalize_orderbook, calculate_best_bid_ask,
    enrich_snapshot_from_orderbook, now_ts,
    parse_kalshi_price,
)


# ── Base connector ─────────────────────────────────────────────────────────

class BaseMarketConnector:
    """All connectors share this interface."""
    name: str = "base"

    def get_markets(self, limit: int = 50) -> List[MarketSnapshot]:
        raise NotImplementedError

    def get_orderbook(self, ticker: str) -> Optional[OrderbookSnapshot]:
        return None

    def _safe_float(self, val, default: float = 0.0) -> float:
        try:   return float(val) if val is not None else default
        except: return default

    def _safe_int(self, val, default: int = 0) -> int:
        try:   return int(val) if val is not None else default
        except: return default

    def _safe_str(self, val, default: str = "") -> str:
        return str(val).strip() if val is not None else default


# ── Mock data ──────────────────────────────────────────────────────────────

_MOCK_MARKETS = [
    {"ticker":"BTC-76K-1PM",     "title":"BTC above $76,266 by 1pm",                "category":"Crypto",
     "side":"NO",  "yes_bid":56,"yes_ask":57,"no_bid":43,"no_ask":44,"last":44,"fair":53,"volume":4200,"oi":1800,
     "expiry":"2026-04-30T13:00:00Z","settlement":"CoinGecko BTC/USD","underlying":76266.0,"liquidity":"High"},
    {"ticker":"BTC-76K-1PM-YES", "title":"BTC above $76,266 by 1pm",                "category":"Crypto",
     "side":"YES", "yes_bid":56,"yes_ask":57,"no_bid":43,"no_ask":44,"last":57,"fair":47,"volume":4200,"oi":1800,
     "expiry":"2026-04-30T13:00:00Z","settlement":"CoinGecko BTC/USD","underlying":76266.0,"liquidity":"High"},
    {"ticker":"ETH-3100",        "title":"ETH above $3,100 by close",                "category":"Crypto",
     "side":"YES", "yes_bid":38,"yes_ask":41,"no_bid":59,"no_ask":62,"last":40,"fair":50,"volume":1800,"oi":620,
     "expiry":"2026-04-30T21:00:00Z","settlement":"CoinGecko ETH/USD","underlying":3087.0,"liquidity":"Medium"},
    {"ticker":"FED-JUNE-CUT",    "title":"Fed rate cut in June",                     "category":"Economics",
     "side":"YES", "yes_bid":62,"yes_ask":65,"no_bid":35,"no_ask":38,"last":63,"fair":58,"volume":9100,"oi":4400,
     "expiry":"2026-06-15T18:00:00Z","settlement":"Fed.gov press release","underlying":None,"liquidity":"High"},
    {"ticker":"CPI-3.2",         "title":"US CPI above 3.2% next report",            "category":"Economics",
     "side":"NO",  "yes_bid":44,"yes_ask":46,"no_bid":54,"no_ask":56,"last":45,"fair":55,"volume":3300,"oi":1200,
     "expiry":"2026-05-14T12:30:00Z","settlement":"BLS CPI release","underlying":None,"liquidity":"Medium"},
    {"ticker":"BTC-75K-DAY",     "title":"BTC daily close above $75k",               "category":"Crypto",
     "side":"YES", "yes_bid":71,"yes_ask":74,"no_bid":26,"no_ask":29,"last":72,"fair":79,"volume":6700,"oi":3100,
     "expiry":"2026-04-30T23:59:00Z","settlement":"CoinGecko BTC/USD","underlying":76266.0,"liquidity":"High"},
    {"ticker":"SOC-MANCITY-WIN", "title":"Man City vs Liverpool — Man City Win",      "category":"Soccer",
     "side":"YES", "yes_bid":48,"yes_ask":51,"no_bid":49,"no_ask":52,"last":50,"fair":59,"volume":8800,"oi":3200,
     "expiry":"2026-04-11T21:00:00Z","settlement":"Premier League result","underlying":None,"liquidity":"High"},
    {"ticker":"SOC-ARS-CHE-OVER","title":"Arsenal vs Chelsea — Over 2.5 goals",      "category":"Soccer",
     "side":"YES", "yes_bid":52,"yes_ask":55,"no_bid":45,"no_ask":48,"last":54,"fair":64,"volume":6200,"oi":2100,
     "expiry":"2026-04-11T21:00:00Z","settlement":"Premier League result","underlying":None,"liquidity":"High"},
    {"ticker":"SOC-RM-BAR-BTTS", "title":"Real Madrid vs Barcelona — BTTS",          "category":"Soccer",
     "side":"YES", "yes_bid":58,"yes_ask":61,"no_bid":39,"no_ask":42,"last":60,"fair":67,"volume":9300,"oi":4100,
     "expiry":"2026-04-12T20:00:00Z","settlement":"La Liga result","underlying":None,"liquidity":"High"},
    {"ticker":"GOLD-2400",       "title":"Gold above $2,400 by Friday",               "category":"Economics",
     "side":"YES", "yes_bid":47,"yes_ask":50,"no_bid":50,"no_ask":53,"last":48,"fair":58,"volume":2100,"oi":880,
     "expiry":"2026-05-02T21:00:00Z","settlement":"COMEX Gold settlement","underlying":2388.0,"liquidity":"Medium"},
]

_MOCK_ORDERBOOKS = {
    # Prices are integer cents (0-100). normalize_orderbook converts to dollars.
    # NO bids must = 100 - YES ask, so that YES ask derived from complement = correct value.
    "BTC-76K-1PM": {"orderbook":{"yes":[{"price":56,"delta":200},{"price":55,"delta":150},{"price":54,"delta":300}],"no":[{"price":43,"delta":180},{"price":42,"delta":220},{"price":41,"delta":90}]}},
    "ETH-3100":    {"orderbook":{"yes":[{"price":38,"delta":80},{"price":37,"delta":60}],"no":[{"price":59,"delta":70},{"price":58,"delta":40}]}},
    "FED-JUNE-CUT":{"orderbook":{"yes":[{"price":62,"delta":500},{"price":61,"delta":300},{"price":60,"delta":800}],"no":[{"price":35,"delta":400},{"price":34,"delta":200}]}},
    "SOC-MANCITY-WIN":{"orderbook":{"yes":[{"price":48,"delta":400},{"price":47,"delta":250}],"no":[{"price":49,"delta":380},{"price":48,"delta":180}]}},
}


class MockMarketConnector(BaseMarketConnector):
    """
    Sample data connector. Always works — no API key needed.
    Adds slight random drift to prices to simulate live feed.
    """
    name = "mock"

    def get_markets(self, limit: int = 50) -> List[MarketSnapshot]:
        snapshots = []
        ts = now_ts()
        for m in _MOCK_MARKETS[:limit]:
            d = random.randint(-1, 1)
            # Convert cents to dollars, apply drift to mid-price only.
            # Keep spread fixed so ask > bid is always guaranteed.
            yb = round(max(1, m["yes_bid"] + d) / 100.0, 4)
            ya = round(yb + (m["yes_ask"] - m["yes_bid"]) / 100.0, 4)   # spread preserved
            nb = round(max(1, m["no_bid"] + d) / 100.0, 4)
            na = round(nb + (m["no_ask"] - m["no_bid"]) / 100.0, 4)
            def c2d(c): return round(max(1, c + d) / 100.0, 4)
            snap = MarketSnapshot(
                source="mock", market_id=m["ticker"], ticker=m["ticker"],
                title=m["title"], category=m["category"], side=m["side"],
                yes_bid=yb, yes_ask=ya,
                no_bid=nb,  no_ask=na,
                last_price=c2d(m["last"]), volume=m["volume"],
                open_interest=m["oi"], expiration_time=m["expiry"],
                settlement_source=m["settlement"], underlying_price=m["underlying"],
                model_fair_price=round(m["fair"] / 100.0, 6), timestamp=ts,
                liquidity_score=m["liquidity"], status="open",
            )
            ob = self.get_orderbook(m["ticker"])
            if ob:
                snap = enrich_snapshot_from_orderbook(snap, ob)
                snap.entry_price_est = snap.ask_price
                snap.exit_price_est  = round(snap.bid_price + (snap.fair_price - snap.ask_price)*0.6, 1)
            snapshots.append(snap)
        return snapshots

    def get_orderbook(self, ticker: str) -> Optional[OrderbookSnapshot]:
        raw = _MOCK_ORDERBOOKS.get(ticker)
        if not raw:
            return None
        try:
            d = random.randint(-1, 1)
            drifted = {"orderbook": {
                "yes": [{"price": max(1, l["price"]+d), "delta": l["delta"]} for l in raw["orderbook"].get("yes",[])],
                "no":  [{"price": max(1, l["price"]+d), "delta": l["delta"]} for l in raw["orderbook"].get("no", [])],
            }}
            return normalize_orderbook(drifted, ticker)
        except Exception as e:
            print(f"[mock orderbook] {ticker}: {e}")
            return None


# ── Kalshi public connector (Phase 1 — no auth required) ──────────────────

class KalshiPublicConnector(BaseMarketConnector):
    """
    Fetches public Kalshi market data via REST GET /markets.
    No authentication required for this endpoint.
    No orders. No account access. Read-only.

    Endpoint: GET {base_url}/markets?limit=N
    Docs: https://trading-api.kalshi.com/trade-api/v2/docs
    """
    name = "kalshi_public"

    def __init__(self, log_fn=None):
        from scanner_config import kalshi_base_url
        self.base_url  = kalshi_base_url()
        self._log      = log_fn or print
        self._last_err = ""

    def _get_json(self, path: str, params: dict = None) -> dict:
        """
        HTTP GET with timeout. Returns parsed JSON or {} on any error.
        Never raises.
        """
        try:
            import requests
        except ImportError:
            self._last_err = "requests not installed: pip install requests"
            return {}
        try:
            url  = f"{self.base_url}{path}"
            resp = requests.get(url, params=params or {}, timeout=10,
                                headers={"Accept": "application/json"})
            if resp.status_code == 200:
                return resp.json()
            self._last_err = f"HTTP {resp.status_code}: {resp.text[:120]}"
            return {}
        except Exception as e:
            self._last_err = str(e)[:120]
            return {}

    def get_markets(self, limit: int = 50) -> List[MarketSnapshot]:
        """
        Fetch open markets from Kalshi public/auth endpoint.
        NOTE: /markets does NOT return bid/ask prices.
             Bid/ask come from /markets/{ticker}/orderbook (per-market).
             All markets load with bid/ask = None (shown as N/A in UI).
             User clicks "Load Orderbook" to fetch prices for selected market.
        Returns [] on any error — caller handles fallback.
        """
        self._log("Requesting Kalshi public markets…")
        data = self._get_json("/markets", {"limit": limit, "status": "open"})

        raw_list = data.get("markets", [])
        if not raw_list:
            self._last_err = self._last_err or "No markets in response"
            self._log(f"Kalshi: {self._last_err}")
            return []

        snapshots = []
        missing_prices = 0
        for raw in raw_list:
            snap = self.normalize_market(raw)
            if snap:
                # Count markets where bid/ask were found in the response
                if snap.yes_bid is None and snap.yes_ask is None:
                    missing_prices += 1
                snapshots.append(snap)

        has_prices = len(snapshots) - missing_prices
        if has_prices > 0:
            self._log(f"Loaded {len(snapshots)} Kalshi markets "
                      f"({has_prices} with prices, {missing_prices} N/A)")
        else:
            self._log(f"Loaded {len(snapshots)} Kalshi markets "
                      f"(bid/ask N/A — click 'Load Orderbook' for a selected market)")
        return snapshots

    def normalize_market(self, raw: dict) -> Optional[MarketSnapshot]:
        """
        Convert one Kalshi API v2 market dict to MarketSnapshot.

        Kalshi v2 /markets response fields:
          ticker            string   e.g. "KXBTCD-25APR30-B76266"
          event_ticker      string
          title             string   human-readable name
          subtitle          string
          category          string   "crypto" | "economics" | "politics" | "sports"
          market_type       "binary" | "scalar"
          status            "open" | "closed" | "settled" | "finalized"
          open_time         ISO datetime
          close_time        ISO datetime  ← expiration
          last_price        int (cents 0-100) ← most recent trade; 0 if no trades
          previous_price    int (cents)
          volume            int  (contracts traded)
          volume_24h        int
          open_interest     int  (contracts open)
          notional_value    int
          result            string (after settlement only)
          yes_sub_title     string
          no_sub_title      string
          can_close_early   bool
          expiration_value  string (settlement description)

        Actual Kalshi v2 fields observed in live responses:
          yes_bid_dollars          "0.5000"   string decimal (dollars)
          yes_ask_dollars          "0.5000"
          no_bid_dollars           "0.5000"
          no_ask_dollars           "0.5000"
          last_price_dollars       "0.5000"
          previous_price_dollars   "0.5000"
          previous_yes_bid_dollars "0.5000"
          previous_yes_ask_dollars "0.5000"

        Legacy integer cent fields may also appear:
          yes_bid / yes_ask / no_bid / no_ask  (int 0-100)
          last_price / previous_price          (int 0-100)

        Strategy: prefer *_dollars fields; fall back to integer fields.
        parse_kalshi_price() handles both formats → internal dollar float.
        format_price() converts dollar float → display string "50c".
        """
        try:
            ticker = self._safe_str(raw.get("ticker"))
            if not ticker:
                return None

            # Category mapping
            cat_map = {
                "crypto":     "Crypto",
                "economics":  "Economics",
                "politics":   "Politics",
                "sports":     "Soccer",
                "financials": "Economics",
                "climate":    "Economics",
                "science":    "Economics",
            }
            raw_cat  = self._safe_str(raw.get("category", "other")).lower()
            category = cat_map.get(raw_cat, raw_cat.title() or "Other")

            # ── Price fields ────────────────────────────────────────────
            # Prefer *_dollars (decimal string); fall back to int cents fields.
            # parse_kalshi_price(None) → None (missing, shows N/A)
            # parse_kalshi_price("0.5000") → 0.50 (shows 50c)
            # parse_kalshi_price(56) → 0.56 (shows 56c)

            def _price(dollars_key: str, cents_key: str = None):
                """Try dollars field first, then cents field, return None if both missing."""
                v = raw.get(dollars_key)
                if v is not None:
                    return parse_kalshi_price(v)
                if cents_key:
                    v2 = raw.get(cents_key)
                    if v2 is not None:
                        return parse_kalshi_price(v2)
                return None

            yes_bid    = _price("yes_bid_dollars",   "yes_bid")
            yes_ask    = _price("yes_ask_dollars",   "yes_ask")
            no_bid     = _price("no_bid_dollars",    "no_bid")
            no_ask     = _price("no_ask_dollars",    "no_ask")

            # last_price: try dollars first, then cents, then previous as fallback
            last_price = (
                _price("last_price_dollars",     "last_price") or
                _price("previous_price_dollars", "previous_price")
            )

            # Apply 100-cent complement rule to fill missing sides
            # YES + NO = 1.00 (dollar) at settlement → no_ask = 1 - yes_bid, etc.
            if yes_bid is not None and no_ask is None:
                no_ask = round(1.0 - yes_bid, 6)
            if yes_ask is not None and no_bid is None:
                no_bid = round(1.0 - yes_ask, 6)
            if no_bid is not None and yes_ask is None:
                yes_ask = round(1.0 - no_bid, 6)
            if no_ask is not None and yes_bid is None:
                yes_bid = round(1.0 - no_ask, 6)

            # Choose which side to analyse: YES or NO — pick lower ask (cheaper entry)
            ya = yes_ask
            na = no_ask
            if ya is not None and na is not None:
                side = "YES" if ya <= na else "NO"
            elif ya is not None:
                side = "YES"
            elif na is not None:
                side = "NO"
            else:
                side = "YES"   # default when no prices available yet

            return MarketSnapshot(
                source            = "kalshi",
                market_id         = ticker,
                ticker            = ticker,
                title             = self._safe_str(raw.get("title", ticker)),
                category          = category,
                side              = side,
                yes_bid           = yes_bid,
                yes_ask           = yes_ask,
                no_bid            = no_bid,
                no_ask            = no_ask,
                last_price        = last_price,
                volume            = self._safe_int(raw.get("volume",        0)),
                open_interest     = self._safe_int(raw.get("open_interest", 0)),
                expiration_time   = self._safe_str(raw.get("close_time", "N/A")),
                settlement_source = self._safe_str(raw.get("expiration_value", "Kalshi")),
                underlying_price  = None,
                model_fair_price  = None,   # no fair price from exchange → DATA NEEDED
                timestamp         = now_ts(),
                liquidity_score   = "Medium",
                status            = self._safe_str(raw.get("status", "open")),
                raw_data          = raw,
            )
        except Exception as e:
            print(f"[normalize_market] {raw.get('ticker','?')}: {e}")
            return None

    def get_orderbook(self, ticker: str) -> Optional[OrderbookSnapshot]:
        """
        Fetch orderbook for one market.
        GET /markets/{ticker}/orderbook
        Returns None on any error.
        """
        if not ticker:
            return None
        try:
            raw = self._get_json(f"/markets/{ticker}/orderbook")
            if not raw:
                return None
            return normalize_orderbook(raw, ticker)
        except Exception as e:
            print(f"[kalshi orderbook] {ticker}: {e}")
            return None

    def last_error(self) -> str:
        return self._last_err


# ── Kalshi auth connector (Phase 2 — RSA-PSS signing) ─────────────────────

class KalshiAuthConnector(KalshiPublicConnector):
    """
    Adds RSA-PSS SHA-256 authentication to Kalshi requests.
    Extends KalshiPublicConnector — all market/orderbook methods inherited.

    Kalshi auth (v2) uses:
      Header: KALSHI-ACCESS-KEY        ← your API Key ID
      Header: KALSHI-ACCESS-TIMESTAMP  ← Unix ms timestamp as string
      Header: KALSHI-ACCESS-SIGNATURE  ← base64(RSA-PSS-SHA256(msg, private_key))

    where msg = timestamp_str + method + path

    Required packages: pip install requests cryptography

    IMPORTANT:
      - Private key is loaded from file — never from env var directly.
      - Private key content is never logged or printed.
      - Only read-only endpoints are called here.
      - No buy/sell/order endpoints exist in this class.
    """
    name = "kalshi_auth"

    def __init__(self, log_fn=None):
        super().__init__(log_fn=log_fn)
        from scanner_config import KALSHI_API_KEY_ID, KALSHI_PRIVATE_KEY_PATH
        self._api_key_id  = KALSHI_API_KEY_ID
        self._pem_path    = KALSHI_PRIVATE_KEY_PATH
        self._private_key = None   # loaded lazily, never printed
        self._auth_ok     = False
        self._auth_err    = ""

    def _load_private_key(self) -> bool:
        """Load PEM private key from file. Returns True on success."""
        if self._private_key is not None:
            return True
        if not self._pem_path:
            self._auth_err = "KALSHI_PRIVATE_KEY_PATH not set"
            return False
        pem_file = Path(self._pem_path)
        if not pem_file.exists():
            self._auth_err = f"Private key file not found: {self._pem_path}"
            return False
        try:
            from cryptography.hazmat.primitives import serialization
            with open(pem_file, "rb") as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(), password=None)
            return True
        except ImportError:
            self._auth_err = "cryptography not installed: pip install cryptography"
            return False
        except Exception as e:
            self._auth_err = f"Failed to load private key: {e}"
            return False

    def _sign(self, timestamp_ms: str, method: str, path: str) -> str:
        """
        Build RSA-PSS SHA-256 signature.
        msg = timestamp_ms_str + METHOD + /path
        Returns base64-encoded signature string.
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        msg       = (timestamp_ms + method.upper() + path).encode("utf-8")
        signature = self._private_key.sign(msg, padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ), hashes.SHA256())
        return base64.b64encode(signature).decode("utf-8")

    def _auth_headers(self, method: str, path: str) -> dict:
        """Return auth headers dict for one request."""
        ts = str(int(time.time() * 1000))
        return {
            "KALSHI-ACCESS-KEY":       self._api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": self._sign(ts, method, path),
            "Accept":                  "application/json",
        }

    def _get_json(self, path: str, params: dict = None) -> dict:
        """Override: add auth headers to all requests."""
        if not self._api_key_id:
            self._last_err = "API key ID not configured"
            return {}
        if not self._load_private_key():
            self._last_err = self._auth_err
            return {}
        try:
            import requests
            url  = f"{self.base_url}{path}"
            hdrs = self._auth_headers("GET", path)
            resp = requests.get(url, params=params or {}, headers=hdrs, timeout=10)
            if resp.status_code == 200:
                self._auth_ok = True
                return resp.json()
            elif resp.status_code == 401:
                self._auth_err = "Auth failed — check API key ID and private key"
                self._auth_ok  = False
            elif resp.status_code == 403:
                self._auth_err = "Forbidden — key may not have market data permission"
                self._auth_ok  = False
            else:
                self._last_err = f"HTTP {resp.status_code}: {resp.text[:120]}"
            return {}
        except ImportError:
            self._last_err = "requests not installed: pip install requests"
            return {}
        except Exception as e:
            self._last_err = str(e)[:120]
            return {}

    def test_auth(self) -> tuple:
        """
        Test authentication using a safe read-only endpoint.
        Returns (success: bool, message: str).
        Does NOT log private key or balance.
        """
        if not self._api_key_id:
            return False, "Missing key: KALSHI_API_KEY_ID not set"
        if not self._load_private_key():
            return False, f"Missing key file: {self._auth_err}"

        # Use /exchange/status — lightweight, no sensitive data
        data = self._get_json("/exchange/status")
        if data:
            self._auth_ok = True
            return True, "Auth: Connected"
        if self._auth_err:
            return False, f"Auth: Failed — {self._auth_err}"
        return False, f"Auth: Failed — {self._last_err or 'unknown error'}"

    def auth_status(self) -> str:
        if not self._api_key_id:
            return "Missing key"
        pem = Path(self._pem_path) if self._pem_path else None
        if not pem or not pem.exists():
            return "Missing PEM file"
        if self._auth_ok:
            return "Connected"
        return "Not tested"


# ── Placeholder connectors ─────────────────────────────────────────────────

class OddsAPIConnector(BaseMarketConnector):
    """TODO: The Odds API. Needs ODDS_API_KEY."""
    name = "odds_api"
    def get_markets(self, limit: int = 50) -> List[MarketSnapshot]:
        return []

class SoccerModelConnector(BaseMarketConnector):
    """Local soccer engine fair prices as market snapshots."""
    name = "soccer_model"
    def get_markets(self, limit: int = 50) -> List[MarketSnapshot]:
        return []


# ── Data layer — main entry point ─────────────────────────────────────────

class DataLayer:
    """
    Routes to the correct connector(s) based on DATA_MODE.
    Handles fallback, error logging, and status reporting.

    Mode routing:
      MOCK             → MockMarketConnector
      KALSHI_PUBLIC    → KalshiPublicConnector  (no auth)
      KALSHI_AUTH_TEST → KalshiAuthConnector → test auth, then load public data
      HYBRID           → KalshiPublicConnector + MockMarketConnector (merged)
    """

    def __init__(self, log_fn=None):
        self._log      = log_fn or print
        self._mock     = MockMarketConnector()
        self._kalshi_pub  = None   # created on first use
        self._kalshi_auth = None   # created on first use
        self._last_update = "Never"
        self._last_source = "—"
        self._last_count  = 0
        self._last_error  = ""
        self._snapshot_cache: dict = {}   # ticker → MarketSnapshot

    def _get_kalshi_pub(self) -> KalshiPublicConnector:
        if self._kalshi_pub is None:
            self._kalshi_pub = KalshiPublicConnector(log_fn=self._log)
        return self._kalshi_pub

    def _get_kalshi_auth(self) -> KalshiAuthConnector:
        if self._kalshi_auth is None:
            self._kalshi_auth = KalshiAuthConnector(log_fn=self._log)
        return self._kalshi_auth

    def fetch(self, category_filter: str = "All") -> tuple:
        """
        Fetch markets based on current DATA_MODE.
        Returns (list[dict], source_label, error_str).
        dict format is what market_scanner_engine.run_scanner() expects.
        """
        from scanner_config import effective_mode
        mode = effective_mode()
        self._log(f"Data mode: {mode}")

        snapshots: List[MarketSnapshot] = []
        source = mode
        error  = ""

        try:
            if mode == "MOCK":
                snapshots = self._mock.get_markets()
                source    = "MOCK"

            elif mode == "KALSHI_PUBLIC":
                conn      = self._get_kalshi_pub()
                snapshots = conn.get_markets()
                if not snapshots:
                    error = conn.last_error()
                    self._log(f"Kalshi public failed: {error}")
                    self._log("Falling back to mock data")
                    snapshots = self._mock.get_markets()
                    source    = "MOCK (fallback)"
                else:
                    source = "KALSHI_PUBLIC"

            elif mode == "KALSHI_AUTH_TEST":
                auth = self._get_kalshi_auth()
                ok, msg = auth.test_auth()
                self._log(msg)
                if ok:
                    self._log("Kalshi auth connected — loading market data")
                    snapshots = auth.get_markets()
                    source    = "KALSHI_AUTH"
                else:
                    self._log("Auth failed — loading public data instead")
                    pub       = self._get_kalshi_pub()
                    snapshots = pub.get_markets()
                    source    = "KALSHI_PUBLIC (auth fallback)"
                if not snapshots:
                    self._log("Kalshi unavailable — using mock data")
                    snapshots = self._mock.get_markets()
                    source    = "MOCK (fallback)"

            elif mode == "HYBRID":
                pub  = self._get_kalshi_pub()
                live = pub.get_markets()
                mock = self._mock.get_markets()
                # Tag source on each snapshot
                for s in live:
                    s.source = "kalshi"
                for s in mock:
                    s.source = "mock"
                snapshots = live + mock
                source    = "HYBRID" if live else "MOCK (hybrid fallback)"
                if not live:
                    self._log(f"Kalshi unavailable: {pub.last_error()}")

            else:
                self._log(f"Unknown mode '{mode}' — using MOCK")
                snapshots = self._mock.get_markets()
                source    = "MOCK"

        except Exception as e:
            error = str(e)
            self._log(f"Fetch error: {e} — using mock data")
            try:
                snapshots = self._mock.get_markets()
                source    = "MOCK (error fallback)"
            except Exception:
                snapshots = []

        # Category filter
        if category_filter and category_filter != "All":
            snapshots = [s for s in snapshots if s.category == category_filter]

        # Cache raw snapshots for detail lookup by ticker
        for snap in snapshots:
            self._snapshot_cache[snap.market_id] = snap

        # Convert to engine dicts
        dicts = [s.to_connector_dict() for s in snapshots]

        self._last_update = datetime.now().strftime("%H:%M:%S")
        self._last_source = source
        self._last_count  = len(dicts)
        self._last_error  = error

        self._log(f"Loaded {len(dicts)} markets from {source}")
        return dicts, source, error

    def get_snapshot(self, ticker: str) -> Optional[MarketSnapshot]:
        """Return the last known MarketSnapshot for a ticker, or None."""
        return self._snapshot_cache.get(ticker)

    def debug_price_summary(self) -> dict:
        """
        Return a summary of price field availability across loaded snapshots.
        Safe — never prints API keys.
        """
        snaps = list(self._snapshot_cache.values())
        if not snaps:
            return {"total": 0, "note": "No markets loaded yet"}

        def _has(attr, snap):
            v = getattr(snap, attr, None)
            return v is not None

        total     = len(snaps)
        with_yb   = sum(1 for s in snaps if _has("yes_bid",   s))
        with_ya   = sum(1 for s in snaps if _has("yes_ask",   s))
        with_nb   = sum(1 for s in snaps if _has("no_bid",    s))
        with_na   = sum(1 for s in snaps if _has("no_ask",    s))
        with_last = sum(1 for s in snaps if _has("last_price", s))
        with_fair = sum(1 for s in snaps if _has("model_fair_price", s))
        with_vol  = sum(1 for s in snaps if getattr(s, "volume", 0) > 0)

        first_snap = snaps[0]
        sample = {}
        if first_snap.raw_data:
            # Show non-null field names from first raw response (no values)
            sample = {k: type(v).__name__
                      for k, v in first_snap.raw_data.items()
                      if v is not None}

        return {
            "total":          total,
            "with_yes_bid":   with_yb,
            "with_yes_ask":   with_ya,
            "with_no_bid":    with_nb,
            "with_no_ask":    with_na,
            "with_last_price":with_last,
            "with_fair_price":with_fair,
            "with_volume":    with_vol,
            "source":         self._last_source,
            "sample_fields":  list(sample.keys())[:20],
        }

    def get_orderbook(self, ticker: str, source: str = "mock") -> Optional[OrderbookSnapshot]:
        """Route orderbook fetch to correct connector."""
        try:
            if "kalshi" in source.lower() or "KALSHI" in source:
                pub = self._get_kalshi_pub()
                ob  = pub.get_orderbook(ticker)
                if ob:
                    return ob
            return self._mock.get_orderbook(ticker)
        except Exception as e:
            self._log(f"Orderbook error {ticker}: {e}")
            return None

    def test_kalshi_auth(self) -> tuple:
        """Run auth test and return (ok, message)."""
        auth = self._get_kalshi_auth()
        ok, msg = auth.test_auth()
        self._log(msg)
        self._log("Auto trading remains OFF")
        return ok, msg

    def kalshi_auth_status(self) -> str:
        if self._kalshi_auth is None:
            return "Not tested"
        return self._kalshi_auth.auth_status()

    def status(self) -> dict:
        from scanner_config import status_report
        rep = status_report()
        rep["last_update"]   = self._last_update
        rep["last_source"]   = self._last_source
        rep["last_count"]    = self._last_count
        rep["last_error"]    = self._last_error
        rep["kalshi_auth_live"] = self.kalshi_auth_status()
        return rep


# ── Legacy shim ────────────────────────────────────────────────────────────

def get_connector(market_type: str) -> BaseMarketConnector:
    """Legacy function — kept for backward compatibility."""
    return MockMarketConnector()
