"""The risk bot: sizing and hard limits. It can veto any trade and can stop the whole day."""
from v2 import config as C


def size(equity, price, stop_dist):
    """Shares: risk RISK_PER_TRADE of equity to the stop, capped at MAX_POSITION_PCT of equity."""
    if stop_dist <= 0 or price <= 0:
        return 0
    by_risk = int(equity * C.RISK_PER_TRADE / stop_dist)
    by_cap = int(equity * C.MAX_POSITION_PCT / price)
    return max(0, min(by_risk, by_cap))


def open_risk(metas):
    """Dollars still at risk: stops already at or past breakeven count as zero."""
    tot = 0.0
    for m in metas.values():
        sign = 1 if m["side"] == "long" else -1
        tot += max(0.0, (m["entry"] - m["stop"]) * sign) * m["qty"]
    return tot


def check(metas, marks, equity, symbol, qty, price, stop_dist, halted):
    """(ok, reason). metas: open-position metadata; marks: {symbol: last price}."""
    if halted:
        return False, "halted for the day"
    if symbol in metas:
        return False, "already holding"
    if qty < 1:
        return False, "size rounds to zero"
    if len(metas) >= C.MAX_OPEN_POSITIONS:
        return False, f"{len(metas)} positions open"
    new_risk = qty * stop_dist
    if open_risk(metas) + new_risk > C.MAX_OPEN_RISK * equity:
        return False, "open risk limit"
    gross = sum(m["qty"] * marks.get(s, m["entry"]) for s, m in metas.items()) + qty * price
    if gross > C.MAX_GROSS * equity:
        return False, "gross exposure limit"
    return True, ""


def daily_stop_hit(equity, start_equity):
    return equity <= start_equity * (1 - C.DAILY_LOSS_LIMIT)
