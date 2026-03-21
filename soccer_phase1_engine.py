#!/usr/bin/env python3
"""
soccer_phase1_engine.py

Phase 1 manual soccer trading assistant:
- You enter live match state manually
- Script estimates:
    * Draw probability
    * Over/Under probability for a target line
- Compares your estimate vs market price
- Flags possible value spots

No external libraries required.
Run:
    python soccer_phase1_engine.py
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

from team_profiles import TEAM_PROFILES, DEFAULT_PROFILE


# ----------------------------
# Core math helpers
# ----------------------------

def poisson_pmf(k: int, lam: float) -> float:
    """Poisson probability mass function."""
    if k < 0:
        return 0.0
    if lam < 0:
        raise ValueError("Lambda must be >= 0")
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def american_style_prob_from_cents(cents: Optional[float]) -> Optional[float]:
    """
    Kalshi-style rough interpretation:
    63 cents ~= 63% implied probability before fees/slippage.
    """
    if cents is None:
        return None
    return clamp(cents / 100.0, 0.0, 1.0)


# ----------------------------
# Model structures
# ----------------------------

@dataclass
class MatchState:
    home_team: str
    away_team: str
    minute: int
    home_goals: int
    away_goals: int
    stoppage_minutes_remaining: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    pressure_bias: int = 0
    """
    pressure_bias:
        -2 = away dominating
        -1 = away slight edge
         0 = balanced
        +1 = home slight edge
        +2 = home dominating
    """


@dataclass
class MarketInput:
    total_line: float
    draw_cents: Optional[float] = None
    over_cents: Optional[float] = None
    under_cents: Optional[float] = None


@dataclass
class ModelConfig:
    baseline_total_goals: float = 2.60
    """
    Typical generic soccer baseline.
    Can tune later by league/team style.
    """

    max_goal_diff_for_draw_calc: int = 6
    max_future_goals: int = 12

    # time decay tuning
    late_game_slowdown: float = 0.90
    early_game_boost: float = 1.03

    # red card adjustments
    red_card_total_goal_boost: float = 0.10
    red_card_strength_shift: float = 0.18

    # pressure adjustments
    pressure_total_boost_per_step: float = 0.03
    pressure_team_shift_per_step: float = 0.08


# ----------------------------
# Probability engine
# ----------------------------

class SoccerEdgeEngine:
    def get_team_profile(self, name: str):
        return TEAM_PROFILES.get(name.lower(), DEFAULT_PROFILE)

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()

    def remaining_minutes_factor(self, minute: int, stoppage_remaining: int) -> float:
        """
        Fraction of match left.
        Uses 90 + remaining stoppage as effective horizon.
        """
        effective_total = 90 + max(stoppage_remaining, 0)
        remaining = max(effective_total - minute, 0)
        return clamp(remaining / max(effective_total, 1), 0.0, 1.0)

    def estimate_remaining_goal_rate(self, state: MatchState) -> Tuple[float, float]:
        total_baseline = self.config.baseline_total_goals

        time_factor = self.remaining_minutes_factor(
            minute=state.minute,
            stoppage_remaining=state.stoppage_minutes_remaining
        )

        remaining_total = total_baseline * time_factor

        if state.minute >= 75:
            remaining_total *= self.config.late_game_slowdown
        elif state.minute <= 20:
            remaining_total *= self.config.early_game_boost

        remaining_total *= (1.0 + abs(state.pressure_bias) * self.config.pressure_total_boost_per_step)

        total_red_diff = abs(state.home_red_cards - state.away_red_cards)
        remaining_total *= (1.0 + total_red_diff * self.config.red_card_total_goal_boost)

        home_profile = self.get_team_profile(state.home_team)
        away_profile = self.get_team_profile(state.away_team)

        avg_late_goal_bias = (home_profile["late"] + away_profile["late"]) / 2.0
        remaining_total *= avg_late_goal_bias

        remaining_total = max(0.02, remaining_total)

        home_attack = home_profile["attack"]
        away_attack = away_profile["attack"]

        home_effective = home_attack * away_profile["defense"]
        away_effective = away_attack * home_profile["defense"]

        total_effective = home_effective + away_effective
        home_share = home_effective / total_effective
        away_share = away_effective / total_effective

        home_share += state.pressure_bias * self.config.pressure_team_shift_per_step
        away_share -= state.pressure_bias * self.config.pressure_team_shift_per_step

        red_diff = state.away_red_cards - state.home_red_cards
        home_share += red_diff * self.config.red_card_strength_shift
        away_share -= red_diff * self.config.red_card_strength_shift

        home_share = clamp(home_share, 0.10, 0.90)
        away_share = clamp(away_share, 0.10, 0.90)

        total_share = home_share + away_share
        home_share /= total_share
        away_share /= total_share

        home_lambda = remaining_total * home_share
        away_lambda = remaining_total * away_share

        return home_lambda, away_lambda

    def draw_probability(self, state: MatchState) -> float:
        home_lambda, away_lambda = self.estimate_remaining_goal_rate(state)
        current_diff = state.home_goals - state.away_goals

        home_profile = self.get_team_profile(state.home_team)
        away_profile = self.get_team_profile(state.away_team)
        avg_draw_bias = (home_profile["draw"] + away_profile["draw"]) / 2.0

        prob = 0.0
        max_future = self.config.max_future_goals

        for h_future in range(max_future + 1):
            ph = poisson_pmf(h_future, home_lambda)
            for a_future in range(max_future + 1):
                pa = poisson_pmf(a_future, away_lambda)
                final_diff = current_diff + h_future - a_future
                if final_diff == 0:
                    prob += ph * pa

        prob *= avg_draw_bias
        return clamp(prob, 0.0, 1.0)

    def total_under_probability(self, state: MatchState, total_line: float) -> float:
        """
        Probability final total goals ends under total_line.
        For x.5 lines, this is straightforward:
            under 2.5 means final_total <= 2
            under 3.5 means final_total <= 3
        """
        if abs(total_line - int(total_line) - 0.5) > 1e-9:
            raise ValueError("Phase 1 script expects half-goal lines like 1.5, 2.5, 3.5, 4.5")

        home_lambda, away_lambda = self.estimate_remaining_goal_rate(state)
        current_total = state.home_goals + state.away_goals
        max_allowed_final = math.floor(total_line - 0.5)
        max_extra_goals = max_allowed_final - current_total

        if max_extra_goals < 0:
            return 0.0

        # Sum probability of total future goals <= max_extra_goals
        total_lambda = home_lambda + away_lambda
        prob = 0.0
        for extra in range(max_extra_goals + 1):
            prob += poisson_pmf(extra, total_lambda)

        return clamp(prob, 0.0, 1.0)

    def total_over_probability(self, state: MatchState, total_line: float) -> float:
        return 1.0 - self.total_under_probability(state, total_line)

    def fair_cents(self, prob: float) -> float:
        return round(prob * 100.0, 1)

    def edge_report(self, model_prob: float, market_cents: Optional[float], label: str) -> str:
        fair = self.fair_cents(model_prob)
        if market_cents is None:
            return f"{label}: model={fair:.1f}c | market=n/a"

        implied = american_style_prob_from_cents(market_cents)
        edge = fair - market_cents

        verdict = "NO EDGE"
        if edge >= 8:
            verdict = "STRONG VALUE"
        elif edge >= 4:
            verdict = "VALUE"
        elif edge <= -8:
            verdict = "AVOID / OVERPRICED"
        elif edge <= -4:
            verdict = "LEAN AVOID"

        return (
            f"{label}: model={fair:.1f}c | market={market_cents:.1f}c "
            f"| edge={edge:+.1f}c | {verdict}"
        )

    def full_analysis(self, state: MatchState, market: MarketInput) -> Dict[str, float]:
        p_draw = self.draw_probability(state)
        p_under = self.total_under_probability(state, market.total_line)
        p_over = 1.0 - p_under

        home_lambda, away_lambda = self.estimate_remaining_goal_rate(state)

        return {
            "home_remaining_lambda": home_lambda,
            "away_remaining_lambda": away_lambda,
            "draw_prob": p_draw,
            "under_prob": p_under,
            "over_prob": p_over,
        }


# ----------------------------
# User interaction
# ----------------------------

def ask_str(prompt: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{prompt}{suffix}: ").strip()
    return raw if raw else (default if default is not None else "")


def ask_int(prompt: str, default: int = 0) -> int:
    while True:
        raw = ask_str(prompt, str(default))
        try:
            return int(raw)
        except ValueError:
            print("Enter a whole number.")


def ask_float(prompt: str, default: float) -> float:
    while True:
        raw = ask_str(prompt, str(default))
        try:
            return float(raw)
        except ValueError:
            print("Enter a number.")


def ask_optional_float(prompt: str) -> Optional[float]:
    raw = ask_str(prompt, "")
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        print("Invalid number, leaving blank.")
        return None


def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def describe_pressure_bias(value: int) -> str:
    mapping = {
        -2: "Away dominating",
        -1: "Away slight edge",
         0: "Balanced",
         1: "Home slight edge",
         2: "Home dominating",
    }
    return mapping.get(value, "Balanced")


def run_once(engine: SoccerEdgeEngine) -> None:
    print_header("SOCCER PHASE 1 EDGE ENGINE")

    home_team = ask_str("Home team", "Home")
    away_team = ask_str("Away team", "Away")
    minute = ask_int("Minute", 75)
    home_goals = ask_int("Home goals", 1)
    away_goals = ask_int("Away goals", 1)
    stoppage = ask_int("Stoppage minutes still expected/remaining", 0)
    home_red = ask_int("Home red cards", 0)
    away_red = ask_int("Away red cards", 0)

    print("\nPressure bias options:")
    print("  -2 = away dominating")
    print("  -1 = away slight edge")
    print("   0 = balanced")
    print("   1 = home slight edge")
    print("   2 = home dominating")
    pressure = ask_int("Pressure bias", 0)
    pressure = int(clamp(pressure, -2, 2))

    total_line = ask_float("Target total line (must be x.5)", 2.5)

    print("\nOptional market prices in cents. Leave blank if unknown.")
    draw_cents = ask_optional_float("Draw market price")
    over_cents = ask_optional_float(f"Over {total_line} market price")
    under_cents = ask_optional_float(f"Under {total_line} market price")

    state = MatchState(
        home_team=home_team,
        away_team=away_team,
        minute=minute,
        home_goals=home_goals,
        away_goals=away_goals,
        stoppage_minutes_remaining=stoppage,
        home_red_cards=home_red,
        away_red_cards=away_red,
        pressure_bias=pressure,
    )

    market = MarketInput(
        total_line=total_line,
        draw_cents=draw_cents,
        over_cents=over_cents,
        under_cents=under_cents,
    )

    results = engine.full_analysis(state, market)

    print_header("MATCH SNAPSHOT")
    print(f"{state.home_team} vs {state.away_team}")
    print(f"Score: {state.home_goals}-{state.away_goals}")
    print(f"Minute: {state.minute}")
    print(f"Pressure: {describe_pressure_bias(state.pressure_bias)}")
    print(f"Red cards: home={state.home_red_cards}, away={state.away_red_cards}")

    print_header("MODEL OUTPUT")
    print(
        f"Expected remaining goals: "
        f"home={results['home_remaining_lambda']:.3f}, "
        f"away={results['away_remaining_lambda']:.3f}, "
        f"total={results['home_remaining_lambda'] + results['away_remaining_lambda']:.3f}"
    )
    print(f"Draw probability:        {results['draw_prob'] * 100:.2f}%")
    print(f"Under {total_line} probability: {results['under_prob'] * 100:.2f}%")
    print(f"Over  {total_line} probability: {results['over_prob'] * 100:.2f}%")

    print_header("EDGE REPORT")
    print(engine.edge_report(results["draw_prob"], market.draw_cents, "DRAW"))
    print(engine.edge_report(results["under_prob"], market.under_cents, f"UNDER {total_line}"))
    print(engine.edge_report(results["over_prob"], market.over_cents, f"OVER {total_line}"))

    print_header("QUICK READ")
    strongest = []

    if market.draw_cents is not None:
        draw_edge = engine.fair_cents(results["draw_prob"]) - market.draw_cents
        strongest.append(("DRAW", draw_edge))

    if market.under_cents is not None:
        under_edge = engine.fair_cents(results["under_prob"]) - market.under_cents
        strongest.append((f"UNDER {total_line}", under_edge))

    if market.over_cents is not None:
        over_edge = engine.fair_cents(results["over_prob"]) - market.over_cents
        strongest.append((f"OVER {total_line}", over_edge))

    if strongest:
        strongest.sort(key=lambda x: x[1], reverse=True)
        best_label, best_edge = strongest[0]
        if best_edge >= 4:
            print(f"Best apparent value: {best_label} ({best_edge:+.1f}c edge)")
        else:
            print("No strong edge detected from entered prices.")
    else:
        print("No market prices entered, so no direct value call yet.")

    print("\nReminder: Phase 1 is a decision-support tool, not a guarantee.")


def main() -> None:
    engine = SoccerEdgeEngine()

    while True:
        run_once(engine)
        again = ask_str("\nAnalyze another match? (y/n)", "y").lower()
        if again not in {"y", "yes"}:
            print("Done.")
            break


if __name__ == "__main__":
    main()
