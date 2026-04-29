"""
market_connectors.py
All market data connectors. Each produces list[MarketSnapshot].
Orderbook data is fetched separately and used to enrich snapshots.

Data modes:
  MOCK        — always works, no keys needed, includes mock orderbooks
  KALSHI_LIVE — requires KALSHI_API_KEY + KALSHI_PRIVATE_KEY_PATH in .env
  HYBRID      — Kalshi live + mock fallback
"""

import os
import random
import time
from datetime import datetime
from typing import Optional, List

from market_models import (
    MarketSnapshot, OrderbookSnapshot, OrderbookLevel,
    normalize_orderbook, calculate_best_bid_ask,
    enrich_snapshot_from_orderbook, now_ts,
)


# ── Base connector ─────────────────────────────────────────────────────────

class BaseMarketConnector:
    """
    All connectors inherit from this.
    get_markets()    → list[MarketSnapshot]
    get_orderbook()  → OrderbookSnapshot | None
    """
    name: str = "base"

    def get_markets(self) -> List[MarketSnapshot]:
        raise NotImplementedError

    def get_orderbook(self, ticker: str) -> Optional[OrderbookSnapshot]:
        """
        Fetch orderbook for one market ticker.
        Returns None if unavailable — callers must handle None safely.
        """
        return None

    def _safe_float(self, val, default: float = 0.0) -> float:
        try:
            return float(val) if val is not None else default
        except (TypeError, ValueError):
            return default

    def _safe_int(self, val, default: int = 0) -> int:
        try:
            return int(val) if val is not None else default
        except (TypeError, ValueError):
            return default


# ── Mock orderbook data ────────────────────────────────────────────────────
#
# Each mock orderbook simulates realistic bid/ask ladders.
# Structure matches what Kalshi API returns:
#   "yes": list of {price, delta}  ← YES side bids
#   "no":  list of {price, delta}  ← NO side bids
# The ask side is derived using the 100-cent complement (see market_models.py).

_MOCK_ORDERBOOKS = {
    "BTC-76K-1PM": {
        "orderbook": {
            "yes": [
                {"price": 56, "delta": 200},   # best YES bid
                {"price": 55, "delta": 150},
                {"price": 54, "delta": 300},
                {"price": 52, "delta": 100},
            ],
            "no": [
                {"price": 44, "delta": 180},   # best NO bid → YES ask = 56c
                {"price": 43, "delta": 220},
                {"price": 42, "delta": 90},
            ],
        }
    },
    "BTC-76K-1PM-YES": {
        "orderbook": {
            "yes": [
                {"price": 56, "delta": 200},
                {"price": 55, "delta": 150},
            ],
            "no": [
                {"price": 43, "delta": 180},
                {"price": 42, "delta": 90},
            ],
        }
    },
    "ETH-3100": {
        "orderbook": {
            "yes": [
                {"price": 38, "delta": 80},
                {"price": 37, "delta": 60},
            ],
            "no": [
                {"price": 59, "delta": 70},
                {"price": 58, "delta": 40},
            ],
        }
    },
    "FED-JUNE-CUT": {
        "orderbook": {
            "yes": [
                {"price": 62, "delta": 500},
                {"price": 61, "delta": 300},
                {"price": 60, "delta": 800},
            ],
            "no": [
                {"price": 35, "delta": 400},
                {"price": 34, "delta": 200},
            ],
        }
    },
    "CPI-3.2": {
        "orderbook": {
            "yes": [
                {"price": 44, "delta": 120},
                {"price": 43, "delta": 80},
            ],
            "no": [
                {"price": 54, "delta": 100},
                {"price": 53, "delta": 60},
            ],
        }
    },
    "BTC-75K-DAY": {
        "orderbook": {
            "yes": [
                {"price": 71, "delta": 350},
                {"price": 70, "delta": 200},
                {"price": 69, "delta": 150},
            ],
            "no": [
                {"price": 26, "delta": 280},
                {"price": 25, "delta": 120},
            ],
        }
    },
    "SOC-MANCITY-WIN": {
        "orderbook": {
            "yes": [
                {"price": 48, "delta": 400},
                {"price": 47, "delta": 250},
            ],
            "no": [
                {"price": 49, "delta": 380},
                {"price": 48, "delta": 180},
            ],
        }
    },
    "SOC-ARS-CHE-OVER": {
        "orderbook": {
            "yes": [
                {"price": 52, "delta": 300},
                {"price": 51, "delta": 180},
            ],
            "no": [
                {"price": 45, "delta": 260},
                {"price": 44, "delta": 140},
            ],
        }
    },
    "SOC-RM-BAR-BTTS": {
        "orderbook": {
            "yes": [
                {"price": 58, "delta": 450},
                {"price": 57, "delta": 300},
                {"price": 56, "delta": 200},
            ],
            "no": [
                {"price": 39, "delta": 380},
                {"price": 38, "delta": 150},
            ],
        }
    },
    "GOLD-2400": {
        "orderbook": {
            "yes": [
                {"price": 47, "delta": 90},
                {"price": 46, "delta": 60},
            ],
            "no": [
                {"price": 50, "delta": 80},
                {"price": 49, "delta": 40},
            ],
        }
    },
}

# ── Mock market definitions ────────────────────────────────────────────────

_MOCK_MARKETS = [
    {
        "ticker": "BTC-76K-1PM",     "title": "BTC above $76,266 by 1pm",
        "category": "Crypto",         "side": "NO",
        "yes_bid": 56, "yes_ask": 57, "no_bid": 43, "no_ask": 44,
        "last": 44, "fair": 53,       "volume": 4200, "oi": 1800,
        "expiry": "2026-04-30T13:00:00Z",
        "settlement": "CoinGecko BTC/USD", "underlying": 76266.0,
        "liquidity": "High",
    },
    {
        "ticker": "BTC-76K-1PM-YES", "title": "BTC above $76,266 by 1pm",
        "category": "Crypto",         "side": "YES",
        "yes_bid": 56, "yes_ask": 57, "no_bid": 43, "no_ask": 44,
        "last": 57, "fair": 47,       "volume": 4200, "oi": 1800,
        "expiry": "2026-04-30T13:00:00Z",
        "settlement": "CoinGecko BTC/USD", "underlying": 76266.0,
        "liquidity": "High",
    },
    {
        "ticker": "ETH-3100",        "title": "ETH above $3,100 by close",
        "category": "Crypto",         "side": "YES",
        "yes_bid": 38, "yes_ask": 41, "no_bid": 59, "no_ask": 62,
        "last": 40, "fair": 50,       "volume": 1800, "oi": 620,
        "expiry": "2026-04-30T21:00:00Z",
        "settlement": "CoinGecko ETH/USD", "underlying": 3087.0,
        "liquidity": "Medium",
    },
    {
        "ticker": "FED-JUNE-CUT",    "title": "Fed rate cut in June",
        "category": "Economics",      "side": "YES",
        "yes_bid": 62, "yes_ask": 65, "no_bid": 35, "no_ask": 38,
        "last": 63, "fair": 58,       "volume": 9100, "oi": 4400,
        "expiry": "2026-06-15T18:00:00Z",
        "settlement": "Fed.gov press release", "underlying": None,
        "liquidity": "High",
    },
    {
        "ticker": "CPI-3.2",         "title": "US CPI above 3.2% next report",
        "category": "Economics",      "side": "NO",
        "yes_bid": 44, "yes_ask": 46, "no_bid": 54, "no_ask": 56,
        "last": 45, "fair": 55,       "volume": 3300, "oi": 1200,
        "expiry": "2026-05-14T12:30:00Z",
        "settlement": "BLS CPI release", "underlying": None,
        "liquidity": "Medium",
    },
    {
        "ticker": "BTC-75K-DAY",     "title": "BTC daily close above $75k",
        "category": "Crypto",         "side": "YES",
        "yes_bid": 71, "yes_ask": 74, "no_bid": 26, "no_ask": 29,
        "last": 72, "fair": 79,       "volume": 6700, "oi": 3100,
        "expiry": "2026-04-30T23:59:00Z",
        "settlement": "CoinGecko BTC/USD", "underlying": 76266.0,
        "liquidity": "High",
    },
    {
        "ticker": "SOC-MANCITY-WIN", "title": "Man City vs Liverpool — Man City Win",
        "category": "Soccer",         "side": "YES",
        "yes_bid": 48, "yes_ask": 51, "no_bid": 49, "no_ask": 52,
        "last": 50, "fair": 59,       "volume": 8800, "oi": 3200,
        "expiry": "2026-04-11T21:00:00Z",
        "settlement": "Premier League result", "underlying": None,
        "liquidity": "High",
    },
    {
        "ticker": "SOC-ARS-CHE-OVER","title": "Arsenal vs Chelsea — Over 2.5 goals",
        "category": "Soccer",         "side": "YES",
        "yes_bid": 52, "yes_ask": 55, "no_bid": 45, "no_ask": 48,
        "last": 54, "fair": 64,       "volume": 6200, "oi": 2100,
        "expiry": "2026-04-11T21:00:00Z",
        "settlement": "Premier League result", "underlying": None,
        "liquidity": "High",
    },
    {
        "ticker": "SOC-RM-BAR-BTTS", "title": "Real Madrid vs Barcelona — BTTS",
        "category": "Soccer",         "side": "YES",
        "yes_bid": 58, "yes_ask": 61, "no_bid": 39, "no_ask": 42,
        "last": 60, "fair": 67,       "volume": 9300, "oi": 4100,
        "expiry": "2026-04-12T20:00:00Z",
        "settlement": "La Liga result", "underlying": None,
        "liquidity": "High",
    },
    {
        "ticker": "GOLD-2400",       "title": "Gold above $2,400 by Friday",
        "category": "Economics",      "side": "YES",
        "yes_bid": 47, "yes_ask": 50, "no_bid": 50, "no_ask": 53,
        "last": 48, "fair": 58,       "volume": 2100, "oi": 880,
        "expiry": "2026-05-02T21:00:00Z",
        "settlement": "COMEX Gold settlement", "underlying": 2388.0,
        "liquidity": "Medium",
    },
]


# ── Mock connector ─────────────────────────────────────────────────────────

class MockMarketConnector(BaseMarketConnector):
    """
    Returns MarketSnapshot objects with mock data and mock orderbooks.
    Always works — no API key needed.
    Applies slight random drift to prices to simulate a live feed.
    """
    name = "mock"

    def get_markets(self) -> List[MarketSnapshot]:
        snapshots = []
        ts = now_ts()
        for m in _MOCK_MARKETS:
            drift = random.randint(-1, 1)

            snap = MarketSnapshot(
                source           = "mock",
                market_id        = m["ticker"],
                ticker           = m["ticker"],
                title            = m["title"],
                category         = m["category"],
                side             = m["side"],
                yes_bid          = float(max(1,  m["yes_bid"] + drift)),
                yes_ask          = float(max(2,  m["yes_ask"] + drift)),
                no_bid           = float(max(1,  m["no_bid"]  + drift)),
                no_ask           = float(max(2,  m["no_ask"]  + drift)),
                last_price       = float(max(1,  m["last"]    + drift)),
                volume           = m["volume"],
                open_interest    = m["oi"],
                expiration_time  = m["expiry"],
                settlement_source= m["settlement"],
                underlying_price = m["underlying"],
                model_fair_price = float(m["fair"]),
                timestamp        = ts,
                liquidity_score  = m["liquidity"],
                status           = "open",
            )

            # Enrich with mock orderbook
            ob = self.get_orderbook(m["ticker"])
            if ob:
                snap = enrich_snapshot_from_orderbook(snap, ob)

                # Estimate entry/exit prices from orderbook depth
                snap.entry_price_est = snap.ask_price
                snap.exit_price_est  = snap.bid_price + round(
                    (snap.fair_price - snap.ask_price) * 0.6, 1)

            snapshots.append(snap)
        return snapshots

    def get_orderbook(self, ticker: str) -> Optional[OrderbookSnapshot]:
        """
        Return mock orderbook for the given ticker.
        Applies small random drift to simulate live data.
        """
        raw = _MOCK_ORDERBOOKS.get(ticker)
        if not raw:
            return None
        try:
            # Apply small drift to mock prices
            drift = random.randint(-1, 1)
            drifted = {"orderbook": {"yes": [], "no": []}}
            for lvl in raw["orderbook"].get("yes", []):
                drifted["orderbook"]["yes"].append({
                    "price": max(1, lvl["price"] + drift),
                    "delta": lvl["delta"],
                })
            for lvl in raw["orderbook"].get("no", []):
                drifted["orderbook"]["no"].append({
                    "price": max(1, lvl["price"] + drift),
                    "delta": lvl["delta"],
                })
            return normalize_orderbook(drifted, ticker)
        except Exception as e:
            print(f"[mock orderbook] {ticker}: {e}")
            return None


# ── Kalshi connector ───────────────────────────────────────────────────────

class KalshiMarketConnector(BaseMarketConnector):
    """
    Kalshi live market connector.
    Read-only — no orders, no account calls, no portfolio actions.

    To activate:
    1. Add to .env:
         KALSHI_API_KEY=your_key
         KALSHI_PRIVATE_KEY_PATH=C:\\path\\to\\private_key.pem
    2. pip install requests cryptography

    Kalshi auth uses RSA private key + JWT (not basic auth).
    All endpoints used here are read-only market data endpoints.

    TODO items are clearly marked. App runs safely without them.
    """
    name = "kalshi"

    def __init__(self):
        from scanner_config import (
            KALSHI_API_KEY, KALSHI_PRIVATE_KEY_PATH, KALSHI_BASE_URL
        )
        self.api_key  = KALSHI_API_KEY
        self.key_path = KALSHI_PRIVATE_KEY_PATH
        self.base_url = KALSHI_BASE_URL.rstrip("/")
        self._headers = {}
        self._last_err = ""
        self._authenticated = False

    def _is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.key_path)

    def _authenticate(self) -> bool:
        """
        Build authenticated request headers using RSA private key.
        Kalshi uses JWT signed with the private key for all API calls.

        TODO: implement full JWT signing.
        Reference: https://trading-api.kalshi.com/trade-api/v2/docs

        Steps needed:
          1. Load RSA private key from self.key_path
          2. Build JWT payload with {sub: api_key, iat: now, exp: now+60}
          3. Sign JWT with RS256 algorithm
          4. Set header: Authorization: Bearer <jwt_token>

        Required package: pip install cryptography PyJWT
        """
        if not self._is_configured():
            self._last_err = "API key or private key path not configured"
            return False

        # TODO: implement JWT signing
        # import jwt
        # from cryptography.hazmat.primitives import serialization
        # with open(self.key_path, "rb") as f:
        #     private_key = serialization.load_pem_private_key(f.read(), password=None)
        # payload = {"sub": self.api_key, "iat": int(time.time()), "exp": int(time.time()) + 60}
        # token = jwt.encode(payload, private_key, algorithm="RS256")
        # self._headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        # self._authenticated = True
        # return True

        self._last_err = "Kalshi JWT auth not yet implemented (see TODO in code)"
        return False

    def _get(self, path: str, params: dict = None) -> dict:
        """
        Make authenticated GET request to Kalshi API.
        Returns parsed JSON dict, or empty dict on error.
        Never raises — logs errors and returns {}.

        Args:
            path:   API path e.g. "/markets"
            params: Optional query params dict
        """
        try:
            import requests
        except ImportError:
            self._last_err = "requests not installed: pip install requests"
            return {}

        if not self._authenticated and not self._authenticate():
            return {}

        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(
                url,
                headers=self._headers,
                params=params or {},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                self._last_err = "Kalshi auth failed — check API key"
                self._authenticated = False
                return {}
            elif resp.status_code == 429:
                self._last_err = "Kalshi rate limit hit — slow down requests"
                return {}
            else:
                self._last_err = f"HTTP {resp.status_code}: {resp.text[:100]}"
                return {}
        except Exception as e:
            self._last_err = str(e)
            return {}

    def _fetch_markets(self, params: dict = None) -> list:
        """
        Call GET /markets to get all open markets.
        Returns list of raw market dicts from Kalshi.

        Kalshi pagination: use cursor param for next page.
        We fetch up to 200 markets per call (Kalshi max is ~200).

        TODO: implement pagination if needed.
        """
        data = self._get("/markets", params={"limit": 200, "status": "open",
                                              **(params or {})})
        return data.get("markets", [])

    def get_orderbook(self, ticker: str) -> Optional[OrderbookSnapshot]:
        """
        Fetch live orderbook for one market ticker.
        GET /markets/{ticker}/orderbook

        Kalshi orderbook response shape:
        {
          "orderbook": {
            "yes": [{"price": 44, "delta": 150}, ...],
            "no":  [{"price": 56, "delta": 80},  ...]
          }
        }

        Args:
            ticker: Kalshi market ticker e.g. "KXBTCD-25APR30-B76266"

        Returns:
            OrderbookSnapshot with best bid/ask filled in, or None on error.
        """
        if not ticker:
            return None
        try:
            raw = self._get(f"/markets/{ticker}/orderbook")
            if not raw:
                return None
            return normalize_orderbook(raw, ticker)
        except Exception as e:
            self._last_err = f"orderbook {ticker}: {e}"
            print(f"[kalshi orderbook] {ticker}: {e}")
            return None

    def normalize_market(self, raw: dict) -> Optional[MarketSnapshot]:
        """
        Convert one Kalshi API market dict to a MarketSnapshot.
        Returns None if data is incomplete.

        Kalshi market fields (from API docs):
          ticker, title, category, yes_bid, yes_ask, no_bid, no_ask,
          last_price, volume, open_interest, close_time, status,
          result, can_close_early, expiration_value

        TODO: verify exact field names against live API response.
        """
        try:
            ticker = raw.get("ticker", "")
            if not ticker:
                return None

            # Map Kalshi category to our internal categories
            cat_map = {
                "crypto":      "Crypto",
                "economics":   "Economics",
                "politics":    "Politics",
                "sports":      "Soccer",
                "weather":     "Economics",
            }
            raw_cat = str(raw.get("category", "other")).lower()
            category = cat_map.get(raw_cat, raw_cat.title())

            # Kalshi prices come in cents (integers 0-100)
            yes_bid = self._safe_float(raw.get("yes_bid", 0))
            yes_ask = self._safe_float(raw.get("yes_ask", 0))
            no_bid  = self._safe_float(raw.get("no_bid",  0))
            no_ask  = self._safe_float(raw.get("no_ask",  0))

            # If one side is missing, derive using complement
            # YES + NO = 100 cents at settlement
            if yes_bid > 0 and no_ask == 0:
                no_ask = round(100.0 - yes_bid, 1)
            if yes_ask > 0 and no_bid == 0:
                no_bid = round(100.0 - yes_ask, 1)
            if no_bid > 0 and yes_ask == 0:
                yes_ask = round(100.0 - no_bid, 1)
            if no_ask > 0 and yes_bid == 0:
                yes_bid = round(100.0 - no_ask, 1)

            # Choose which side to analyze based on better edge opportunity
            # (prefer the side with lower ask = cheaper to buy)
            side = "YES" if yes_ask <= no_ask else "NO"

            return MarketSnapshot(
                source           = "kalshi",
                market_id        = ticker,
                ticker           = ticker,
                title            = raw.get("title", ticker),
                category         = category,
                side             = side,
                yes_bid          = yes_bid,
                yes_ask          = yes_ask,
                no_bid           = no_bid,
                no_ask           = no_ask,
                last_price       = self._safe_float(raw.get("last_price", 0)),
                volume           = self._safe_int(raw.get("volume", 0)),
                open_interest    = self._safe_int(raw.get("open_interest", 0)),
                expiration_time  = raw.get("close_time", "N/A"),
                settlement_source= raw.get("expiration_value", "Kalshi"),
                underlying_price = None,  # TODO: fetch from market rules
                model_fair_price = None,  # scanner engine will estimate
                timestamp        = now_ts(),
                liquidity_score  = "Medium",  # updated after orderbook fetch
                status           = raw.get("status", "open"),
            )
        except Exception as e:
            print(f"[normalize_market] {raw.get('ticker','?')}: {e}")
            return None

    def get_markets(self) -> List[MarketSnapshot]:
        """
        Fetch live markets from Kalshi and enrich with orderbook data.
        Falls back to empty list on any error — caller handles fallback.
        """
        if not self._is_configured():
            self._last_err = "Kalshi API key not configured"
            return []

        try:
            raw_markets = self._fetch_markets()
            if not raw_markets:
                if not self._last_err:
                    self._last_err = "No markets returned from Kalshi"
                return []

            snapshots = []
            for raw in raw_markets:
                snap = self.normalize_market(raw)
                if snap is None:
                    continue

                # Enrich each market with live orderbook
                ob = self.get_orderbook(snap.ticker)
                if ob:
                    snap = enrich_snapshot_from_orderbook(snap, ob)
                    # Estimate entry/exit prices
                    snap.entry_price_est = snap.ask_price
                    snap.exit_price_est  = round(
                        snap.ask_price + (snap.fair_price - snap.ask_price) * 0.6, 1)
                    snap.orderbook_depth = ob.total_yes_qty + ob.total_no_qty

                snapshots.append(snap)

            return snapshots

        except Exception as e:
            self._last_err = str(e)
            print(f"[kalshi get_markets] {e}")
            return []

    def last_error(self) -> str:
        return self._last_err


# ── Placeholder connectors ─────────────────────────────────────────────────

class OddsAPIConnector(BaseMarketConnector):
    """TODO: Connect to The Odds API. Requires ODDS_API_KEY in .env."""
    name = "odds_api"

    def get_markets(self) -> List[MarketSnapshot]:
        return []


class SoccerModelConnector(BaseMarketConnector):
    """Uses local soccer engine fair prices as market snapshots."""
    name = "soccer_model"

    def get_markets(self) -> List[MarketSnapshot]:
        return []


# ── Data layer ─────────────────────────────────────────────────────────────

class DataLayer:
    """
    Single entry point for the scanner UI.
    Routes to the right connector based on DATA_MODE.
    Handles fallback and error logging.
    """

    def __init__(self, log_fn=None):
        self._log      = log_fn or print
        self._mock     = MockMarketConnector()
        self._kalshi   = KalshiMarketConnector()
        self._last_update = "Never"
        self._last_source = "—"
        self._last_count  = 0
        self._last_error  = ""

    def fetch(self, category_filter: str = "All") -> tuple:
        """
        Fetch markets based on current DATA_MODE.
        Returns (list[dict], source_label, error_str)
        dict format is what market_scanner_engine.run_scanner() expects.
        """
        from scanner_config import effective_mode
        mode  = effective_mode()
        self._log(f"Data mode: {mode}")

        snapshots: List[MarketSnapshot] = []
        source = mode
        error  = ""

        try:
            if mode == "MOCK":
                snapshots = self._mock.get_markets()
                source    = "MOCK"

            elif mode == "KALSHI_LIVE":
                self._log("Kalshi live data requested")
                snapshots = self._kalshi.get_markets()
                if not snapshots:
                    error = self._kalshi.last_error()
                    self._log(f"Live data failed: {error}")
                    self._log("Falling back safely to mock data")
                    snapshots = self._mock.get_markets()
                    source = "MOCK (fallback)"
                else:
                    source = "KALSHI_LIVE"

            elif mode == "HYBRID":
                self._log("Hybrid mode: live + mock")
                live = self._kalshi.get_markets()
                if live:
                    # Tag live snapshots clearly
                    snapshots = live
                    source = "HYBRID"
                else:
                    error = self._kalshi.last_error()
                    self._log(f"Live unavailable: {error} — using mock rows")
                    snapshots = self._mock.get_markets()
                    source = "MOCK (hybrid fallback)"

        except Exception as e:
            error = str(e)
            self._log(f"Fetch error: {e} — using mock data")
            try:
                snapshots = self._mock.get_markets()
                source = "MOCK (error fallback)"
            except Exception:
                snapshots = []

        # Category filter
        if category_filter and category_filter != "All":
            snapshots = [s for s in snapshots
                         if s.category == category_filter]

        # Convert to engine dicts
        dicts = [s.to_connector_dict() for s in snapshots]

        self._last_update = datetime.now().strftime("%H:%M:%S")
        self._last_source = source
        self._last_count  = len(dicts)
        self._last_error  = error

        self._log(f"Loaded {len(dicts)} markets from {source}")
        return dicts, source, error

    def get_orderbook(self, ticker: str,
                       source: str = "mock") -> Optional[OrderbookSnapshot]:
        """
        Fetch orderbook for a single ticker.
        Routes to correct connector based on active source.
        Safe — returns None on any error.
        """
        try:
            if source == "KALSHI_LIVE":
                ob = self._kalshi.get_orderbook(ticker)
                if ob:
                    return ob
            # Fallback to mock orderbook
            return self._mock.get_orderbook(ticker)
        except Exception as e:
            self._log(f"Orderbook error {ticker}: {e}")
            return None

    def status(self) -> dict:
        from scanner_config import status_report
        rep = status_report()
        rep["last_update"] = self._last_update
        rep["last_source"] = self._last_source
        rep["last_count"]  = self._last_count
        rep["last_error"]  = self._last_error
        return rep


# ── Legacy shim ────────────────────────────────────────────────────────────

def get_connector(market_type: str) -> BaseMarketConnector:
    """Legacy function kept for backward compatibility."""
    return MockMarketConnector()
