"""Market data: prior-session history (volume curves, indicator warm-up) + today's 1-minute bars,
turned into one `Ctx` per symbol that every bot reads."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from v2 import indicators as ind
from v2.util import ET, log, minute_index, parse_ts


@dataclass
class Ctx:
    symbol: str
    ready: bool = False
    why_not: str = ""
    now_idx: int = 0
    price: float = 0.0
    day_open: float = 0.0
    prev_close: float = 0.0
    gap_pct: float = 0.0
    bars: list = field(default_factory=list)       # today's 1-min bars
    closes1: list = field(default_factory=list)    # warm-up + today
    vwap: float = 0.0
    vwap_sd: float = 0.0
    vwap_slope: float = 0.0
    reclaim_up: bool = False
    reclaim_dn: bool = False
    or_high: float = 0.0
    or_low: float = 0.0
    rvol: float = 0.0
    vol_last3: float = 0.0
    vol_avg20: float = 0.0
    atr1: float = 0.0
    atr5: float = 0.0
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    rsi5: float | None = None
    macd_h: float | None = None
    macd_h_prev: float | None = None
    rsi1_7: float | None = None
    bb: tuple | None = None
    bid: float = 0.0
    ask: float = 0.0
    spread_bps: float | None = None
    bar_age_min: int = 0
    news: str = "both"                    # both / long / short / block (AI desk)
    news_note: str = ""


def _norm(b):
    ts = parse_ts(b["t"])
    return {"t": b["t"], "ts": ts, "idx": minute_index(ts), "o": float(b["o"]), "h": float(b["h"]),
            "l": float(b["l"]), "c": float(b["c"]), "v": float(b.get("v") or 0)}


class Feed:
    def __init__(self, broker, symbols):
        self.broker, self.symbols = broker, list(symbols)
        self.today = {s: [] for s in self.symbols}
        self.warm = {s: [] for s in self.symbols}
        self.curve = {}        # symbol -> avg cumulative volume by minute index (0..389)
        self.prev_close = {}
        self.quotes = {}

    # ---- history ----
    def load_history(self, now, open_dt):
        start = (now - timedelta(days=15)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = open_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        raw = self.broker.bars(self.symbols, start, end)
        for s in self.symbols:
            sessions = {}
            for b in raw.get(s, []):
                nb = _norm(b)
                if 0 <= nb["idx"] < 390 and nb["ts"] < open_dt:
                    sessions.setdefault(nb["ts"].date(), []).append(nb)
            days = sorted(sessions)[-10:]
            curves = []
            for d in days:
                cum, arr, bi, rows = 0.0, [], 0, sessions[d]
                for i in range(390):
                    while bi < len(rows) and rows[bi]["idx"] <= i:
                        cum += rows[bi]["v"]
                        bi += 1
                    arr.append(cum)
                curves.append(arr)
            self.curve[s] = [sum(c[i] for c in curves) / len(curves) for i in range(390)] if curves else None
            allb = [b for d in days for b in sessions[d]]
            self.warm[s] = allb[-400:]
            self.prev_close[s] = allb[-1]["c"] if allb else 0.0
        ok = sum(1 for s in self.symbols if self.curve.get(s))
        log(f"History loaded for {ok}/{len(self.symbols)} symbols")

    # ---- live ----
    def update(self, now, open_dt):
        first = min((b[-1]["ts"] for b in self.today.values() if b), default=None)
        start_dt = (first - timedelta(minutes=1)) if first else open_dt
        raw = self.broker.bars(self.symbols, start_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for s in self.symbols:
            have = {b["t"] for b in self.today[s][-5:]}
            for b in raw.get(s, []):
                nb = _norm(b)
                if nb["idx"] < 0 or nb["ts"] < open_dt or nb["t"] in have:
                    continue
                if self.today[s] and nb["ts"] <= self.today[s][-1]["ts"]:
                    continue
                self.today[s].append(nb)
        try:
            self.quotes = self.broker.quotes(self.symbols)
        except Exception as e:
            log(f"quote fetch failed: {type(e).__name__}: {e}")

    # ---- per-symbol context ----
    def ctx(self, s, now, news=("both", "")):
        c = Ctx(symbol=s)
        c.news, c.news_note = news
        bars = self.today[s]
        c.bars = bars
        c.now_idx = minute_index(now)
        if len(bars) < 20:
            c.why_not = f"only {len(bars)} bars today"
            return c
        last = bars[-1]
        c.price, c.day_open, c.prev_close = last["c"], bars[0]["o"], self.prev_close.get(s, 0.0)
        c.gap_pct = (c.day_open / c.prev_close - 1) * 100 if c.prev_close else 0.0
        c.bar_age_min = c.now_idx - last["idx"]
        bq = self.quotes.get(s)
        if bq and bq[0] > 0 and bq[1] > 0 and bq[1] >= bq[0]:
            c.bid, c.ask = bq
            c.spread_bps = (c.ask - c.bid) / ((c.ask + c.bid) / 2) * 1e4

        c.vwap, c.vwap_sd = ind.vwap_sd(bars)
        if not c.vwap:
            c.why_not = "no volume yet"
            return c
        older = bars[:-10] if len(bars) > 30 else None
        v10, _ = ind.vwap_sd(older) if older else (c.vwap, 0)
        c.vwap_slope = c.vwap - (v10 or c.vwap)
        recent = [b["c"] for b in bars[-8:-1]]
        c.reclaim_up = bool(recent) and min(recent) < c.vwap < c.price and last["c"] > last["o"]
        c.reclaim_dn = bool(recent) and max(recent) > c.vwap > c.price and last["c"] < last["o"]

        orb = [b for b in bars if b["idx"] < 15]
        if orb:
            c.or_high, c.or_low = max(b["h"] for b in orb), min(b["l"] for b in orb)

        curve = self.curve.get(s)
        cum = sum(b["v"] for b in bars)
        idx = min(max(last["idx"], 0), 389)
        c.rvol = cum / curve[idx] if curve and curve[idx] > 0 else 0.0
        vols = [b["v"] for b in bars]
        c.vol_last3 = sum(vols[-3:]) / 3
        c.vol_avg20 = sum(vols[-20:]) / min(20, len(vols))

        allb = self.warm[s] + bars
        c.closes1 = [b["c"] for b in allb]
        c.atr1 = ind.atr([b["h"] for b in allb[-16:]], [b["l"] for b in allb[-16:]], c.closes1[-16:], 14) or 0.0
        b5 = ind.resample(allb, 5)
        c5 = [b["c"] for b in b5]
        if len(c5) >= 21:
            c.ema_fast, c.ema_slow = ind.ema(c5, 9)[-1], ind.ema(c5, 20)[-1]
            c.atr5 = ind.atr([b["h"] for b in b5[-16:]], [b["l"] for b in b5[-16:]], c5[-16:], 14) or 0.0
            c.rsi5 = ind.rsi(c5, 14)
            c.macd_h, c.macd_h_prev = ind.macd_hist(c5)
        c.rsi1_7 = ind.rsi(c.closes1[-60:], 7)
        c.bb = ind.bollinger(c.closes1, 20, 2.0)
        if c.atr1 <= 0:
            c.why_not = "no ATR"
            return c
        c.ready = True
        return c
