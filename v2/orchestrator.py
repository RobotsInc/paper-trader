"""The orchestrator: asks every signal bot for a vote, weighs them, applies the filters, and decides.
Every bot's vote is returned so the engine can log it with the trade (that log is how weak bots get cut)."""
import json
from dataclasses import dataclass, field

from v2 import bots
from v2 import config as C


@dataclass
class Decision:
    symbol: str
    side: str = ""                 # "long" / "short" / ""
    score: float = 0.0
    votes: list = field(default_factory=list)
    skip: str = ""                 # why no trade ("" = go)
    stop_dist: float = 0.0
    stop_price: float = 0.0
    side_bps: float = 0.0
    had_signal: bool = False       # score + agreement cleared the bar before the filters ran


def load_weights():
    """Bot weights from data/v2/bots.json (hit-rate based once a bot has enough trades); default 1.0."""
    try:
        d = json.load(open(C.DATA_DIR / "bots.json"))
        return {b["name"]: float(b.get("weight", 1.0)) for b in d.get("bots", [])}
    except Exception:
        return {}


def evaluate(c, weights=None):
    weights = weights or {}
    d = Decision(c.symbol)
    if not c.ready:
        d.skip = c.why_not or "not ready"
        return d
    votes = [f(c) for f in bots.SIGNAL_BOTS]
    nv = bots.news(c)
    d.votes = votes + [nv]
    wsum = sum(weights.get(v.name, 1.0) for v in votes)
    d.score = sum(weights.get(v.name, 1.0) * v.dir * v.conf for v in votes) / wsum
    direction = 1 if d.score > 0 else -1 if d.score < 0 else 0
    if direction == 0 or abs(d.score) < C.ENTRY_SCORE:
        d.skip = f"score {d.score:+.2f}"
        return d
    agree = [v for v in votes if v.dir == direction and v.conf >= 0.3]
    if len(agree) < C.MIN_AGREE:
        d.skip = f"only {len(agree)} bots agree"
        return d
    if any(v.dir == -direction and v.conf >= 0.7 for v in votes):
        d.skip = "a strong bot disagrees"
        return d
    d.had_signal = True
    d.side = "long" if direction > 0 else "short"
    if d.side == "short" and not C.ALLOW_SHORTS:
        d.skip, d.side = "shorts off", ""
        return d

    # filters
    if c.news == "block":
        d.skip = "news: " + (c.news_note or "event risk"); d.side = ""
        return d
    if (c.news == "long" and direction < 0) or (c.news == "short" and direction > 0):
        d.skip = "news disagrees"; d.side = ""
        return d
    ok, why = bots.volume_filter(c, direction)
    if not ok:
        d.skip = "volume: " + why; d.side = ""
        return d

    stop_dist = min(max(C.STOP_ATR_MULT * c.atr1, C.MIN_STOP_PCT * c.price), C.MAX_STOP_PCT * c.price)
    ok, why, side_bps = bots.liquidity_filter(c, stop_dist)
    if not ok:
        d.skip = "liquidity: " + why; d.side = ""
        return d
    d.stop_dist, d.side_bps = stop_dist, side_bps
    d.stop_price = round(c.price - direction * stop_dist, 2)
    return d


def votes_str(votes):
    """Compact, comma-free: name:dir:conf|name:dir:conf"""
    return "|".join(f"{v.name}:{v.dir:+d}:{v.conf:.2f}" for v in votes)
