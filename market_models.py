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
        # Kalshi orderbook prices are integer cents (0-100).
        # We store as dollar floats (0.0-1.0) to match MarketSnapshot.
        for lvl in ob.get("yes", []):
            raw_price = lvl.get("price", 0)
            qty       = int(lvl.get("delta", lvl.get("quantity", 0)))
            price = parse_kalshi_price(raw_price)
            if price is not None and price > 0 and qty > 0:
                snap.yes_bids.append(OrderbookLevel(price=price, quantity=qty))

        # ── Parse NO bids from API ──────────────────────────────────────
        for lvl in ob.get("no", []):
            raw_price = lvl.get("price", 0)
            qty       = int(lvl.get("delta", lvl.get("quantity", 0)))
            price = parse_kalshi_price(raw_price)
            if price is not None and price > 0 and qty > 0:
                snap.no_bids.append(OrderbookLevel(price=price, quantity=qty))

        # ── Derive asks using the 1.0 complement ─────────────────────
        #
        # Since YES + NO = $1.00 at settlement (dollar representation):
        #   YES ask = 1.0 - NO best bid
        #   NO ask  = 1.0 - YES best bid
        #
        # Example: YES best bid = 0.44 → NO ask = 1.0 - 0.44 = 0.56
        #          NO best bid  = 0.56 → YES ask = 1.0 - 0.56 = 0.44
        #
        for lvl in snap.no_bids:
            derived_yes_ask = round(1.0 - lvl.price, 6)
            snap.yes_asks.append(OrderbookLevel(
                price=derived_yes_ask, quantity=lvl.quantity))

        for lvl in snap.yes_bids:
            derived_no_ask = round(1.0 - lvl.price, 6)
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

    # ── Cross-derive any missing prices (dollar complement: YES + NO = 1.0) ──
    if snap.yes_best_ask is None and snap.no_best_bid is not None:
        snap.yes_best_ask = round(1.0 - snap.no_best_bid, 6)
    if snap.no_best_ask is None and snap.yes_best_bid is not None:
        snap.no_best_ask = round(1.0 - snap.yes_best_bid, 6)
    if snap.yes_best_bid is None and snap.no_best_ask is not None:
        snap.yes_best_bid = round(1.0 - snap.no_best_ask, 6)
    if snap.no_best_bid is None and snap.yes_best_ask is not None:
        snap.no_best_bid = round(1.0 - snap.yes_best_ask, 6)

    # ── Spreads (in dollars; 0.01 = 1 cent) ────────────────────────────
    if snap.yes_best_bid is not None and snap.yes_best_ask is not None:
        snap.yes_spread = round(snap.yes_best_ask - snap.yes_best_bid, 6)
    if snap.no_best_bid is not None and snap.no_best_ask is not None:
        snap.no_spread = round(snap.no_best_ask - snap.no_best_bid, 6)

    # ── Total quantity and liquidity score ──────────────────────────────
    snap.total_yes_qty = sum(l.quantity for l in snap.yes_bids + snap.yes_asks)
    snap.total_no_qty  = sum(l.quantity for l in snap.no_bids  + snap.no_asks)
    total_qty = snap.total_yes_qty + snap.total_no_qty

    avg_spread = None
    spreads = [s for s in [snap.yes_spread, snap.no_spread] if s is not None]
    if spreads:
        avg_spread = sum(spreads) / len(spreads)

    # Thresholds in dollars: 0.02 = 2 cents, 0.04 = 4 cents
    if total_qty >= 500 and avg_spread is not None and avg_spread <= 0.02:
        snap.liquidity = "High"
    elif total_qty >= 100 or (avg_spread is not None and avg_spread <= 0.04):
        snap.liquidity = "Medium"
    else:
        snap.liquidity = "Low"

    return snap


def enrich_snapshot_from_orderbook(
    snap: 'MarketSnapshot',
    ob:   OrderbookSnapshot,
) -> 'MarketSnapshot':
    """
    Enrich a MarketSnapshot with orderbook prices — but never erase
    valid market-level prices that already exist.

    Priority:
      1. Orderbook best bid/ask (most current, from live depth)
      2. Market-level *_dollars fields (already on snap from normalize_market)
      3. None / N/A if neither source has the price

    Kalshi orderbook returns only bids for each side.
    Asks are inferred using the 1.00 complement:
      YES ask = 1.0 - NO best bid    (if no_bid exists)
      NO ask  = 1.0 - YES best bid   (if yes_bid exists)

    Args:
        snap: MarketSnapshot that may already have prices from *_dollars fields
        ob:   OrderbookSnapshot from GET /markets/{ticker}/orderbook
    """
    if ob is None:
        return snap

    # ── Orderbook best bids (direct from API) ──────────────────────────
    # Only overwrite if orderbook has a real value — never set to None
    if ob.yes_best_bid is not None:
        snap.yes_bid = ob.yes_best_bid    # dollars (0.0–1.0)
    if ob.no_best_bid is not None:
        snap.no_bid = ob.no_best_bid

    # ── Orderbook asks (inferred from opposite side bids) ──────────────
    # Kalshi orderbook only returns bids; asks come from the complement rule.
    # Only fill if orderbook provides the data; fallback keeps existing value.
    if ob.yes_best_ask is not None:
        snap.yes_ask = ob.yes_best_ask
    elif ob.no_best_bid is not None and snap.yes_ask is None:
        # Infer YES ask from NO bid: YES_ask = 1.0 - NO_bid
        snap.yes_ask = round(1.0 - ob.no_best_bid, 6)

    if ob.no_best_ask is not None:
        snap.no_ask = ob.no_best_ask
    elif ob.yes_best_bid is not None and snap.no_ask is None:
        # Infer NO ask from YES bid: NO_ask = 1.0 - YES_bid
        snap.no_ask = round(1.0 - ob.yes_best_bid, 6)

    # ── Complement rule on what we now have ────────────────────────────
    # Fill any remaining gaps using whatever prices we have
    if snap.yes_bid is not None and snap.no_ask is None:
        snap.no_ask = round(1.0 - snap.yes_bid, 6)
    if snap.yes_ask is not None and snap.no_bid is None:
        snap.no_bid = round(1.0 - snap.yes_ask, 6)
    if snap.no_bid is not None and snap.yes_ask is None:
        snap.yes_ask = round(1.0 - snap.no_bid, 6)
    if snap.no_ask is not None and snap.yes_bid is None:
        snap.yes_bid = round(1.0 - snap.no_ask, 6)

    # ── Pick better side ───────────────────────────────────────────────
    ya, na = snap.yes_ask, snap.no_ask
    if ya is not None and na is not None:
        snap.side = "YES" if ya <= na else "NO"
    elif ya is not None:
        snap.side = "YES"
    elif na is not None:
        snap.side = "NO"

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
    yes_bid:            Optional[float]  # best bid on YES side (cents); None = not available
    yes_ask:            Optional[float]  # best ask on YES side (cents); None = not available
    no_bid:             Optional[float]  # best bid on NO side (cents); None = not available
    no_ask:             Optional[float]  # best ask on NO side (cents); None = not available
    last_price:         Optional[float]  # most recent trade price (cents); None = no trades
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

    # Raw API response — stored for debugging, never logged publicly
    raw_data:           Optional[dict]  = None   # original API dict if available

    # ── Derived properties ─────────────────────────────────────────────────

    @property
    def bid_price(self) -> Optional[float]:
        """Best bid for the selected side. None = not yet loaded."""
        return self.yes_bid if self.side == "YES" else self.no_bid

    @property
    def ask_price(self) -> Optional[float]:
        """Best ask for the selected side. None = not yet loaded."""
        return self.yes_ask if self.side == "YES" else self.no_ask

    @property
    def spread(self) -> Optional[float]:
        """Bid-ask spread. None if either price is missing."""
        b, a = self.bid_price, self.ask_price
        if b is None or a is None:
            return None
        return round(a - b, 1)

    @property
    def fair_price(self) -> Optional[float]:
        """
        Model fair price.
        Returns model estimate if set.
        Falls back to midpoint only if both bid AND ask are available.
        Returns None if no price information exists.
        """
        if self.model_fair_price is not None:
            return self.model_fair_price
        b, a = self.bid_price, self.ask_price
        if b is not None and a is not None and a > 0:
            return round((b + a) / 2, 1)
        return None

    def to_connector_dict(self) -> dict:
        """
        Convert to the dict format expected by market_scanner_engine.
        None values are passed through — the engine handles missing prices safely.

        IMPORTANT: model_fair_price is always the explicit model estimate,
        never the midpoint fallback. If no model has priced this market,
        model_fair_price = None → engine signals DATA NEEDED.
        This prevents the engine from treating a midpoint as a real fair value.
        """
        return {
            "market_id":        self.market_id,
            "market_name":      self.title,
            "category":         self.category,
            "side":             self.side,
            "bid_price":        self.bid_price,          # None = not loaded
            "ask_price":        self.ask_price,          # None = not loaded
            "last_price":       self.last_price,         # None = no trades
            "model_fair_price": self.model_fair_price,   # None = DATA NEEDED
            "volume":           self.volume,
            "liquidity":        self.liquidity_score,
        }


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_kalshi_price(value, field_name: str = "") -> Optional[float]:
    """
    Convert a raw Kalshi price field to an internal dollar float (0.0 – 1.0).
    Returns None for missing/invalid — never returns 0 for missing data.

    Decision logic (exactly one multiply-by-100 ever happens here):
      field_name ends with "_dollars":
        "0.5000" → 0.50  (parse string as dollars, no division needed)
        "1.0000" → 1.00
      value is None or "" → None
      value is float 0.0–1.0 → keep as-is (already dollars)
      value is int/float 1.0–100 → divide by 100 (legacy cents → dollars)
      anything else → None (log warning, safe failure)
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() in ("n/a", "null", "none"):
            return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None

    if v == 0.0:
        return 0.0                      # explicit zero (e.g. unsettled market)
    elif 0.0 < v <= 1.0:
        return round(v, 6)              # already dollars — no conversion needed
    elif 1.0 < v <= 100.0:
        return round(v / 100.0, 6)      # legacy cents int → dollars
    else:
        return None                      # out of range for binary market


def format_price(value) -> str:
    """
    Format an internal DOLLAR price (0.0–1.0) for display.
    Multiplies by 100 exactly once.

      0.50  → "50c"
      1.00  → "100c"
      0.00  → "0c"    (explicit zero, different from None)
      None  → "N/A"
      50.0  → WARNING: this is cents not dollars — returns "N/A" with guard

    Do NOT call this on MarketSignal.bid_price/ask_price (those are cents).
    Use format_cents() for MarketSignal values.
    """
    if value is None:
        return "N/A"
    if isinstance(value, str) and value.strip() == "":
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"
    # Safety guard: internal dollar prices must be 0.0–1.0
    # Values > 1.0 are cents accidentally passed here — reject them
    if v > 1.0:
        return "N/A"   # caller bug: passed cents instead of dollars
    cents = v * 100.0
    return f"{int(cents + 0.5)}c"


def format_cents(value) -> str:
    """
    Format a CENTS value (0–100) for display.
    Used for MarketSignal.bid_price, ask_price, spread, edge, breakeven etc.

      56.0  → "56c"
      9.0   → "9c"
      0.0   → "0c"
      None  → "N/A"
    """
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"
    return f"{v:.0f}c"





def sanity_check_price(value, label: str = "") -> Optional[float]:
    """Validate that an internal price is in dollar range (0.0-1.0). Log if not."""
    if value is None:
        return None
    if value > 1.0:
        print(f"[sanity] WARNING: {label} = {value:.4f} is > 1.0 (should be dollars). "
              f"Setting to None.")
        return None
    return value


def debug_market_fields(raw: dict, label: str = "market") -> None:
    """
    Log price-related fields from a raw Kalshi API market dict.
    Safe: never prints API key or private key content.
    Only prints field names and their values/types.
    """
    price_keywords = {"bid","ask","price","last","yes","no","cent","dollar","fee","volume"}
    print(f"\n[debug] Raw {label}: {raw.get('ticker','?')} price fields below")
    for k, v in sorted(raw.items()):
        # Include all price-related fields
        if any(kw in k.lower() for kw in price_keywords):
            print(f"  {k:40s} = {repr(v)[:80]}")
    print()
