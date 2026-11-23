"""The exit manager. Checks every open position each scan:
  - take profit at TARGET_R, unless the trade is clearly still running (then trail instead)
  - ratchet the stop up behind winners so a winner can't turn into a loser
  - close trades that have gone nowhere for MAX_HOLD_MIN
The protective stop itself is always held by Alpaca between scans."""
from v2 import config as C


def _strong(m, c):
    """Is the trade still being driven by trend + VWAP + volume?"""
    if c is None or not c.ready:
        return False
    sign = 1 if m["side"] == "long" else -1
    trend_ok = (c.ema_fast - c.ema_slow) * sign > 0 and (c.price - c.ema_fast) * sign > 0
    vwap_ok = (c.price - c.vwap) * sign > 0
    return trend_ok and vwap_ok and c.rvol >= 1.5


def r_multiple(m, price):
    sign = 1 if m["side"] == "long" else -1
    return sign * (price - m["entry"]) / m["risk_ps"] if m["risk_ps"] else 0.0


def desired_lock(peak_r):
    for thresh, lock in C.RATCHET:
        if peak_r >= thresh:
            return peak_r - C.TRAIL_BEHIND_R if lock == "trail" else lock
    return None


def manage(m, price, c, held_min):
    """Returns {"action": "hold"|"close"|"stop", "new_stop": float|None, "reason": str, "r": float}."""
    sign = 1 if m["side"] == "long" else -1
    r = r_multiple(m, price)
    m["peak_r"] = max(m.get("peak_r", 0.0), r)
    out = {"action": "hold", "new_stop": None, "reason": "", "r": r}

    if held_min >= C.MAX_HOLD_MIN and r < 0.3:
        return dict(out, action="close", reason="time stop (gone nowhere)")
    if r >= C.TARGET_R and not _strong(m, c):
        return dict(out, action="close", reason=f"target {r:.2f}R, momentum fading")

    lock = desired_lock(m["peak_r"])
    if lock is not None:
        new_stop = round(m["entry"] + sign * lock * m["risk_ps"], 2)
        tighter = new_stop > m["stop"] + 0.005 if sign > 0 else new_stop < m["stop"] - 0.005
        # a stop must stay on the loss side of the current price
        valid = new_stop < price - 0.01 if sign > 0 else new_stop > price + 0.01
        if tighter and valid:
            return dict(out, action="stop", new_stop=new_stop, reason=f"peak {m['peak_r']:.2f}R, lock {lock:.2f}R")
    return out
