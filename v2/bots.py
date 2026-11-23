"""The bot team. Every signal bot is plain code: it reads a Ctx and returns a Vote.
  direction +1 = long, -1 = short, 0 = no opinion; conf 0..1.
Filters (volume, liquidity, news) can veto a trade. The risk bot lives in risk.py, the exit manager in exits.py.
The news bot is the only one that calls an AI model (Google Gemini free tier, once or twice a day)."""
from dataclasses import dataclass

from v2 import config as C
from v2 import costs


@dataclass
class Vote:
    name: str
    dir: int = 0
    conf: float = 0.0
    why: str = ""


def _clip(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# ---------- signal bots ----------
def vwap(c):
    if c.vwap_sd <= 0:
        return Vote("vwap", 0, 0, "no spread yet")
    if c.reclaim_up:
        return Vote("vwap", +1, 0.9, "reclaimed VWAP")
    if c.reclaim_dn:
        return Vote("vwap", -1, 0.9, "lost VWAP")
    z = (c.price - c.vwap) / c.vwap_sd
    if abs(z) > 2.0:
        return Vote("vwap", 0, 0, "stretched >2 sd from VWAP")
    if z > 0.3 and c.vwap_slope >= 0:
        return Vote("vwap", +1, _clip(0.4 + 0.2 * z, 0, 0.8), f"above rising VWAP ({z:.1f} sd)")
    if z < -0.3 and c.vwap_slope <= 0:
        return Vote("vwap", -1, _clip(0.4 - 0.2 * z, 0, 0.8), f"below falling VWAP ({z:.1f} sd)")
    return Vote("vwap", 0, 0, "at VWAP")


def relvol(c):
    if c.rvol < 1.2 or len(c.closes1) < 12:
        return Vote("relvol", 0, 0, f"rvol {c.rvol:.1f}")
    ret = c.price / c.closes1[-11] - 1
    if abs(ret) < 0.0005:
        return Vote("relvol", 0, 0, "volume but no direction")
    d = 1 if ret > 0 else -1
    return Vote("relvol", d, _clip((c.rvol - 1) / 2), f"rvol {c.rvol:.1f}x, 10-min move {ret * 100:+.2f}%")


def trend(c):
    if not c.ema_slow or c.atr5 <= 0:
        return Vote("trend", 0, 0, "not enough 5-min bars")
    gap = c.ema_fast - c.ema_slow
    if gap > 0 and c.price > c.ema_fast:
        return Vote("trend", +1, _clip(0.4 + abs(gap) / (2 * c.atr5), 0, 0.9), "EMA9 > EMA20, price above")
    if gap < 0 and c.price < c.ema_fast:
        return Vote("trend", -1, _clip(0.4 + abs(gap) / (2 * c.atr5), 0, 0.9), "EMA9 < EMA20, price below")
    return Vote("trend", 0, 0, "mixed")


def orb(c):
    if c.now_idx < 15 or c.now_idx > 120 or c.or_high <= c.or_low:
        return Vote("orb", 0, 0, "outside the breakout window")
    rng = c.or_high - c.or_low
    last = c.bars[-1]["c"]
    if c.price > c.or_high and last > c.or_high:
        ext = (c.price - c.or_high) / rng
        return Vote("orb", +1, _clip(0.85 - 0.3 * ext), "broke above opening range") if ext <= 0.6 else Vote("orb", 0, 0, "extended past range")
    if c.price < c.or_low and last < c.or_low:
        ext = (c.or_low - c.price) / rng
        return Vote("orb", -1, _clip(0.85 - 0.3 * ext), "broke below opening range") if ext <= 0.6 else Vote("orb", 0, 0, "extended past range")
    return Vote("orb", 0, 0, "inside range")


def momentum(c):
    """RSI + MACD on 5-min bars. Never acts alone: needs the trend to agree."""
    if c.rsi5 is None or c.macd_h is None or c.macd_h_prev is None:
        return Vote("momentum", 0, 0, "warming up")
    t = trend(c).dir
    rising = c.macd_h > c.macd_h_prev
    if t > 0 and 55 <= c.rsi5 <= 75 and c.macd_h > 0 and rising:
        return Vote("momentum", +1, _clip((c.rsi5 - 50) / 30 + 0.2), f"RSI {c.rsi5:.0f}, MACD rising")
    if t < 0 and 25 <= c.rsi5 <= 45 and c.macd_h < 0 and not rising:
        return Vote("momentum", -1, _clip((50 - c.rsi5) / 30 + 0.2), f"RSI {c.rsi5:.0f}, MACD falling")
    return Vote("momentum", 0, 0, "no clean momentum")


def meanrev(c):
    """Fade stretched moves (Bollinger + fast RSI) - but not in a strong trend."""
    if not c.bb or c.rsi1_7 is None:
        return Vote("meanrev", 0, 0, "warming up")
    if c.atr5 > 0 and abs(c.ema_fast - c.ema_slow) > 2 * c.atr5:
        return Vote("meanrev", 0, 0, "strong trend - no fading")
    _, up, lo = c.bb
    if c.price < lo and c.rsi1_7 < 25:
        return Vote("meanrev", +1, 0.6, f"below lower band, RSI7 {c.rsi1_7:.0f}")
    if c.price > up and c.rsi1_7 > 75:
        return Vote("meanrev", -1, 0.6, f"above upper band, RSI7 {c.rsi1_7:.0f}")
    return Vote("meanrev", 0, 0, "inside bands")


SIGNAL_BOTS = [vwap, relvol, trend, orb, momentum, meanrev]
NAMES = ["vwap", "relvol", "trend", "orb", "momentum", "meanrev", "volume", "liquidity", "risk", "exits", "news"]


# ---------- filters (can veto) ----------
def volume_filter(c, direction):
    """Breakouts on quiet volume mostly fail. Needs session rvol >= MIN_RVOL and the last 3 bars not drying up."""
    if c.rvol < C.MIN_RVOL:
        return False, f"rvol {c.rvol:.1f} < {C.MIN_RVOL}"
    if c.vol_avg20 > 0 and c.vol_last3 < 0.6 * c.vol_avg20:
        return False, "volume drying up"
    return True, ""


def liquidity_filter(c, stop_dist):
    """Reject stale prices, wide spreads, and trades where costs would eat the target."""
    if c.bar_age_min > 3:
        return False, f"last print {c.bar_age_min} min old", 0.0
    if c.spread_bps is not None and c.spread_bps > C.MAX_SPREAD_BPS:
        return False, f"spread {c.spread_bps:.1f} bps", 0.0
    side_bps = costs.bps_per_side(c.spread_bps)
    cost_ps = c.price * 2 * side_bps / 1e4               # round trip, per share
    target = stop_dist * C.TARGET_R
    if cost_ps > C.MAX_COST_TO_TARGET * target:
        return False, f"cost {cost_ps:.3f} > {int(C.MAX_COST_TO_TARGET * 100)}% of target {target:.3f}", side_bps
    return True, "", side_bps


# ---------- news bot (AI) ----------
def news(c):
    n = c.news
    if n == "long":
        return Vote("news", +1, 0.6, c.news_note or "positive catalyst")
    if n == "short":
        return Vote("news", -1, 0.6, c.news_note or "negative catalyst")
    if n == "block":
        return Vote("news", 0, 0, "BLOCK: " + (c.news_note or "event risk"))
    return Vote("news", 0, 0, c.news_note or "no restriction")


def run_news_desk(rows, now):
    """Call the AI desk (Gemini free tier) for today's names. Fails open: returns {} on any problem.
    rows: [{symbol, gap_pct, relvol}]. Returns ({symbol: (decision, note)}, briefing)."""
    import sys
    sys.path.insert(0, str(C.ROOT / "bot"))
    try:
        import news_filter   # reused from the v1 bot
        res = news_filter.run(rows, now)
    except Exception as e:  # noqa
        return {}, f"news desk unavailable: {type(e).__name__}: {e}"
    out = {s: (d["decision"], (d.get("catalyst") or d.get("reason") or "")[:80]) for s, d in res.get("decisions", {}).items()}
    return out, res.get("briefing") or res.get("error", "")
