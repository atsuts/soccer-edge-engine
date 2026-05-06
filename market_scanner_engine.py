"""
market_scanner_engine.py
Core calculation logic for the AI Market Scanner.

All calculations are for analysis and paper trading only.
No real orders. Auto trading is OFF.

Price convention throughout: ALL prices are in CENTS (0-100).
  e.g. 44c means 44 cents = $0.44 per contract
  A $1 contract settles at either 100c (win) or 0c (loss).
"""

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple
from datetime import datetime


# ── Data structures ────────────────────────────────────────────────────────

@dataclass
class TradePlan:
    """
    Human-readable trade plan for a single signal.
    All prices in cents. Size in dollars.
    """
    signal:          str           # ENTRY | STRONG ENTRY | WATCH | AVOID | NO TRADE
    side:            str           # YES | NO
    entry:           float         # suggested entry price (cents)
    breakeven:       float         # minimum exit price to not lose money (cents)
    first_target:    float         # conservative exit target (cents)
    strong_target:   float         # ideal exit target near fair value (cents)
    avoid_above:     float         # do not chase above this price (cents)
    max_risk_dollars:float         # maximum dollar risk for this trade
    contracts:       int           # suggested contract count
    buy_fee_est:     float         # estimated Kalshi fee to enter (cents total)
    sell_fee_est:    float         # estimated Kalshi fee to exit (cents total)
    total_fee_est:   float         # buy + sell fee total (cents)
    raw_edge:        float         # fair - ask (cents)
    fee_adj_edge:    float         # raw_edge minus fee per contract (cents)
    fair_price:      float         # model fair value (cents)
    ask_price:       float         # current ask price (cents)
    reason:          str           # 1-sentence plain-English explanation
    detail:          str           # multi-line detail for the UI
    data_quality:    str           # FULL | PARTIAL | MISSING


@dataclass
class MarketSignal:
    """One scanned market with all computed signal fields.
    ALL prices stored as CENTS (0–100) for display convenience.
    Input dollar prices are converted to cents via _to_cents() in analyse_market().
    format_price() must NOT be called on these — they are already cents.
    Use format_cents(value) to display them as "50c".
    """
    market_id:      str
    market_name:    str
    category:       str
    side:           str            # YES | NO
    bid_price:      float          # cents (0–100)
    ask_price:      float          # cents
    last_price:     float          # cents
    fair_price:     float          # cents, 0.0 = missing
    volume:         int
    liquidity:      str

    # Computed fields (filled by analyse_market)
    raw_edge:       float = 0.0    # cents: fair - ask
    fee_est:        float = 0.0    # cents total
    fee_adj_edge:   float = 0.0    # cents
    breakeven:      float = 0.0    # cents
    spread:         float = 0.0    # cents: ask - bid
    signal:         str   = "NO TRADE"
    suggested_size: float = 0.0    # dollars
    exit_target:    float = 0.0    # cents
    reason:         str   = ""
    status:         str   = "PAPER"
    data_quality:   str   = "FULL"
    trade_plan:     Optional[TradePlan] = field(default=None)


@dataclass
class PaperTrade:
    """One paper trade record."""
    time:          str
    market:        str
    side:          str
    entry_price:   float           # cents
    contracts:     int
    fee_paid:      float           # cents (total buy fee)
    target_exit:   float           # cents
    current_price: float           # cents
    status:        str  = "OPEN"

    @property
    def unrealized_pl(self) -> float:
        """Estimated P&L in dollars. Negative = loss."""
        if self.status != "OPEN":
            return 0.0
        gain_cents    = (self.current_price - self.entry_price) * self.contracts
        gain_dollars  = gain_cents / 100.0
        fee_dollars   = self.fee_paid / 100.0
        return round(gain_dollars - fee_dollars, 2)


@dataclass
class RiskGuard:
    """
    Enforces paper-mode limits. Auto trading is always OFF.
    can_trade() returns (False, reason) to block any real action.
    """
    max_trade_size:     float = 10.0
    max_daily_loss:     float = 30.0
    max_trades_per_day: int   = 10
    stop_after_losses:  int   = 3
    auto_trading:       bool  = False   # NEVER set to True
    trades_today:       int   = 0
    losses_today:       int   = 0
    daily_pnl:          float = 0.0

    def can_trade(self) -> Tuple[bool, str]:
        if self.auto_trading:
            return False, "Auto trading is OFF — paper mode only"
        if self.daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit ${self.max_daily_loss:.0f} reached"
        if self.trades_today >= self.max_trades_per_day:
            return False, f"Max {self.max_trades_per_day} trades/day reached"
        if self.losses_today >= self.stop_after_losses:
            return False, f"Stop-loss triggered after {self.stop_after_losses} losses"
        return True, "Paper mode OK"


# ── Fee calculations ───────────────────────────────────────────────────────

def calculate_kalshi_fee(contracts: int, price_cents: float) -> float:
    """
    Official Kalshi fee formula:
      fee = ceil_to_cent(0.07 × contracts × price × (1 − price))

    where price is in DOLLARS (0.0 – 1.0), not cents.

    Example:
      contracts=22, price=44c → price_dollars=0.44
      fee = ceil(0.07 × 22 × 0.44 × 0.56) = ceil(0.3793) = 0.38 → 38 cents

    Returns: fee in CENTS (total, not per contract).
    """
    if contracts <= 0 or price_cents <= 0:
        return 0.0
    price_dollars   = price_cents / 100.0
    raw_fee_dollars = 0.07 * contracts * price_dollars * (1.0 - price_dollars)
    fee_cents       = math.ceil(raw_fee_dollars * 100.0)
    return float(fee_cents)


def calculate_contracts_for_budget(budget_dollars: float,
                                    price_cents: float) -> int:
    """
    Conservative contract count for a given budget.

    Accounts for both the purchase cost and the entry fee so we
    never overspend the budget.

    Formula (per contract):
      cost_per = price_cents/100 + fee_per_contract_dollars
      fee_per  = 0.07 × price_dollars × (1 − price_dollars)
      contracts = floor(budget / cost_per)

    Args:
        budget_dollars: e.g. 10.0 for a $10 max trade
        price_cents:    e.g. 44.0 for a 44-cent market

    Returns: integer number of contracts (minimum 0).
    """
    if price_cents <= 0 or budget_dollars <= 0:
        return 0
    price_dollars = price_cents / 100.0
    fee_per       = 0.07 * price_dollars * (1.0 - price_dollars)
    cost_per      = price_dollars + fee_per
    if cost_per <= 0:
        return 0
    return max(0, int(budget_dollars / cost_per))


def calculate_raw_edge(fair_cents: float, buy_price_cents: float) -> float:
    """
    Raw (pre-fee) edge for a BUY order:
      raw_edge = fair_price − ask_price

    Positive → we're paying less than fair value (value bet).
    Negative → market is asking more than fair value (overpriced).

    Args:
        fair_cents:      model's estimate of true probability × 100
        buy_price_cents: current ask price to enter the trade
    """
    return round(fair_cents - buy_price_cents, 1)


def calculate_fee_adjusted_edge(raw_edge_cents: float,
                                 total_fee_cents: float,
                                 contracts: int) -> float:
    """
    Edge after deducting the per-contract fee burden:
      fee_adj_edge = raw_edge − (total_fee / contracts)

    This is the true edge we keep after paying Kalshi.
    If fee_adj_edge is still positive, the trade has real value.

    Args:
        raw_edge_cents:  output of calculate_raw_edge()
        total_fee_cents: total fee for the position (buy + sell estimate)
        contracts:       number of contracts in the position
    """
    if contracts <= 0:
        return raw_edge_cents
    fee_per_contract = total_fee_cents / contracts
    return round(raw_edge_cents - fee_per_contract, 1)


def calculate_breakeven_exit(entry_cents: float, contracts: int) -> float:
    """
    Minimum sell price needed to not lose money.

    Must cover:
      1. Entry cost   (entry_cents × contracts)
      2. Buy fee      (calculate_kalshi_fee at entry)
      3. Sell fee     (estimated at breakeven — one iteration)

    Derivation:
      total_needed = entry × n + buy_fee
      sell_revenue = sell_price × n − sell_fee(sell_price)
      Set sell_revenue = total_needed, solve for sell_price.
      (One Newton iteration is sufficient for our precision.)

    Returns: breakeven exit price in cents.
    """
    if contracts <= 0 or entry_cents <= 0:
        return 0.0

    buy_fee = calculate_kalshi_fee(contracts, entry_cents)

    # Estimate: first guess = entry + fee burden per contract
    est_sell    = entry_cents + (buy_fee / contracts)
    sell_fee    = calculate_kalshi_fee(contracts, est_sell)

    # One refinement step
    total_out   = entry_cents * contracts + buy_fee + sell_fee
    breakeven   = total_out / contracts
    return round(breakeven, 1)


# ── Signal classification ──────────────────────────────────────────────────

def classify_signal(
    edge_cents:     float,
    spread_cents:   float,
    fair_price:     float,
    max_spread:     float = 5.0,
    min_edge:       float = 8.0,
    liquidity:      str   = "Medium",
    fee_adj_edge:   float = 0.0,
) -> str:
    """
    Classify a market into one of five signal tiers.

    Decision tree (evaluated top to bottom — first match wins):

    1. DATA NEEDED  — fair price is 0 or missing: cannot calculate edge
    2. NO TRADE     — spread too wide or liquidity too low for the spread
    3. AVOID        — raw edge is negative (market is overpriced)
    4. WATCH        — edge positive but below minimum threshold
    5. ENTRY        — edge above minimum threshold
    6. STRONG ENTRY — edge well above threshold AND tight spread AND good liquidity

    Args:
        edge_cents:   raw edge (fair - ask) in cents
        spread_cents: bid-ask spread in cents
        fair_price:   model fair price in cents (0 = unknown)
        max_spread:   maximum acceptable spread (cents)
        min_edge:     minimum edge to trigger ENTRY (cents)
        liquidity:    "High" | "Medium" | "Low"
        fee_adj_edge: fee-adjusted edge (used for STRONG ENTRY gate)
    """
    # Gate 1 — missing fair price
    if fair_price <= 0:
        return "DATA NEEDED"

    # Gate 2 — spread / liquidity
    if liquidity == "Low" and spread_cents > max_spread * 0.6:
        return "NO TRADE"
    if spread_cents > max_spread:
        return "NO TRADE"

    # Gate 3 — negative edge
    if edge_cents <= 0:
        return "AVOID"

    # Gate 4 — below threshold
    if edge_cents < min_edge:
        return "WATCH"

    # Gate 5/6 — ENTRY vs STRONG ENTRY
    # STRONG ENTRY: edge is meaningfully above minimum, spread tight,
    # liquidity good, and fee-adjusted edge is still positive.
    strong_edge_threshold = min_edge + 3.0
    if (edge_cents >= strong_edge_threshold
            and spread_cents <= 3.0
            and liquidity in ("High", "Medium")
            and fee_adj_edge > 0):
        return "STRONG ENTRY"

    return "ENTRY"


def _suggest_size(signal: str, max_size: float, edge_cents: float) -> float:
    """
    Conservative position sizing by signal tier.

    STRONG ENTRY → full max_size
    ENTRY        → 60% of max_size (min $5)
    others       → $0 (no trade recommended)
    """
    if signal == "STRONG ENTRY":
        return max_size
    if signal == "ENTRY":
        return min(max_size, max(5.0, max_size * 0.6))
    return 0.0


def _suggest_exit(fair_cents: float, ask_cents: float, signal: str) -> float:
    """
    Conservative first exit target.

    For actionable signals:
      first_target = ask + 60% of the raw edge
    This locks in most of the edge before the market fully reprices.
    """
    if signal in ("ENTRY", "STRONG ENTRY"):
        raw = fair_cents - ask_cents
        return round(ask_cents + raw * 0.6, 1)
    return 0.0


# ── Human-readable explanation builder ────────────────────────────────────

# ── Market type classifier ───────────────────────────────────────────────────

def classify_market_type(
    market_name: str = "",
    ticker:      str = "",
    category:    str = "",
    raw_data:    dict = None,
) -> dict:
    """
    Classify what kind of Kalshi market this is from title/ticker/category.

    Returns:
        {
            "market_type":    str,   # CRYPTO_PRICE | SPORTS | ECONOMIC | WEATHER |
                                     # POLITICS | FINANCIAL_INDEX | COMPANY | OTHER | UNKNOWN
            "category":       str,
            "asset":          Optional[str],   # BTC / ETH / SPX / etc.
            "direction":      Optional[str],   # ABOVE / BELOW / UNKNOWN
            "threshold":      Optional[float],
            "unit":           Optional[str],   # USD / DEGREES / etc.
            "time_window":    Optional[str],   # deadline phrase
            "confidence":     str,  # HIGH / MEDIUM / LOW
            "parser_status":  str,  # PARSED / PARTIAL / UNKNOWN
            "reasons":        list[str],
            "missing_inputs": list[str],
        }

    Conservative — never forces a classification it isn't sure of.
    """
    import re
    reasons  = []
    missing  = []
    name_up  = (market_name or "").upper()
    tick_up  = (ticker or "").upper()
    cat_low  = (category or "").lower()
    combined = f"{name_up} {tick_up}"

    # ── Crypto ─────────────────────────────────────────────────────────
    CRYPTO_KW = {"BTC","BITCOIN","ETH","ETHEREUM","CRYPTO","SOLANA","SOL",
                 "DOGE","XRP","USDT","USDC"}
    if any(k in combined for k in CRYPTO_KW) or "crypto" in cat_low:
        # Delegate detailed parsing to parse_crypto_market_title
        try:
            from crypto_price_connectors import parse_crypto_market_title
            ctx = parse_crypto_market_title(market_name)
            reasons.append(f"Crypto asset: {ctx.asset}")
            return {
                "market_type":   "CRYPTO_PRICE",
                "category":      category or "Crypto",
                "asset":         ctx.asset if ctx.asset != "UNKNOWN" else None,
                "direction":     ctx.condition if ctx.condition != "UNKNOWN" else None,
                "threshold":     ctx.target_price,
                "unit":          "USD" if ctx.target_price else None,
                "time_window":   ctx.expiration_text,
                "confidence":    "HIGH" if ctx.target_price else "MEDIUM",
                "parser_status": "PARSED" if ctx.target_price else "PARTIAL",
                "reasons":       reasons,
                "missing_inputs":[] if ctx.target_price else ["target price not parsed"],
            }
        except Exception as e:
            reasons.append(f"Crypto parse error: {e}")
            return _unknown_market_type(market_name, reasons, [str(e)])

    # ── Sports ─────────────────────────────────────────────────────────
    SPORTS_KW = {"SOCCER","FOOTBALL","BASKETBALL","MLB","NFL","NBA","NHL","UFC",
                 "FIFA","PREMIER LEAGUE","LA LIGA","SUPER BOWL","WORLD CUP",
                 "GOAL","MATCH","GAME","PLAYER","TEAM","SCORE"}
    if any(k in combined for k in SPORTS_KW) or "sports" in cat_low:
        reasons.append("Sports keywords detected")
        return _typed(market_name, "SPORTS", category, reasons, confidence="MEDIUM")

    # ── Economic ───────────────────────────────────────────────────────
    ECON_KW = {"CPI","INFLATION","FOMC","FED","FEDERAL RESERVE","RATE","GDP",
               "UNEMPLOYMENT","JOBS","PAYROLL","PCE","ISM","PMI","DEFICIT",
               "DEBT","TREASURY","YIELD","INTEREST RATE"}
    if any(k in combined for k in ECON_KW) or "economics" in cat_low:
        reasons.append("Economic indicator keywords detected")
        return _typed(market_name, "ECONOMIC", category, reasons, confidence="MEDIUM")

    # ── Weather ────────────────────────────────────────────────────────
    WEATHER_KW = {"HURRICANE","TROPICAL","STORM","RAIN","SNOW","TEMPERATURE",
                  "TORNADO","DROUGHT","FLOOD","WEATHER","CELSIUS","FAHRENHEIT"}
    if any(k in combined for k in WEATHER_KW) or "weather" in cat_low:
        reasons.append("Weather keywords detected")
        return _typed(market_name, "WEATHER", category, reasons, confidence="MEDIUM")

    # ── Politics ───────────────────────────────────────────────────────
    POLITICS_KW = {"ELECTION","VOTE","PRESIDENT","CONGRESS","SENATE","BILL",
                   "POLICY","CANDIDATE","PARTY","DEMOCRAT","REPUBLICAN","TRUMP",
                   "BIDEN","PRIMARY","LEGISLATION"}
    if any(k in combined for k in POLITICS_KW) or "politics" in cat_low:
        reasons.append("Politics keywords detected")
        return _typed(market_name, "POLITICS", category, reasons, confidence="MEDIUM")

    # ── Financial index ────────────────────────────────────────────────
    INDEX_KW = {"S&P","SPX","SP500","NASDAQ","DOW","DJIA","RUSSELL","VIX",
                "INDEX","STOCK MARKET","EQUITY"}
    if any(k in combined for k in INDEX_KW):
        reasons.append("Financial index keywords detected")
        return _typed(market_name, "FINANCIAL_INDEX", category, reasons, confidence="MEDIUM")

    # ── Category fallback ──────────────────────────────────────────────
    if category:
        reasons.append(f"Using provided category: {category}")
        return _typed(market_name, "OTHER", category, reasons, confidence="LOW")

    missing.append("No recognizable keywords found in title/ticker/category")
    return _unknown_market_type(market_name, reasons, missing)


def _typed(name, mtype, cat, reasons, confidence="MEDIUM"):
    return {
        "market_type": mtype, "category": cat or mtype.title(),
        "asset": None, "direction": None, "threshold": None,
        "unit": None, "time_window": None,
        "confidence": confidence, "parser_status": "PARTIAL",
        "reasons": reasons, "missing_inputs": [],
    }

def _unknown_market_type(name, reasons, missing):
    return {
        "market_type": "UNKNOWN", "category": "Unknown",
        "asset": None, "direction": None, "threshold": None,
        "unit": None, "time_window": None,
        "confidence": "LOW", "parser_status": "UNKNOWN",
        "reasons": reasons, "missing_inputs": missing,
    }


# ── Settlement rule parser ────────────────────────────────────────────────────

def parse_settlement_rules(raw_data: dict) -> dict:
    """
    Parse settlement rules from a Kalshi market raw_data dict.

    Returns:
        {
            "rules_available":  bool,
            "rules_summary":    str,
            "settlement_sources": list[str],
            "settlement_value": Optional[str],
            "close_time":       Optional[str],
            "expiration_time":  Optional[str],
            "can_close_early":  Optional[bool],
            "rule_clarity":     str,   # GOOD | PARTIAL | MISSING
            "warnings":         list[str],
            "raw_rules_preview":Optional[str],  # first 300 chars only
        }

    Does NOT invent rules. If missing, says so clearly.
    """
    if not raw_data:
        raw_data = {}

    warnings = []
    sources  = []

    rules_p  = (raw_data.get("rules_primary",   "") or "").strip()
    rules_s  = (raw_data.get("rules_secondary",  "") or "").strip()
    sett_src = raw_data.get("settlement_source", "") or raw_data.get("settlement_sources", "")
    sett_val = raw_data.get("settlement_value",  None)
    close_t  = raw_data.get("close_time",        None) or raw_data.get("expiration_time", None)
    exp_t    = raw_data.get("expected_expiration_time", None) or raw_data.get("expiration_time", None)
    can_early= raw_data.get("can_close_early",   None)
    result   = raw_data.get("result",            None)

    if isinstance(sett_src, str) and sett_src:
        sources = [sett_src]
    elif isinstance(sett_src, list):
        sources = [str(s) for s in sett_src if s]

    # Determine rule clarity
    if rules_p:
        rule_clarity = "GOOD"
        summary      = rules_p[:120] + ("…" if len(rules_p) > 120 else "")
        preview      = rules_p[:300]
    elif rules_s:
        rule_clarity = "PARTIAL"
        summary      = rules_s[:120] + ("…" if len(rules_s) > 120 else "")
        preview      = rules_s[:300]
        warnings.append("Only secondary rules available — primary rules missing")
    else:
        rule_clarity = "MISSING"
        summary      = "Settlement rules not available from current market payload."
        preview      = None
        warnings.append("Settlement rules missing — verify before paper trading")

    warnings.append("Always verify settlement rules before real trading. Paper mode only.")

    return {
        "rules_available":   bool(rules_p or rules_s),
        "rules_summary":     summary,
        "settlement_sources":sources,
        "settlement_value":  str(sett_val) if sett_val else None,
        "close_time":        str(close_t)  if close_t  else None,
        "expiration_time":   str(exp_t)    if exp_t    else None,
        "can_close_early":   can_early,
        "rule_clarity":      rule_clarity,
        "warnings":          warnings,
        "raw_rules_preview": preview,
    }


# ── Data quality scorer ───────────────────────────────────────────────────────

def data_quality_score(
    has_bid:            bool = False,
    has_ask:            bool = False,
    has_last:           bool = False,
    has_orderbook:      bool = False,
    has_settlement_rules:bool = False,
    has_expiration:     bool = False,
    has_crypto_ref:     bool = False,   # only relevant if crypto market
    is_crypto_market:   bool = False,
    has_fair_price:     bool = False,
    market_type_confidence: str = "LOW",
) -> str:
    """
    Return data quality label: GOOD | PARTIAL | MISSING | LOW_CONFIDENCE

    Used in Signal Detail, watchlist, and signal scoring.
    Conservative — never inflates quality.
    """
    # MISSING: no usable prices at all
    if not has_bid and not has_ask and not has_last:
        return "MISSING"

    score = 0
    if has_bid:  score += 2
    if has_ask:  score += 2
    if has_last: score += 1
    if has_orderbook: score += 2
    if has_settlement_rules: score += 2
    if has_expiration: score += 1
    if has_fair_price: score += 2
    if is_crypto_market and has_crypto_ref: score += 1
    if market_type_confidence == "HIGH":   score += 1

    if score >= 10: return "GOOD"
    if score >= 5:  return "PARTIAL"
    if market_type_confidence == "LOW":    return "LOW_CONFIDENCE"
    return "PARTIAL"


# ── Fair price estimation (heuristic placeholder) ────────────────────────────

def estimate_fair_price(
    market_name:    str,
    category:       str          = "",
    crypto_prices:  dict         = None,   # {symbol: CryptoPriceSnapshot}
    expiration_str: str          = None,
) -> dict:
    """
    Estimate a conservative heuristic fair price for a Kalshi market.

    Returns:
        {
            "fair_price":        Optional[float],   # 0.0–1.0 (dollars), None = unavailable
            "fair_price_cents":  Optional[float],   # 0–100 display
            "fair_price_source": str,               # model status label
            "confidence":        str,               # LOW / NONE
            "model_status":      str,               # UNAVAILABLE / DATA_NEEDED / HEURISTIC_ONLY
            "reasons":           list[str],
            "missing_inputs":    list[str],
        }

    IMPORTANT:
    - This is a rough heuristic only.
    - Do NOT use for real trading decisions.
    - All outputs are marked HEURISTIC_ONLY or DATA_NEEDED.
    - Confidence is always LOW or NONE.
    - Missing inputs → fair_price = None (never fabricated).
    """
    missing  = []
    reasons  = []
    fp_d     = None       # fair price in dollars
    source   = "UNAVAILABLE"
    conf     = "NONE"
    status   = "UNAVAILABLE"

    # ── Try to parse crypto market ─────────────────────────────────────
    try:
        from crypto_price_connectors import parse_crypto_market_title, CryptoMarketContext
        ctx: CryptoMarketContext = parse_crypto_market_title(market_name or "")
    except Exception as e:
        return {
            "fair_price": None, "fair_price_cents": None,
            "fair_price_source": "UNAVAILABLE",
            "confidence": "NONE", "model_status": "UNAVAILABLE",
            "reasons": [], "missing_inputs": [f"parse error: {e}"],
        }

    # ── Non-crypto market — no heuristic yet ──────────────────────────
    if ctx.asset == "UNKNOWN":
        return {
            "fair_price": None, "fair_price_cents": None,
            "fair_price_source": "UNAVAILABLE",
            "confidence": "NONE", "model_status": "UNAVAILABLE",
            "reasons":  [],
            "missing_inputs": ["Non-crypto market — no heuristic model available"],
        }

    # ── Crypto market — try to compute distance-based heuristic ───────
    asset = ctx.asset   # "BTC" or "ETH"

    # Get reference price
    ref_price = None
    if crypto_prices and asset in crypto_prices:
        snap = crypto_prices[asset]
        if snap and snap.price and snap.price > 0:
            ref_price = snap.price
            reasons.append(f"{asset} ref price: ${ref_price:,.2f}")
        else:
            missing.append(f"{asset} reference price unavailable")
    else:
        missing.append(f"{asset} reference price not loaded")

    if ref_price is None:
        return {
            "fair_price": None, "fair_price_cents": None,
            "fair_price_source": "DATA_NEEDED",
            "confidence": "NONE", "model_status": "DATA_NEEDED",
            "reasons": reasons, "missing_inputs": missing,
        }

    # Get target price
    target = ctx.target_price
    if target is None or target <= 0:
        missing.append("Target price not parseable from title")
        return {
            "fair_price": None, "fair_price_cents": None,
            "fair_price_source": "DATA_NEEDED",
            "confidence": "NONE", "model_status": "DATA_NEEDED",
            "reasons": reasons, "missing_inputs": missing,
        }

    reasons.append(f"Target: ${target:,.2f}  Direction: {ctx.condition}")

    # Distance to target as fraction of target
    dist_frac = (ref_price - target) / target   # positive = above target

    # Time factor (if expiration available)
    time_factor = 1.0
    time_mins   = None
    if expiration_str and expiration_str not in ("N/A", "", None):
        try:
            from datetime import datetime, timezone
            for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
                try:
                    if fmt.endswith("Z"):
                        dt = datetime.strptime(expiration_str, fmt).replace(tzinfo=timezone.utc)
                    else:
                        dt = datetime.strptime(expiration_str, fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    diff = (dt - datetime.now(timezone.utc)).total_seconds()
                    time_mins = max(0, diff / 60)
                    break
                except Exception:
                    continue
        except Exception:
            pass

    if time_mins is not None:
        reasons.append(f"Time to expiry: {int(time_mins)}m")
        # Simple time scaling: more time = more uncertainty
        if time_mins > 1440:
            time_factor = 0.6    # >1 day: very uncertain
        elif time_mins > 240:
            time_factor = 0.75   # >4 hours
        elif time_mins > 60:
            time_factor = 0.85   # >1 hour
        else:
            time_factor = 0.95   # <1 hour: more decisive
    else:
        missing.append("Expiration time unavailable — time factor not applied")
        time_factor = 0.7    # conservative without expiry

    # ── Heuristic: logistic-style curve on distance ────────────────────
    # This is a ROUGH placeholder only — do not use for real trading.
    # p(ABOVE) = sigmoid(k * dist_frac / time_uncertainty)
    import math
    k = 4.0   # sharpness (purely empirical)
    raw_p = 1.0 / (1.0 + math.exp(-k * dist_frac * time_factor))

    if ctx.condition == "ABOVE":
        fp_d = round(raw_p, 4)
        reasons.append(
            f"Heuristic P(above ${target:,.0f}): {fp_d*100:.1f}c "
            f"(dist: {dist_frac*100:+.1f}%, time_factor={time_factor:.2f})")
    elif ctx.condition == "BELOW":
        fp_d = round(1.0 - raw_p, 4)
        reasons.append(
            f"Heuristic P(below ${target:,.0f}): {fp_d*100:.1f}c "
            f"(dist: {dist_frac*100:+.1f}%, time_factor={time_factor:.2f})")
    else:
        missing.append("Condition (ABOVE/BELOW) not parsed")
        fp_d = None

    if fp_d is not None:
        # Clip to conservative range 0.05–0.95 (never claim certainty)
        fp_d   = round(max(0.05, min(0.95, fp_d)), 4)
        source = "HEURISTIC_ONLY"
        conf   = "LOW"
        status = "HEURISTIC_ONLY"
        reasons.append(
            "⚠ HEURISTIC ONLY — not a real volatility model. "
            "Confidence: LOW. Do not use for real trading.")
    else:
        status = "DATA_NEEDED"

    return {
        "fair_price":        fp_d,
        "fair_price_cents":  round(fp_d * 100, 2) if fp_d is not None else None,
        "fair_price_source": source,
        "confidence":        conf,
        "model_status":      status,
        "reasons":           reasons,
        "missing_inputs":    missing,
    }


# ── Signal scoring ───────────────────────────────────────────────────────────

SIGNAL_PRIORITY = {
    "POSSIBLE EDGE": 0,
    "STRONG ENTRY":  1,
    "ENTRY":         2,
    "WATCH":         3,
    "PAPER ONLY":    4,
    "CAUTION":       5,
    "DATA NEEDED":   6,
    "AVOID":         7,
    "NO TRADE":      8,
}


def score_market(
    signal:       str,
    spread_cents: float,
    liquidity:    str,
    bid:          float,
    ask:          float,
    fair:         float,
    volume:       int,
    extra:        dict = None,   # optional: {"distance_pct": float, "time_left_mins": int}
) -> dict:
    """
    Compute a 0-100 signal score and augmented signal tier.

    Returns:
        {
            "score":       int,       # 0 (worst) to 100 (best)
            "tier":        str,       # upgraded signal label
            "reasons":     list[str], # human-readable positive reasons
            "risks":       list[str], # human-readable risk factors
            "suggested":   str,       # one-line recommended action
            "data_issues": list[str], # missing data problems
        }

    Does NOT fabricate edge. Missing fair price → conservative result.
    """
    extra       = extra or {}
    score       = 0
    reasons     = []
    risks       = []
    data_issues = []
    tier        = signal

    # ── Settlement rules / market type safety ──────────────────────────
    if extra.get("settlement_rules_missing"):
        risks.append("Settlement rules unavailable — verify before paper trading")
        # Never let a missing-rules market reach POSSIBLE EDGE
        if tier == "POSSIBLE EDGE":
            tier = "PAPER ONLY"

    if extra.get("market_type") == "UNKNOWN":
        risks.append("Market type unrecognized — low confidence in analysis")
        if extra.get("parser_confidence") == "LOW":
            data_issues.append("Parser confidence LOW for this market")

    # ── Data availability ──────────────────────────────────────────────
    if ask <= 0:
        data_issues.append("Missing ask price — load orderbook first")
        tier = "DATA NEEDED"
    if bid <= 0:
        data_issues.append("Missing bid price")
    if fair <= 0:
        data_issues.append("No fair price model — cannot calculate true edge")
        risks.append("Fair value unavailable — paper/watch only")

    if not data_issues:
        score += 20
        reasons.append("Quote available (bid/ask loaded)")

    # ── Spread ─────────────────────────────────────────────────────────
    if ask > 0 and bid > 0:
        if spread_cents <= 2:
            score += 20
            reasons.append(f"Tight spread ({spread_cents:.1f}c)")
        elif spread_cents <= 5:
            score += 10
            reasons.append(f"Acceptable spread ({spread_cents:.1f}c)")
        elif spread_cents <= 10:
            score += 0
            risks.append(f"Wide spread ({spread_cents:.1f}c)")
        else:
            score -= 10
            risks.append(f"Very wide spread ({spread_cents:.1f}c) — CAUTION")
            if tier not in ("DATA NEEDED", "AVOID"):
                tier = "CAUTION"

    # ── Liquidity ──────────────────────────────────────────────────────
    liq_scores = {"High": 20, "Medium": 10, "Low": 0}
    liq_score  = liq_scores.get(liquidity, 5)
    score += liq_score
    if liquidity == "High":
        reasons.append("High liquidity")
    elif liquidity == "Low":
        risks.append("Low liquidity — fill uncertainty")
        if tier not in ("DATA NEEDED", "AVOID"):
            tier = "CAUTION"

    # ── Volume ─────────────────────────────────────────────────────────
    if volume > 10000:
        score += 10
        reasons.append(f"High volume ({volume:,})")
    elif volume > 1000:
        score += 5
    elif volume == 0:
        data_issues.append("No volume data")

    # ── Crypto reference distance ───────────────────────────────────────
    dist_pct = extra.get("distance_pct")
    if dist_pct is not None:
        abs_dist = abs(dist_pct)
        if abs_dist <= 1.0:
            score += 15
            reasons.append(f"Price very close to target ({dist_pct:+.2f}%)")
            if tier in ("WATCH",):
                tier = "PAPER ONLY"
        elif abs_dist <= 3.0:
            score += 8
            reasons.append(f"Price near target ({dist_pct:+.2f}%)")
        else:
            risks.append(f"Price far from target ({dist_pct:+.2f}%)")

    # ── Time to expiration ─────────────────────────────────────────────
    time_left = extra.get("time_left_mins")
    if time_left is not None:
        if time_left < 15:
            score -= 15
            risks.append(f"Expiring very soon ({time_left}m) — CAUTION")
            if tier not in ("DATA NEEDED", "AVOID"):
                tier = "CAUTION"
        elif time_left < 60:
            score -= 5
            risks.append(f"Less than 1 hour to expiration ({time_left}m)")
        elif time_left > 1440:
            score += 5
            reasons.append(f"Plenty of time remaining ({time_left//60}h)")

    # ── Fair price edge ────────────────────────────────────────────────
    if fair > 0 and ask > 0:
        edge = fair - ask
        if edge >= 12:
            score += 20
            # Only upgrade to POSSIBLE EDGE if settlement rules are available
            # and no other safety downgrade was applied
            if not extra.get("settlement_rules_missing"):
                tier = "POSSIBLE EDGE"
            elif tier not in ("DATA NEEDED", "AVOID"):
                tier = "PAPER ONLY"
            reasons.append(f"Strong edge: {edge:+.1f}c above fair value")
        elif edge >= 8:
            score += 15
            reasons.append(f"Edge: {edge:+.1f}c above fair value")
        elif edge >= 3:
            score += 8
            reasons.append(f"Positive edge: {edge:+.1f}c")
        elif edge < 0:
            score -= 10
            risks.append(f"Negative edge ({edge:+.1f}c) — market overpriced")

    score = max(0, min(100, score))

    # ── Suggested action ───────────────────────────────────────────────
    if tier == "POSSIBLE EDGE":
        suggested = "Consider paper trade — edge present if fair model is correct"
    elif tier in ("WATCH", "PAPER ONLY"):
        suggested = "Add to watchlist — monitor for better entry or confirmation"
    elif tier == "CAUTION":
        suggested = "Wait — spread/liquidity/timing unfavorable"
    elif tier == "DATA NEEDED":
        suggested = "Load orderbook and enable fair price model first"
    elif tier == "AVOID":
        suggested = "Market appears overpriced — skip"
    else:
        suggested = "Monitor only"

    return {
        "score":       score,
        "tier":        tier,
        "reasons":     reasons,
        "risks":       risks,
        "suggested":   suggested,
        "data_issues": data_issues,
    }


def build_trade_plan(
    raw:          dict,
    signal:       str,
    edge:         float,
    fee_adj_edge: float,
    breakeven:    float,
    contracts:    int,
    buy_fee:      float,
    fair:         float,
    ask:          float,
    bid:          float,
    spread:       float,
    max_size:     float,
    min_edge:     float,
) -> TradePlan:
    """
    Build a complete TradePlan with human-readable explanation.

    All prices in cents. Returns a TradePlan dataclass.
    """
    side      = raw.get("side", "YES")
    market    = raw.get("market_name", "")
    liquidity = raw.get("liquidity", "Medium")

    # Sell fee estimate at the first target
    exit_target    = _suggest_exit(fair, ask, signal)
    sell_fee       = calculate_kalshi_fee(contracts, exit_target) if exit_target > 0 else 0.0
    total_fee      = buy_fee + sell_fee
    avoid_above    = round(ask + 3, 1)
    strong_target  = round(fair * 0.97, 1)
    max_risk       = _suggest_size(signal, max_size, edge)
    data_quality   = _data_quality(raw)

    # ── Plain-English reason (one sentence) ───────────────────────────────
    # Build context-aware reason
    # ask_missing: no ask price means bid/ask not yet loaded from orderbook
    _ask_missing_in_plan = (ask == 0)
    if _ask_missing_in_plan:
        data_needed_reason = (
            "Kalshi market data loaded, but model fair price is not available yet. "
            "Click 'Load Orderbook' to fetch bid/ask prices for this market, "
            "then connect a pricing model to generate ENTRY signals."
        )
    elif fair == 0:
        data_needed_reason = (
            "Kalshi market loaded with live bid/ask. "
            "Model fair price is not available yet — cannot calculate edge. "
            "Signal will upgrade once a fair price estimate is added."
        )
    else:
        data_needed_reason = (
            "No model fair price available — cannot calculate edge. "
            "Add a fair price estimate before trading."
        )

    reasons = {
        "STRONG ENTRY": (
            f"Model fair value is {fair:.0f}c but market asks only {ask:.0f}c "
            f"— {edge:+.0f}c raw edge, {fee_adj_edge:+.0f}c after fees, "
            f"tight {spread:.0f}c spread, {liquidity.lower()} liquidity."
        ),
        "ENTRY": (
            f"Model fair value {fair:.0f}c vs ask {ask:.0f}c "
            f"gives {edge:+.0f}c edge ({fee_adj_edge:+.0f}c after fees). "
            f"Spread {spread:.0f}c is acceptable."
        ),
        "WATCH": (
            f"Edge is {edge:+.0f}c — positive but below the {min_edge:.0f}c "
            f"minimum threshold. Monitor for improvement."
        ),
        "AVOID": (
            f"Market ask {ask:.0f}c exceeds model fair {fair:.0f}c "
            f"by {-edge:.0f}c — do not buy at this price."
        ),
        "NO TRADE": (
            f"Spread {spread:.0f}c exceeds limit or {liquidity.lower()} "
            f"liquidity makes fill uncertain."
        ),
        "DATA NEEDED": data_needed_reason,
    }
    reason = reasons.get(signal, "Unknown signal.")

    # ── Multi-line detail for the UI ──────────────────────────────────────
    if signal in ("ENTRY", "STRONG ENTRY"):
        detail = (
            f"Buy {side} at {ask:.0f}c or better.\n"
            f"Contracts at ${max_risk:.0f}: ~{contracts}\n"
            f"Entry fee (est): {buy_fee:.0f}c\n"
            f"Breakeven exit:  {breakeven:.0f}c\n"
            f"First target:    {exit_target:.0f}c\n"
            f"Strong target:   {strong_target:.0f}c\n"
            f"Do not chase above {avoid_above:.0f}c.\n"
            f"Total fees (est): {total_fee:.0f}c\n"
            f"Mode: Paper only — no real orders sent."
        )
    elif signal == "WATCH":
        detail = (
            f"Edge {edge:+.0f}c is below {min_edge:.0f}c minimum.\n"
            f"Watch for ask to drop below {fair - min_edge:.0f}c.\n"
            f"No position recommended yet."
        )
    elif signal == "DATA NEEDED":
        detail = (
            "Fair price is missing or zero.\n"
            "Cannot compute edge without a model estimate.\n"
            "Signal will update when fair price is available."
        )
    else:
        detail = reason

    return TradePlan(
        signal           = signal,
        side             = side,
        entry            = ask,
        breakeven        = breakeven,
        first_target     = exit_target if exit_target > 0 else 0.0,
        strong_target    = strong_target if fair > 0 else 0.0,
        avoid_above      = avoid_above,
        max_risk_dollars = max_risk,
        contracts        = contracts,
        buy_fee_est      = buy_fee,
        sell_fee_est     = sell_fee,
        total_fee_est    = total_fee,
        raw_edge         = edge,
        fee_adj_edge     = fee_adj_edge,
        fair_price       = fair,
        ask_price        = ask,
        reason           = reason,
        detail           = detail,
        data_quality     = data_quality,
    )


def _data_quality(raw: dict) -> str:
    """
    Assess how complete the market data is.

    FULL    — fair price + bid + ask all present
    PARTIAL — some prices missing or zero
    MISSING — fair price not available
    """
    fair = raw.get("model_fair_price", 0.0) or 0.0
    bid  = raw.get("bid_price", 0.0) or 0.0
    ask  = raw.get("ask_price", 0.0) or 0.0

    if fair <= 0:
        return "MISSING"
    if bid <= 0 or ask <= 0:
        return "PARTIAL"
    return "FULL"


# ── Full market analysis ───────────────────────────────────────────────────

def analyse_market(
    raw:        dict,
    min_edge:   float = 8.0,
    max_spread: float = 5.0,
    max_size:   float = 10.0,
) -> MarketSignal:
    """
    Analyse one market dict and return a fully computed MarketSignal.

    Args:
        raw:        dict with keys: market_id, market_name, category, side,
                    bid_price, ask_price, last_price, model_fair_price,
                    volume, liquidity
        min_edge:   minimum cents of edge to trigger ENTRY signal
        max_spread: maximum cents of spread allowed for any trade
        max_size:   maximum dollar size for position sizing

    Returns:
        MarketSignal with all fields populated, including a TradePlan.
    """
    # ── Extract raw values ─────────────────────────────────────────────
    # Prices from connectors are dollar floats (0.0-1.0).
    # The engine works in CENTS (0-100), so we multiply by 100.
    # None means the price was not available → DATA NEEDED signal.
    _bid_raw  = raw.get("bid_price",        None)
    _ask_raw  = raw.get("ask_price",        None)
    _last_raw = raw.get("last_price",       None)
    _fair_raw = raw.get("model_fair_price", None)

    def _to_cents(v, default=0.0) -> float:
        """Convert dollar float to cents. None → default (not 0)."""
        if v is None:
            return default
        try:
            f = float(v)
            # Dollar format: 0.0-1.0 → multiply by 100 to get cents
            # Cents format: already >1 (legacy) → use as-is
            if 0.0 <= f <= 1.0:
                return round(f * 100.0, 2)
            return f   # already in cents (legacy path)
        except:
            return default

    bid       = _to_cents(_bid_raw,  0.0)
    ask       = _to_cents(_ask_raw,  0.0)
    last      = _to_cents(_last_raw, ask)
    fair      = _to_cents(_fair_raw, 0.0)
    liquidity = raw.get("liquidity", "Medium")
    volume    = int(raw.get("volume", 0) or 0)

    # Track whether prices were actually provided vs missing
    bid_missing  = _bid_raw  is None
    ask_missing  = _ask_raw  is None
    fair_missing = _fair_raw is None

    # ── Derived quantities ─────────────────────────────────────────────
    spread    = round(max(0.0, ask - bid), 1)
    contracts = calculate_contracts_for_budget(max_size, ask) if ask > 0 else 0

    # ── Fees ───────────────────────────────────────────────────────────
    buy_fee   = calculate_kalshi_fee(max(contracts, 1), ask) if ask > 0 else 0.0

    # ── Edge ───────────────────────────────────────────────────────────
    raw_edge  = calculate_raw_edge(fair, ask) if fair > 0 else 0.0
    fee_adj   = calculate_fee_adjusted_edge(raw_edge, buy_fee, max(contracts, 1))

    # ── Breakeven ──────────────────────────────────────────────────────
    breakeven = calculate_breakeven_exit(ask, max(contracts, 1)) if ask > 0 else 0.0

    # ── Signal ─────────────────────────────────────────────────────────
    # If bid/ask not loaded (Kalshi markets before orderbook fetch),
    # force DATA NEEDED — we cannot compute edge without a buy price.
    if ask_missing or ask == 0:
        signal = "DATA NEEDED"
    else:
        signal = classify_signal(
            edge_cents   = raw_edge,
            spread_cents = spread,
            fair_price   = fair,
            max_spread   = max_spread,
            min_edge     = min_edge,
            liquidity    = liquidity,
            fee_adj_edge = fee_adj,
        )

    # ── Sizing and targets ─────────────────────────────────────────────
    size      = _suggest_size(signal, max_size, raw_edge)
    exit_tgt  = _suggest_exit(fair, ask, signal)

    # ── Trade plan ─────────────────────────────────────────────────────
    plan = build_trade_plan(
        raw          = raw,
        signal       = signal,
        edge         = raw_edge,
        fee_adj_edge = fee_adj,
        breakeven    = breakeven,
        contracts    = max(contracts, 0),
        buy_fee      = buy_fee,
        fair         = fair,
        ask          = ask,
        bid          = bid,
        spread       = spread,
        max_size     = max_size,
        min_edge     = min_edge,
    )

    return MarketSignal(
        market_id      = str(raw.get("market_id",    "")),
        market_name    = str(raw.get("market_name",  "")),
        category       = str(raw.get("category",     "")),
        side           = str(raw.get("side",         "YES")),
        bid_price      = bid,
        ask_price      = ask,
        last_price     = last,
        fair_price     = fair,
        volume         = volume,
        liquidity      = liquidity,
        raw_edge       = raw_edge,
        fee_est        = buy_fee,
        fee_adj_edge   = fee_adj,
        breakeven      = breakeven,
        spread         = spread,
        signal         = signal,
        suggested_size = size,
        exit_target    = exit_tgt,
        reason         = plan.reason,
        status         = "PAPER",
        data_quality   = plan.data_quality,
        trade_plan     = plan,
    )


def run_scanner(
    markets:      list,
    min_edge:     float = 8.0,
    max_spread:   float = 5.0,
    max_size:     float = 10.0,
    crypto_prices: dict = None,    # {symbol: CryptoPriceSnapshot} for heuristic fair price
) -> list:
    """
    Analyse a list of raw market dicts and return sorted MarketSignal list.

    Sort order: STRONG ENTRY → ENTRY → WATCH → AVOID → NO TRADE → DATA NEEDED
    Within each tier: sorted by absolute edge descending.

    When crypto_prices is supplied and model_fair_price is None:
    - estimate_fair_price() is called to get a heuristic estimate
    - The estimate is injected into the market dict as model_fair_price
    - It is clearly marked HEURISTIC_ONLY in the trade plan reason
    - Confidence is LOW — do not use for real trading

    Args:
        markets:       list of dicts from DataLayer.fetch
        min_edge:      cents of edge for ENTRY signal
        max_spread:    max cents of spread for tradeable markets
        max_size:      max dollar size for position sizing
        crypto_prices: optional live crypto price dict for heuristic model

    Returns:
        list of MarketSignal, sorted best to worst.
    """
    order = {
        "STRONG ENTRY": 0,
        "ENTRY":        1,
        "WATCH":        2,
        "AVOID":        3,
        "NO TRADE":     4,
        "DATA NEEDED":  5,
    }

    signals = []
    for m in markets:
        try:
            # Inject heuristic fair price if model price is missing and crypto_prices available
            if m.get("model_fair_price") is None and crypto_prices:
                try:
                    est = estimate_fair_price(
                        market_name   = m.get("market_name", ""),
                        category      = m.get("category", ""),
                        crypto_prices = crypto_prices,
                        expiration_str= m.get("expiration_time") or m.get("expiry"),
                    )
                    if est.get("fair_price") is not None:
                        m = dict(m)   # copy so original is untouched
                        m["model_fair_price"]    = est["fair_price"]
                        m["_fair_price_source"]  = est["fair_price_source"]
                        m["_fair_confidence"]    = est["confidence"]
                        m["_fair_model_status"]  = est["model_status"]
                        m["_fair_reasons"]       = est["reasons"]
                        m["_fair_missing"]       = est["missing_inputs"]
                except Exception as fe:
                    pass   # heuristic failure never blocks the scan

            sig = analyse_market(m, min_edge, max_spread, max_size)

            # Attach fair price metadata to signal reason
            if m.get("_fair_price_source"):
                src_tag = m["_fair_price_source"]
                conf    = m.get("_fair_confidence", "LOW")
                sig.reason = (
                    f"[Fair: {src_tag} conf={conf}] " + sig.reason
                )

            signals.append(sig)
        except Exception as e:
            print(f"[scanner] skipped {m.get('market_id','?')}: {e}")

    signals.sort(key=lambda s: (order.get(s.signal, 9), -abs(s.raw_edge)))
    return signals
