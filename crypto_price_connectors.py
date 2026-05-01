"""
crypto_price_connectors.py
Read-only crypto reference price connectors.

No trading. No order execution. No account access.
Used only to fetch spot prices for Kalshi market context.

Connector hierarchy:
  BaseCryptoPriceConnector
  MockCryptoPriceConnector      — always works, no internet needed
  CoinGeckoPriceConnector       — public API, no key required
  BinancePriceConnector         — public ticker endpoint, no key required
  CoinbasePriceConnector        — public product ticker, no key required
  CryptoPriceDataLayer          — auto-selects, falls back gracefully
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import time


# ── Snapshot dataclass ─────────────────────────────────────────────────────

@dataclass
class CryptoPriceSnapshot:
    """
    Normalized crypto spot price snapshot.
    All prices in USD. None = unavailable.
    """
    source:    str
    symbol:    str              # "BTC" | "ETH"
    price:     Optional[float]  # USD spot price
    bid:       Optional[float]  # best bid if available
    ask:       Optional[float]  # best ask if available
    timestamp: str
    status:    str              # "ok" | "error" | "mock"
    raw_data:  Optional[dict]   = field(default=None)

    @property
    def price_str(self) -> str:
        if self.price is None:
            return "N/A"
        return f"${self.price:,.2f}"

    @property
    def age_seconds(self) -> float:
        try:
            ts = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - ts).total_seconds()
        except Exception:
            return 9999.0


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── Base connector ─────────────────────────────────────────────────────────

class BaseCryptoPriceConnector:
    name = "base"
    symbols = ["BTC", "ETH"]

    def fetch(self, symbol: str = "BTC") -> CryptoPriceSnapshot:
        raise NotImplementedError

    def fetch_all(self) -> dict:
        """Return {symbol: CryptoPriceSnapshot} for all symbols."""
        return {s: self.fetch(s) for s in self.symbols}

    def _error(self, symbol: str, reason: str) -> CryptoPriceSnapshot:
        return CryptoPriceSnapshot(
            source=self.name, symbol=symbol, price=None,
            bid=None, ask=None, timestamp=_now(),
            status=f"error: {reason[:60]}")


# ── Mock connector (always works) ─────────────────────────────────────────

# Realistic mock prices — updated by drift each call to simulate movement
_MOCK_PRICES = {"BTC": 76266.0, "ETH": 3087.0}
_MOCK_DRIFT  = {"BTC": 0.0,     "ETH": 0.0}

class MockCryptoPriceConnector(BaseCryptoPriceConnector):
    """
    Always-available mock connector.
    Applies small random drift to simulate live prices.
    """
    name = "mock"

    def fetch(self, symbol: str = "BTC") -> CryptoPriceSnapshot:
        import random
        sym = symbol.upper()
        base = _MOCK_PRICES.get(sym, 1000.0)
        # Small drift: ±0.05% each call
        drift = base * random.uniform(-0.0005, 0.0005)
        _MOCK_DRIFT[sym] = _MOCK_DRIFT.get(sym, 0.0) + drift
        price = base + _MOCK_DRIFT[sym]
        spread = price * 0.0001  # 0.01% spread
        return CryptoPriceSnapshot(
            source="mock", symbol=sym, price=round(price, 2),
            bid=round(price - spread, 2), ask=round(price + spread, 2),
            timestamp=_now(), status="mock")


# ── CoinGecko connector (public, no key) ─────────────────────────────────

class CoinGeckoPriceConnector(BaseCryptoPriceConnector):
    """
    Fetches BTC/ETH prices from CoinGecko public API.
    No API key required for basic price data.
    Rate limit: ~30 calls/min on free tier.
    """
    name = "coingecko"
    BASE = "https://api.coingecko.com/api/v3"

    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
    }

    def fetch(self, symbol: str = "BTC") -> CryptoPriceSnapshot:
        sym = symbol.upper()
        coin_id = self.SYMBOL_MAP.get(sym)
        if not coin_id:
            return self._error(sym, f"Unknown symbol: {sym}")
        try:
            import requests
            url = f"{self.BASE}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            }
            resp = requests.get(url, params=params, timeout=5,
                                headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                info = data.get(coin_id, {})
                price = info.get("usd")
                if price is None:
                    return self._error(sym, "No price in response")
                return CryptoPriceSnapshot(
                    source="coingecko", symbol=sym,
                    price=float(price), bid=None, ask=None,
                    timestamp=_now(), status="ok", raw_data=info)
            elif resp.status_code == 429:
                return self._error(sym, "CoinGecko rate limit hit")
            else:
                return self._error(sym, f"HTTP {resp.status_code}")
        except ImportError:
            return self._error(sym, "requests not installed")
        except Exception as e:
            return self._error(sym, str(e)[:80])


# ── Binance connector (public ticker, no key) ────────────────────────────

class BinancePriceConnector(BaseCryptoPriceConnector):
    """
    Fetches BTCUSDT/ETHUSDT prices from Binance public REST API.
    No API key required. Read-only price data only.
    Endpoint: GET /api/v3/ticker/bookTicker
    """
    name = "binance"
    BASE = "https://api.binance.com/api/v3"

    SYMBOL_MAP = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
    }

    def fetch(self, symbol: str = "BTC") -> CryptoPriceSnapshot:
        sym = symbol.upper()
        pair = self.SYMBOL_MAP.get(sym)
        if not pair:
            return self._error(sym, f"Unknown symbol: {sym}")
        try:
            import requests
            # bookTicker gives best bid/ask in real-time
            resp = requests.get(
                f"{self.BASE}/ticker/bookTicker",
                params={"symbol": pair},
                timeout=5, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data = resp.json()
                bid = float(data.get("bidPrice", 0))
                ask = float(data.get("askPrice", 0))
                mid = round((bid + ask) / 2, 2) if bid and ask else None
                return CryptoPriceSnapshot(
                    source="binance", symbol=sym,
                    price=mid, bid=bid if bid else None, ask=ask if ask else None,
                    timestamp=_now(), status="ok", raw_data=data)
            elif resp.status_code == 451:
                return self._error(sym, "Binance not available in your region")
            else:
                return self._error(sym, f"HTTP {resp.status_code}")
        except ImportError:
            return self._error(sym, "requests not installed")
        except Exception as e:
            return self._error(sym, str(e)[:80])


# ── Coinbase connector (public product ticker, no key) ───────────────────

class CoinbasePriceConnector(BaseCryptoPriceConnector):
    """
    Fetches BTC/ETH prices from Coinbase Advanced Trade public API.
    No API key required for public market data.
    Endpoint: GET /api/v3/brokerage/best_bid_ask
    Fallback: GET /products/{product_id}/ticker (legacy)
    """
    name = "coinbase"
    BASE_ADV  = "https://api.coinbase.com/api/v3/brokerage"
    BASE_LEGACY = "https://api.exchange.coinbase.com"

    SYMBOL_MAP = {
        "BTC": "BTC-USD",
        "ETH": "ETH-USD",
    }

    def fetch(self, symbol: str = "BTC") -> CryptoPriceSnapshot:
        sym = symbol.upper()
        product = self.SYMBOL_MAP.get(sym)
        if not product:
            return self._error(sym, f"Unknown symbol: {sym}")
        try:
            import requests
            # Legacy endpoint — no auth required
            resp = requests.get(
                f"{self.BASE_LEGACY}/products/{product}/ticker",
                timeout=5, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                data  = resp.json()
                price = float(data.get("price", 0)) or None
                bid   = float(data.get("bid", 0)) or None
                ask   = float(data.get("ask", 0)) or None
                return CryptoPriceSnapshot(
                    source="coinbase", symbol=sym,
                    price=price, bid=bid, ask=ask,
                    timestamp=_now(), status="ok", raw_data=data)
            else:
                return self._error(sym, f"HTTP {resp.status_code}")
        except ImportError:
            return self._error(sym, "requests not installed")
        except Exception as e:
            return self._error(sym, str(e)[:80])


# ── Auto data layer ───────────────────────────────────────────────────────

CONNECTOR_ORDER = [
    ("coingecko", CoinGeckoPriceConnector),
    ("binance",   BinancePriceConnector),
    ("coinbase",  CoinbasePriceConnector),
    ("mock",      MockCryptoPriceConnector),
]

class CryptoPriceDataLayer:
    """
    Auto-selects the best available crypto price source.
    Falls back gracefully through the connector list.
    Never crashes — always returns a CryptoPriceSnapshot.
    """

    def __init__(self, preferred: str = "auto", log_fn=None):
        self._preferred = preferred.lower()
        self._log       = log_fn or print
        self._cache:   dict = {}      # {symbol: CryptoPriceSnapshot}
        self._cache_ts: dict = {}     # {symbol: float timestamp}
        self._cache_ttl = 15.0        # seconds before re-fetch
        self._last_source = "—"
        self._conn_status: dict = {}  # connector name → "ok" | "error" | "not tested"

        self._connectors = dict(CONNECTOR_ORDER)
        self._mock = MockCryptoPriceConnector()

    def fetch(self, symbol: str = "BTC") -> CryptoPriceSnapshot:
        """
        Fetch price for symbol. Uses cache if fresh.
        Tries preferred source first; falls back to others.
        Always returns a snapshot (mock if all else fails).
        """
        sym = symbol.upper()
        # Return cached if still fresh
        if sym in self._cache:
            age = time.time() - self._cache_ts.get(sym, 0)
            if age < self._cache_ttl:
                return self._cache[sym]

        snap = self._try_fetch(sym)
        self._cache[sym] = snap
        self._cache_ts[sym] = time.time()
        self._last_source = snap.source
        return snap

    def fetch_all(self) -> dict:
        return {s: self.fetch(s) for s in ["BTC", "ETH"]}

    def _try_fetch(self, symbol: str) -> CryptoPriceSnapshot:
        """Try connectors in preferred order, fall back to mock."""
        order = self._build_order()
        for name in order:
            cls = self._connectors.get(name)
            if cls is None:
                continue
            try:
                snap = cls().fetch(symbol)
                if snap.status == "ok" or snap.status == "mock":
                    self._conn_status[name] = "ok"
                    self._log(f"Crypto {symbol}: ${snap.price:,.0f} from {name}")
                    return snap
                else:
                    self._conn_status[name] = f"error: {snap.status}"
            except Exception as e:
                self._conn_status[name] = f"error: {e}"
        # Last resort: mock
        snap = self._mock.fetch(symbol)
        self._log(f"Crypto {symbol}: using mock (all live sources failed)")
        return snap

    def _build_order(self) -> list:
        if self._preferred == "auto":
            return [name for name, _ in CONNECTOR_ORDER]
        if self._preferred in self._connectors:
            others = [n for n in self._connectors if n != self._preferred]
            return [self._preferred] + others
        return [name for name, _ in CONNECTOR_ORDER]

    def set_preferred(self, source: str):
        self._preferred = source.lower()
        self._cache.clear()  # clear cache so next fetch uses new source

    def status(self) -> dict:
        return {
            "last_source": self._last_source,
            "connectors":  dict(self._conn_status),
            "cache_size":  len(self._cache),
        }

    def invalidate_cache(self):
        self._cache.clear()
        self._cache_ts.clear()


# ── Market title parser ───────────────────────────────────────────────────

from dataclasses import dataclass as _dc
import re as _re

@_dc
class CryptoMarketContext:
    """Parsed context from a Kalshi crypto market title."""
    asset:           str            # "BTC" | "ETH" | "UNKNOWN"
    target_price:    Optional[float]
    condition:       str            # "ABOVE" | "BELOW" | "UNKNOWN"
    expiration_text: Optional[str]
    raw_title:       str


def parse_crypto_market_title(title: str) -> CryptoMarketContext:
    """
    Extract crypto context from a Kalshi market title.
    Safe — never crashes. Returns UNKNOWN fields when unparseable.

    Examples it handles:
      "BTC above $76,266 by 7:45 PM"
      "Bitcoin greater than $80,000"
      "ETH above $3,100 by close"
      "Ethereum below $2,500 by Friday"
    """
    if not title:
        return CryptoMarketContext(
            asset="UNKNOWN", target_price=None,
            condition="UNKNOWN", expiration_text=None, raw_title="")

    t = title.strip()

    # Detect asset
    asset = "UNKNOWN"
    if any(x in t.upper() for x in ("BTC", "BITCOIN")):
        asset = "BTC"
    elif any(x in t.upper() for x in ("ETH", "ETHEREUM", "ETHER")):
        asset = "ETH"

    # Detect condition
    condition = "UNKNOWN"
    tl = t.lower()
    if any(x in tl for x in ("above", "greater than", "higher than", "over", "exceed")):
        condition = "ABOVE"
    elif any(x in tl for x in ("below", "less than", "lower than", "under")):
        condition = "BELOW"

    # Extract target price — find dollar amounts like $76,266 or $76266 or $76k
    target_price = None
    # Match $XX,XXX.XX or $XXXXX or $XXk
    price_match = _re.search(
        r'\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)([kKmM]?)',
        t)
    if price_match:
        num_str  = price_match.group(1).replace(",", "")
        suffix   = price_match.group(2).upper()
        try:
            val = float(num_str)
            if suffix == "K":
                val *= 1_000
            elif suffix == "M":
                val *= 1_000_000
            target_price = val
        except ValueError:
            pass

    # Extract expiration text (everything after "by")
    expiration_text = None
    by_match = _re.search(r'\bby\b(.+?)$', t, _re.IGNORECASE)
    if by_match:
        expiration_text = by_match.group(1).strip()

    return CryptoMarketContext(
        asset=asset, target_price=target_price,
        condition=condition, expiration_text=expiration_text,
        raw_title=t)
