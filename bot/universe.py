"""Morning scanner: pick today's "stocks in play" (Zarattini, Barbon & Aziz).

Candidates = CORE (liquid large caps + ETFs) + Alpaca's most-active list + top
gainers/losers. A candidate qualifies with price >= MIN_PRICE, 14-day average volume
>= MIN_AVG_VOLUME, 14-day ATR >= MIN_ATR, and relative volume >= MIN_RELVOL, where
relative volume = today's opening-range volume / the same window's average over the
last 14 sessions. The MAX_UNIVERSE names with the highest relative volume are traded."""
from datetime import timedelta, timezone

import re

import alpaca
import config as C

# Fund names that mark a leveraged or inverse ETF (catches ones EXCLUDE doesn't list by ticker).
LEVERAGED = re.compile(r"\b(\d(\.\d+)?X|2x|3x|ultra|ultrapro|leveraged|inverse|daily target)\b", re.I)


def is_leveraged(symbol):
    try:
        return bool(LEVERAGED.search(alpaca.asset(symbol).get("name", "")))
    except Exception:
        return False

CORE = [
    # Index / sector ETFs
    "SPY", "QQQ", "IWM", "DIA", "SMH", "XLF", "XLE", "XLK", "XLV", "XBI", "ARKK", "TLT", "GLD", "SLV", "USO",
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AVGO", "NFLX", "ORCL",
    # Semis
    "AMD", "INTC", "MU", "QCOM", "TXN", "AMAT", "LRCX", "KLAC", "MRVL", "ARM", "SMCI", "TSM", "ON",
    # Software / internet
    "CRM", "ADBE", "NOW", "SNOW", "PLTR", "CRWD", "PANW", "ZS", "NET", "DDOG", "SHOP", "UBER", "ABNB",
    "DASH", "RBLX", "SNAP", "PINS", "ROKU", "SPOT", "TTD", "APP", "DELL", "IBM", "CSCO",
    # Fintech / crypto-linked
    "COIN", "HOOD", "MSTR", "PYPL", "SOFI", "AFRM", "XYZ",
    # Financials
    "JPM", "BAC", "WFC", "C", "GS", "MS", "SCHW", "V", "MA", "AXP",
    # Energy
    "XOM", "CVX", "OXY", "COP", "SLB",
    # Industrials / defense
    "BA", "CAT", "DE", "GE", "LMT", "RTX",
    # Health
    "UNH", "LLY", "JNJ", "PFE", "MRK", "ABBV", "MRNA", "AMGN",
    # Consumer
    "WMT", "COST", "TGT", "HD", "NKE", "SBUX", "MCD", "DIS", "LULU",
    # Autos / EV
    "F", "GM", "RIVN", "LCID", "NIO",
]


def _utc(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atr(daily):
    """Average true range over the last 14 sessions (needs 15 daily bars)."""
    d = daily[-15:]
    if len(d) < 15:
        return None
    trs = [max(b["h"] - b["l"], abs(b["h"] - p["c"]), abs(b["l"] - p["c"])) for p, b in zip(d, d[1:])]
    return sum(trs) / len(trs)


def build(or_start, or_end, log):
    cands = set(CORE)
    for name, fn, n in (("most-actives", alpaca.most_actives, C.SCAN_MOST_ACTIVES),
                        ("movers", alpaca.movers, C.SCAN_MOVERS)):
        try:
            found = fn(n)
            cands |= set(found)
            log(f"Scanner: {len(found)} names from {name}")
        except Exception as e:
            log(f"Scanner: {name} unavailable ({e}) - using core list")
    cands = sorted(s for s in cands if s.isalpha() and s not in C.EXCLUDE)  # skip warrants, units, leveraged ETFs

    # Daily history (all exchanges; free for data older than 15 min) -> ATR and average volume.
    day0 = or_start.replace(hour=0, minute=0)
    try:
        daily = alpaca.bars(cands, _utc(day0 - timedelta(days=35)), _utc(day0), timeframe="1Day", feed="sip")
    except RuntimeError as e:
        log(f"Scanner: all-exchange daily bars unavailable ({e}) - using IEX")
        daily = alpaca.bars(cands, _utc(day0 - timedelta(days=35)), _utc(day0), timeframe="1Day")
    liquid = {}
    for s in cands:
        d = daily.get(s, [])
        a = atr(d)
        if a is None:
            continue
        avg_vol = sum(b["v"] for b in d[-14:]) / 14
        floor = min(C.MIN_PRICE, C.SMALLCAP_MIN_PRICE) if C.SMALLCAP_TRACK else C.MIN_PRICE
        if d[-1]["c"] < floor or avg_vol < C.MIN_AVG_VOLUME or a < C.MIN_ATR:
            continue
        liquid[s] = {"prev_close": d[-1]["c"], "atr": a, "tier": "main" if d[-1]["c"] >= C.MIN_PRICE else "small"}

    # Opening-range volume over the last 14 sessions, same window, same (IEX) feed as today.
    k = C.OPENING_RANGE_MIN
    cal = alpaca.calendar((day0 - timedelta(days=30)).date().isoformat(),
                          (day0 - timedelta(days=1)).date().isoformat())[-14:]
    hist = {s: [] for s in liquid}
    for c in cal:
        t0 = or_start.replace(year=int(c["date"][:4]), month=int(c["date"][5:7]), day=int(c["date"][8:10]))
        past = alpaca.bars(sorted(liquid), _utc(t0), _utc(t0 + timedelta(minutes=k, seconds=-1)))
        for s in liquid:
            v = sum(x["v"] for x in past.get(s, []))
            if v > 0:  # days with no trades on the free feed would make relative volume meaningless
                hist[s].append(v)

    bars = alpaca.bars(sorted(liquid), _utc(or_start), _utc(or_end - timedelta(seconds=1)))
    rows = []
    for s, info in liquid.items():
        b = bars.get(s, [])
        base = sum(hist[s]) / len(hist[s]) if hist[s] else 0
        if len(b) < C.MIN_RANGE_BARS or len(hist[s]) < 10 or base <= 0:
            continue
        hi, lo = max(x["h"] for x in b), min(x["l"] for x in b)
        o, c = b[0]["o"], b[-1]["c"]
        direction = 1 if c > o else -1 if c < o else 0
        relvol = sum(x["v"] for x in b) / base
        if relvol < C.MIN_RELVOL or hi <= lo or (C.DIRECTION == "candle" and direction == 0):
            continue
        rows.append({
            "symbol": s, "high": hi, "low": lo, "prev_close": info["prev_close"],
            "gap_pct": round((o / info["prev_close"] - 1) * 100, 2), "relvol": round(relvol, 2),
            "range_pct": round((hi - lo) / c * 100, 2), "atr": round(info["atr"], 4),
            "dir": direction, "score": round(relvol, 3), "tier": info["tier"],
            "source": "core" if s in CORE else "scanner",
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    picked, small = [], []
    for r in rows:
        if r["tier"] == "main" and len(picked) >= C.MAX_UNIVERSE:
            continue
        if r["tier"] == "small" and len(small) >= C.SMALLCAP_MAX:
            continue
        if r["source"] == "scanner" and is_leveraged(r["symbol"]):
            continue
        (picked if r["tier"] == "main" else small).append(r)
    main_rows = [r for r in rows if r["tier"] == "main"]
    return picked, {"scanned": len(cands), "liquid": len(liquid), "qualified": len(main_rows),
                    "selected": len(picked), "small_tracked": len(small)}, small
