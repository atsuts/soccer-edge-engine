watchlist = []


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


def get_watchlist():
    return watchlist


def get_match_by_index(index: int):
    if index < 0 or index >= len(watchlist):
        return None
    return watchlist[index]


def clear_watchlist():
    watchlist.clear()