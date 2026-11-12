"""Morning scanner: pick the stocks most 'in play' today.

Candidates = CORE (liquid large caps + ETFs) + Alpaca's most-active list + top
gainers/losers. Each is scored on its opening gap and opening-range relative
volume; the top MAX_UNIVERSE become today's trading list."""
from datetime import timedelta, timezone

import alpaca
import config as C

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
    cands = sorted(s for s in cands if s.isalpha())  # skip warrants, units, class shares

    snaps = alpaca.snapshots(cands)
    liquid = []
    for s in cands:
        prev = (snaps.get(s) or {}).get("prevDailyBar")
        if not prev or prev["c"] < C.MIN_PRICE or prev["v"] * prev["c"] < C.MIN_PREV_DOLLAR_VOL:
            continue
        liquid.append((s, prev["c"], prev["v"]))

    bars = alpaca.bars([x[0] for x in liquid], _utc(or_start), _utc(or_end - timedelta(seconds=1)))
    rows = []
    for s, prev_close, prev_vol in liquid:
        b = bars.get(s, [])
        if len(b) < C.MIN_RANGE_BARS:
            continue
        hi, lo = max(x["h"] for x in b), min(x["l"] for x in b)
        last = b[-1]["c"]
        width = (hi - lo) / last
        if not (C.MIN_RANGE_PCT <= width <= C.MAX_RANGE_PCT):
            continue
        gap = b[0]["o"] / prev_close - 1
        relvol = sum(x["v"] for x in b) / max(prev_vol * C.OPENING_RANGE_MIN / 390, 1)
        rows.append({
            "symbol": s, "high": hi, "low": lo, "prev_close": prev_close,
            "gap_pct": round(gap * 100, 2), "relvol": round(relvol, 2),
            "range_pct": round(width * 100, 2),
            "score": round(relvol * (1 + 10 * abs(gap)), 3),
            "source": "core" if s in CORE else "scanner",
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    return rows[:C.MAX_UNIVERSE], {"scanned": len(cands), "liquid": len(liquid),
                                   "qualified": len(rows), "selected": min(len(rows), C.MAX_UNIVERSE)}
