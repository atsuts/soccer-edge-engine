import json
from pathlib import Path

WATCHLIST_FILE = Path(__file__).with_name("watchlist.json")
watchlist = []


def load_watchlist():
    global watchlist

    if not WATCHLIST_FILE.exists():
        watchlist = []
        return watchlist

    try:
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            watchlist = json.load(f)
    except Exception:
        watchlist = []

    return watchlist


def save_watchlist():
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, indent=2)


def add_match(state, market):
    watchlist.append({
        "home": state.home_team,
        "away": state.away_team,
        "minute": state.minute,
        "home_goals": state.home_goals,
        "away_goals": state.away_goals,
        "stoppage": state.stoppage_minutes_remaining,
        "home_reds": state.home_red_cards,
        "away_reds": state.away_red_cards,
        "pressure": state.pressure_bias,
        "draw_price": market.draw_cents,
        "under_price": market.under_cents,
        "over_price": market.over_cents,
    })
    save_watchlist()


def get_watchlist():
    return watchlist


def get_match_by_index(index: int):
    if index < 0 or index >= len(watchlist):
        return None
    return watchlist[index]


def remove_match_by_index(index: int):
    if index < 0 or index >= len(watchlist):
        return False
    del watchlist[index]
    save_watchlist()
    return True


def clear_watchlist():
    watchlist.clear()
    save_watchlist()