"""
market_models.py
Normalized data models for the AI Market Scanner.
All connectors produce MarketSnapshot objects.
The UI only reads MarketSnapshot — does not care about data source.

Kalshi binary market price relationships:
  YES + NO always sum to $1 (100 cents) at settlement.
  Therefore:
    NO bid  = 100 - YES ask   (best price to buy NO = 100 - best price to sell YES)
    NO ask  = 100 - YES bid   (best price to sell NO = 100 - best price to buy YES)
    YES bid = 100 - NO ask
    YES ask = 100 - NO bid
  This means we can always derive one side from the other.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


# ── Orderbook structures ───────────────────────────────────────────────────

@dataclass
class OrderbookLevel:
    """A single price level in an orderbook (one row of bids or asks)."""
    price:    float   # cents (0-100)
    quantity: int     # number of contracts available at this price


@dataclass
class OrderbookSnapshot:
    """
    Full orderbook for one Kalshi market ticker.
    Kalshi returns YES side bids and asks.
    NO side is derived using the reciprocal relationship.
    """
    ticker:    str
    timestamp: str

    # YES side — direct from API
    yes_bids: List[OrderbookLevel] = field(default_factory=list)
    yes_asks: List[OrderbookLevel] = field(default_factory=list)

    # NO side — derived or direct from API
    no_bids:  List[OrderbookLevel] = field(default_factory=list)
    no_asks:  List[OrderbookLevel] = field(default_factory=list)

    # Best prices (populated by calculate_best_bid_ask)
    yes_best_bid: Optional[float] = None   # highest YES bid
    yes_best_ask: Optional[float] = None   # lowest YES ask
    no_best_bid:  Optional[float] = None   # highest NO bid
    no_best_ask:  Optional[float] = None   # lowest NO ask

    # Computed fields
    yes_spread:    Optional[float] = None
    no_spread:     Optional[float] = None
    liquidity:     str = "Low"             # "High" | "Medium" | "Low"
    total_yes_qty: int = 0
    total_no_qty:  int = 0


def normalize_orderbook(raw: dict, ticker: str) -> Optional[OrderbookSnapshot]:
    """
    Convert a raw Kalshi orderbook API response to OrderbookSnapshot.

    Kalshi API response shape (approximate):
    {
      "orderbook": {
        "yes": [
          {"price": 44, "delta": 150},   # bids — people willing to buy YES at 44c
          ...
        ],
        "no": [
          {"price": 57, "delta": 80},    # bids — people willing to buy NO at 57c
          ...
        ]
      }
    }

    Note: Kalshi returns bids for each side. The "asks" are the bids of
    the opposite side converted via the 100-cent complement.

    Args:
        raw:    Raw API dict (or mock dict with same structure)
        ticker: Market ticker string

    Returns:
        OrderbookSnapshot, or None if input is empty/invalid
    """
    if not raw:
        return None

    try:
        ob    = raw.get("orderbook", raw)   # handle both wrapped and unwrapped
        ts    = now_ts()
        snap  = OrderbookSnapshot(ticker=ticker, timestamp=ts)

        # ── Parse YES bids from API ─────────────────────────────────────
        # These are buy orders on the YES side
        for lvl in ob.get("yes", []):
            price = float(lvl.get("price", 0))
            qty   = int(lvl.get("delta", lvl.get("quantity", 0)))
            if price > 0 and qty > 0:
                snap.yes_bids.append(OrderbookLevel(price=price, quantity=qty))

        # ── Parse NO bids from API ──────────────────────────────────────
        # These are buy orders on the NO side
        for lvl in ob.get("no", []):
            price = float(lvl.get("price", 0))
            qty   = int(lvl.get("delta", lvl.get("quantity", 0)))
            if price > 0 and qty > 0:
                snap.no_bids.append(OrderbookLevel(price=price, quantity=qty))

        # ── Derive asks using the 100-cent complement ───────────────────
        #
        # Since YES + NO = 100 cents at settlement:
        #   YES ask = 100 - NO best bid
        #   NO ask  = 100 - YES best bid
        #
        # Example: YES best bid = 44c → NO ask = 100 - 44 = 56c
        #          NO best bid  = 56c → YES ask = 100 - 56 = 44c
        #
        # We derive the ask levels by inverting the opposite side's bids.
        for lvl in snap.no_bids:
            derived_yes_ask = round(100.0 - lvl.price, 1)
            snap.yes_asks.append(OrderbookLevel(
                price=derived_yes_ask, quantity=lvl.quantity))

        for lvl in snap.yes_bids:
            derived_no_ask = round(100.0 - lvl.price, 1)
            snap.no_asks.append(OrderbookLevel(
                price=derived_no_ask, quantity=lvl.quantity))

        # Sort: bids descending (best bid = highest price first)
        #       asks ascending  (best ask = lowest price first)
        snap.yes_bids.sort(key=lambda x: x.price, reverse=True)
        snap.no_bids.sort( key=lambda x: x.price, reverse=True)
        snap.yes_asks.sort(key=lambda x: x.price)
        snap.no_asks.sort( key=lambda x: x.price)

        # ── Calculate best prices ───────────────────────────────────────
        return calculate_best_bid_ask(snap)

    except Exception as e:
        print(f"[normalize_orderbook] {ticker}: {e}")
        return None


def calculate_best_bid_ask(snap: OrderbookSnapshot) -> OrderbookSnapshot:
    """
    Fill in best bid/ask prices and derived fields on an OrderbookSnapshot.
    Also calculates spread and liquidity score.

    Args:
        snap: OrderbookSnapshot with bids/asks lists populated

    Returns:
        Same snapshot with best prices, spreads, liquidity filled in.
    """
    # Best YES bid = highest price someone will pay for YES
    if snap.yes_bids:
        snap.yes_best_bid = snap.yes_bids[0].price

    # Best YES ask = lowest price someone will sell YES for
    if snap.yes_asks:
        snap.yes_best_ask = snap.yes_asks[0].price

    # Best NO bid = highest price someone will pay for NO
    if snap.no_bids:
        snap.no_best_bid = snap.no_bids[0].price

    # Best NO ask = lowest price someone will sell NO for
    if snap.no_asks:
        snap.no_best_ask = snap.no_asks[0].price

    # ── Cross-derive any missing prices ────────────────────────────────
    # If YES ask is still missing, derive from NO bid
    if snap.yes_best_ask is None and snap.no_best_bid is not None:
        snap.yes_best_ask = round(100.0 - snap.no_best_bid, 1)

    # If NO ask is still missing, derive from YES bid
    if snap.no_best_ask is None and snap.yes_best_bid is not None:
        snap.no_best_ask = round(100.0 - snap.yes_best_bid, 1)

    # If YES bid missing, derive from NO ask
    if snap.yes_best_bid is None and snap.no_best_ask is not None:
        snap.yes_best_bid = round(100.0 - snap.no_best_ask, 1)

    # If NO bid missing, derive from YES ask
    if snap.no_best_bid is None and snap.yes_best_ask is not None:
        snap.no_best_bid = round(100.0 - snap.yes_best_ask, 1)

    # ── Spreads ─────────────────────────────────────────────────────────
    if snap.yes_best_bid is not None and snap.yes_best_ask is not None:
        snap.yes_spread = round(snap.yes_best_ask - snap.yes_best_bid, 1)

    if snap.no_best_bid is not None and snap.no_best_ask is not None:
        snap.no_spread = round(snap.no_best_ask - snap.no_best_bid, 1)

    # ── Total quantity (liquidity proxy) ────────────────────────────────
    snap.total_yes_qty = sum(l.quantity for l in snap.yes_bids + snap.yes_asks)
    snap.total_no_qty  = sum(l.quantity for l in snap.no_bids  + snap.no_asks)
    total_qty = snap.total_yes_qty + snap.total_no_qty

    # ── Liquidity score ─────────────────────────────────────────────────
    # Based on total quantity available across all levels.
    # Thresholds are approximate — tune with real data.
    avg_spread = None
    spreads = [s for s in [snap.yes_spread, snap.no_spread] if s is not None]
    if spreads:
        avg_spread = sum(spreads) / len(spreads)

    if total_qty >= 500 and avg_spread is not None and avg_spread <= 2:
        snap.liquidity = "High"
    elif total_qty >= 100 or (avg_spread is not None and avg_spread <= 4):
        snap.liquidity = "Medium"
    else:
        snap.liquidity = "Low"

    return snap


def enrich_snapshot_from_orderbook(
    snap: 'MarketSnapshot',
    ob:   OrderbookSnapshot,
) -> 'MarketSnapshot':
    """
    Update a MarketSnapshot with live orderbook prices.
    Only overwrites prices if the orderbook has valid data.

    Args:
        snap: Existing MarketSnapshot (may have stale/mock prices)
        ob:   Fresh OrderbookSnapshot from API

    Returns:
        Updated MarketSnapshot with live bid/ask/spread/liquidity.
    """
    if ob is None:
        return snap

    # Update YES side
    if ob.yes_best_bid is not None:
        snap.yes_bid = ob.yes_best_bid
    if ob.yes_best_ask is not None:
        snap.yes_ask = ob.yes_best_ask

    # Update NO side
    if ob.no_best_bid is not None:
        snap.no_bid = ob.no_best_bid
    if ob.no_best_ask is not None:
        snap.no_ask = ob.no_best_ask

    # Update liquidity from orderbook depth
    snap.liquidity_score = ob.liquidity

    return snap


# ── Market snapshot ────────────────────────────────────────────────────────

@dataclass
class MarketSnapshot:
    """
    One normalized market record.
    Produced by any connector (mock, Kalshi, sportsbook, etc.)
    All prices in cents (0-100).
    """
    source:             str
    market_id:          str
    ticker:             str
    title:              str
    category:           str
    side:               str            # "YES" | "NO" — which side we're analyzing
    yes_bid:            float          # best bid on YES side (cents)
    yes_ask:            float          # best ask on YES side (cents)
    no_bid:             float          # best bid on NO side (cents)
    no_ask:             float          # best ask on NO side (cents)
    last_price:         float          # most recent trade price (cents)
    volume:             int
    open_interest:      int
    expiration_time:    str
    settlement_source:  str
    underlying_price:   Optional[float]
    model_fair_price:   Optional[float]
    timestamp:          str
    liquidity_score:    str            # "High" | "Medium" | "Low"
    status:             str            # "open" | "closed" | "settled"

    # Orderbook-derived fields (None = not yet fetched)
    orderbook_depth:    Optional[int]   = None   # total qty across top levels
    entry_price_est:    Optional[float] = None   # estimated fill price to enter
    exit_price_est:     Optional[float] = None   # estimated fill price to exit

    # ── Derived properties ─────────────────────────────────────────────────

    @property
    def bid_price(self) -> float:
        """Best bid for the selected side."""
        return self.yes_bid if self.side == "YES" else self.no_bid

    @property
    def ask_price(self) -> float:
        """Best ask for the selected side."""
        return self.yes_ask if self.side == "YES" else self.no_ask

    @property
    def spread(self) -> float:
        """Bid-ask spread for the selected side."""
        return round(self.ask_price - self.bid_price, 1)

    @property
    def fair_price(self) -> float:
        """Model fair price — falls back to midpoint if not set."""
        if self.model_fair_price is not None:
            return self.model_fair_price
        return round((self.bid_price + self.ask_price) / 2, 1)

    def to_connector_dict(self) -> dict:
        """
        Convert to the dict format expected by market_scanner_engine.
        Keeps backward compatibility with existing engine.
        """
        return {
            "market_id":        self.market_id,
            "market_name":      self.title,
            "category":         self.category,
            "side":             self.side,
            "bid_price":        self.bid_price,
            "ask_price":        self.ask_price,
            "last_price":       self.last_price,
            "model_fair_price": self.fair_price,
            "volume":           self.volume,
            "liquidity":        self.liquidity_score,
        }


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
